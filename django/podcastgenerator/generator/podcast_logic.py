# audio_processor/podcast_logic.py

import os
import csv
from datetime import datetime
from google.cloud import texttospeech_v1beta1 as texttospeech
from google.oauth2 import service_account
from pydub import AudioSegment
# Elimina 'from pydub.playback import play' ya que no reproduciremos en el servidor
# Elimina 'import pandas as pd' si solo usas csv.DictReader

# --- Configuración (ajustada para Django) ---
# Las credenciales y la ruta de salida se gestionarán de forma más dinámica.
# Es mejor usar variables de entorno de Django o cargar desde settings.py si es necesario.

# Asume que las credenciales están configuradas a nivel de entorno o que Google Cloud SDK las encuentra.
# Si tus credenciales están en un archivo, deberías pasar la ruta a la función o hacerla una configuración global segura.
# Para este ejemplo, asumiremos que GOOGLE_APPLICATION_CREDENTIALS ya está configurado en el entorno de Django.
# Opcional: puedes cargar las credenciales directamente aquí si el archivo está dentro de tu proyecto Django
# CREDENTIALS_PATH = os.path.join(settings.BASE_DIR, "credentials.json") # Asegúrate de que esto sea seguro en producción

try:
    # Intenta cargar las credenciales automáticamente si GOOGLE_APPLICATION_CREDENTIALS está configurado
    client = texttospeech.TextToSpeechClient()
except Exception as e:
    # Si no, carga desde la ruta especificada
    try:
        CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
        credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
        client = texttospeech.TextToSpeechClient(credentials=credentials)
    except Exception as e:
        raise RuntimeError(f"Error cargando credenciales de Google Cloud: {e}. Asegúrate de que GOOGLE_APPLICATION_CREDENTIALS esté configurado o el archivo 'credentials.json' exista.")


SPEAKER_VOICES = {
    "R": {"voice_name": "es-US-Chirp3-HD-Iapetus", "pause_after": 500},
    "S": {"voice_name": "es-US-Chirp-HD-F", "pause_after": 750},
    "T": {"voice_name": "es-US-Neural2-B", "pause_after": 600}
}


def generate_podcast_audio(csv_file_path):
    """
    Procesa un archivo CSV con columnas 'speaker' y 'text', genera audio
    usando Google Text-to-Speech y lo une en un único archivo MP3.

    Args:
        csv_file_path (str): La ruta completa al archivo CSV de entrada.

    Returns:
        str: La ruta completa al archivo MP3 generado.
    """
    from django.conf import settings # Importa settings aquí para evitar circular imports

    # Directorio de salida dentro de MEDIA_ROOT de Django
    output_dir = os.path.join(settings.MEDIA_ROOT, 'generated_audios')
    os.makedirs(output_dir, exist_ok=True)

    now = datetime.now()
    # Genera un nombre de archivo único basado en el nombre del CSV y la fecha/hora
    base_csv_name = os.path.basename(csv_file_path).replace('.csv', '')
    final_podcast_filename = f"podcast_{base_csv_name}_{now.strftime('%Y%m%d%H%M%S')}.mp3"
    final_podcast_path = os.path.join(output_dir, final_podcast_filename)


    # --- Leer CSV ---
    dialogue_turns = []
    try:
        with open(csv_file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            # Asegúrate de que las columnas existan
            if 'speaker' not in reader.fieldnames or 'text' not in reader.fieldnames:
                raise ValueError("El archivo CSV debe contener las columnas 'speaker' y 'text'.")

            for i, row in enumerate(reader):
                speaker_id = row['speaker'].strip()
                text = row['text'].strip()

                if speaker_id not in SPEAKER_VOICES:
                    print(f"Advertencia: Speaker ID '{speaker_id}' no tiene voz definida. Línea {i+2}. Se omitirá este turno.")
                    continue

                dialogue_turns.append({
                    "speaker_id": speaker_id,
                    "text": text,
                    "voice_name": SPEAKER_VOICES[speaker_id]["voice_name"],
                    "pause_after": SPEAKER_VOICES[speaker_id]["pause_after"],
                    # El nombre del archivo se generará al guardar
                })
    except FileNotFoundError:
        raise FileNotFoundError(f"El archivo CSV no se encontró en: {csv_file_path}")
    except Exception as e:
        raise RuntimeError(f"Error al leer el archivo CSV: {e}")

    # --- Generar audio y unir ---
    audio_segments = []
    # Usaremos un directorio temporal para los segmentos de audio generados por gTTS
    temp_segment_dir = os.path.join(settings.MEDIA_ROOT, 'temp_audio_segments')
    os.makedirs(temp_segment_dir, exist_ok=True)

    try:
        for i, turn in enumerate(dialogue_turns):
            synthesis_input = texttospeech.SynthesisInput(text=turn["text"])
            voice_params = texttospeech.VoiceSelectionParams(
                language_code="-".join(turn["voice_name"].split("-")[:2]),
                name=turn["voice_name"]
            )
            audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

            response = client.synthesize_speech(
                input=synthesis_input, voice=voice_params, audio_config=audio_config
            )

            # Guarda los segmentos temporalmente
            segment_path = os.path.join(temp_segment_dir, f"segment_{i+1:02d}_{turn['speaker_id']}.mp3")
            with open(segment_path, "wb") as out:
                out.write(response.audio_content)
            segment = AudioSegment.from_file(segment_path, format="mp3") # Usa from_file
            audio_segments.append(segment)

            # Añadir pausa si no es el último turno
            if turn["pause_after"] > 0 and i < len(dialogue_turns) - 1:
                audio_segments.append(AudioSegment.silent(duration=turn["pause_after"]))

    except Exception as e:
        # Limpia los archivos temporales si hay un error
        for temp_file in os.listdir(temp_segment_dir):
            os.remove(os.path.join(temp_segment_dir, temp_file))
        os.rmdir(temp_segment_dir)
        raise RuntimeError(f"Error durante la síntesis de voz: {e}")


    # --- Unir audio y exportar ---
    if audio_segments:
        # Suma todos los segmentos de audio
        podcast = sum(audio_segments)
        podcast.export(final_podcast_path, format="mp3")
        print(f"Podcast exportado como {final_podcast_path}")
    else:
        # Esto debería ser manejado por la validación de diálogo_turns, pero es una seguridad.
        print("No se generó ningún audio a partir del CSV.")
        final_podcast_path = None # O lanza un error para que Django lo maneje

    # Limpia los archivos temporales de segmentos
    for temp_file in os.listdir(temp_segment_dir):
        os.remove(os.path.join(temp_segment_dir, temp_file))
    os.rmdir(temp_segment_dir)

    return final_podcast_path
