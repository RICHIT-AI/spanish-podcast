# 🎙️ Podcast Generator desde CSV

Este script genera un podcast simulado con múltiples voces en español utilizando **Google Cloud Text-to-Speech**. Lee los diálogos desde un archivo CSV y produce un único archivo `.mp3` que concatena todos los segmentos generados.
🔊 **Escucha un ejemplo generado con este script**:
[Podcast de ejemplo en Google Drive](https://drive.google.com/file/d/1KLRcNGkuw-OPAG5UCCMyvnqFBbcGAvRJ/view?usp=sharing)


---

## 📂 Formato del CSV

Tu archivo `dialogos.csv` debe tener exactamente estas dos columnas con encabezados en minúsculas:

```csv
speaker,text
R,Hola, ¿cómo estás hoy?
S,Muy bien, gracias. ¿Y tú?
R,Contento de grabar este podcast.
```

- `speaker`: ID del hablante. Debe coincidir con los definidos en el script (`R`, `S`, `T`, etc.).
- `text`: Texto que se convertirá a voz con la voz correspondiente.

---

## 📦 Requisitos

- Python 3.8+
- Archivo de credenciales JSON para Google Cloud con Text-to-Speech habilitado
- `ffmpeg` instalado en el sistema (necesario para que funcione `pydub`)

---

## 🛠 Instalación

1. Crea y activa un entorno virtual (opcional pero recomendado):

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

2. Instala las dependencias:

```bash
pip install -r requirements.txt
```

### 📄 Contenido de `requirements.txt`:

```
google-cloud-texttospeech==2.15.0
pydub==0.25.1
```

3. Asegúrate de tener instalado `ffmpeg` en tu sistema y accesible desde la terminal.

---

## ⚙️ Configuración del entorno

Antes de ejecutar el script, define las siguientes variables de entorno en tu sistema:

### En Linux o macOS:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=./credentials.json
export DIALOGUE_CSV_PATH=./dialogos.csv
export OUTPUT_DIR=./output_segments
```

### En Windows (CMD):

```cmd
set GOOGLE_APPLICATION_CREDENTIALS=credentials.json
set DIALOGUE_CSV_PATH=dialogos.csv
set OUTPUT_DIR=output_segments
```

---

## ▶️ Ejecución

Una vez configurado todo, ejecuta el script:

```bash
python podcast-generator.py
```

---

## 📁 Salida esperada

- Los segmentos de audio individuales se guardan en `./output_segments/`.
- El archivo final `.mp3` se genera con un nombre como:  
  `podcast_final_250528143322.mp3` (fecha y hora).

> El script intenta reproducir automáticamente el podcast final. Si no se reproduce, puedes abrir el archivo `.mp3` manualmente con tu reproductor favorito.

---

## 🗣️ Personalizar las voces

Puedes modificar las voces asignadas a cada hablante editando el siguiente bloque en el script:

```python
SPEAKER_VOICES = {
    "R": { "voice_name": "es-US-Chirp3-HD-Iapetus", "pause_after": 500 },
    "S": { "voice_name": "es-US-Chirp-HD-F", "pause_after": 750 },
    "T": { "voice_name": "es-US-Neural2-B", "pause_after": 600 }
}
```

- Puedes consultar todas las voces disponibles en la [documentación oficial de Google Cloud TTS](https://cloud.google.com/text-to-speech/docs/voices).

---

## 🧪 Ejemplo de archivo `dialogos.csv`

Guarda esto como `dialogos.csv` para una prueba rápida:

```csv
speaker,text
R,Bienvenidos al podcast de prueba.
S,Hoy vamos a hablar sobre inteligencia artificial.
R,¡Comencemos!
```

---

## 🔒 Seguridad

- **Nunca subas tu archivo de credenciales `credentials.json` a Git**.
- Asegúrate de mantenerlo en `.gitignore` y fuera de control de versiones.

