"""
Genera audio para un podcast simulado con múltiples voces en español
leyendo los diálogos desde un archivo CSV y luego une los segmentos en un único archivo MP3.

Instrucciones:
- Instala dependencias con: pip install -r requirements.txt
- Asegúrate de configurar tus credenciales de Google Cloud.
- Ejecuta el script: python podcast-from-csv.py
"""

import os
import csv
from datetime import datetime
from google.cloud import texttospeech_v1beta1 as texttospeech
from google.oauth2 import service_account
from pydub import AudioSegment
from pydub.playback import play

# --- Configuración ---
CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
DIALOGUE_CSV_PATH = os.getenv("DIALOGUE_CSV_PATH", "dialogos.csv")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output_segments")
now = datetime.now()
FINAL_PODCAST_PATH = f"podcast_final_{now.strftime('%y%m%d%H%M%S')}.mp3"

os.makedirs(OUTPUT_DIR, exist_ok=True)

try:
    credentials = service_account.Credentials.from_service_account_file(CREDENTIALS_PATH)
    client = texttospeech.TextToSpeechClient(credentials=credentials)
except Exception as e:
    raise RuntimeError(f"Error cargando credenciales: {e}")

SPEAKER_VOICES = {
    "R": {"voice_name": "es-US-Chirp3-HD-Iapetus", "pause_after": 500},
    "S": {"voice_name": "es-US-Chirp-HD-F", "pause_after": 750},
    "T": {"voice_name": "es-US-Neural2-B", "pause_after": 600}
}

# --- Leer CSV ---
dialogue_turns = []
with open(DIALOGUE_CSV_PATH, mode='r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for i, row in enumerate(reader):
        speaker_id = row['speaker'].strip()
        text = row['text'].strip()

        if speaker_id not in SPEAKER_VOICES:
            print(f"Advertencia: Speaker ID '{speaker_id}' no tiene voz definida. Línea {i+2}")
            continue

        dialogue_turns.append({
            "speaker_id": speaker_id,
            "text": text,
            "voice_name": SPEAKER_VOICES[speaker_id]["voice_name"],
            "pause_after": SPEAKER_VOICES[speaker_id]["pause_after"],
            "filename": f"segment_{i+1:02d}_{speaker_id}.mp3"
        })

# --- Generar audio ---
audio_segments = []
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
    segment_path = os.path.join(OUTPUT_DIR, turn["filename"])
    with open(segment_path, "wb") as out:
        out.write(response.audio_content)
    segment = AudioSegment.from_mp3(segment_path)
    audio_segments.append(segment)
    if turn["pause_after"] > 0 and i < len(dialogue_turns) - 1:
        audio_segments.append(AudioSegment.silent(duration=turn["pause_after"]))

# --- Unir audio ---
if audio_segments:
    podcast = sum(audio_segments[1:], audio_segments[0])
    podcast.export(FINAL_PODCAST_PATH, format="mp3")
    print(f"Podcast exportado como {FINAL_PODCAST_PATH}")
    try:
        play(podcast)
    except Exception as e:
        print(f"Reproducción fallida: {e}")
else:
    print("No se generó ningún audio.")

