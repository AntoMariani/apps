# 📘 Manual de uso – TRANSCRIPTIONS

Esta aplicación permite convertir grabaciones de clases o cualquier otro tipo de audio o video en una transcripción detallada, además de generar un resumen estilo apuntes teóricos.

---

## 🧱 Requisitos

- Python 3.9 o superior
- ffmpeg instalado y agregado al PATH
- Acceso a internet (para YouTube o Google Drive)

Librerías Python necesarias:
```bash
pip install -r requirements.txt
```
(El archivo `requirements.txt` debe incluir: `whisper`, `gdown`, `yt-dlp`, `python-slugify`, `pyperclip`, etc.)

---

## 🛠 Estructura del proyecto

```
TRANSCRIPTIONS/
├── transcriber.py               # Script principal
├── requirements.txt             # Requisitos Python
├── Manual.md                    # Este archivo con instrucciones
├── contents/                    # Carpeta donde se guarda cada sesión
│   └── video-nombre-fecha/
│       ├── media/               # Video, audio original y audio limpio
│       ├── segments/            # Segmentos divididos
│       │   ├── audio/           # Segmentos .wav
│       │   └── transcript/      # Transcripciones por segmento
│       └── transcripcion.txt    # Transcripción final
├── logs/                        # Registro detallado por ejecución
├── local-video/                 # Carpeta opcional donde poner archivos manualmente
└── dist/                        # Carpeta que contiene el ejecutable (.exe)
```

---

## ▶️ Cómo usar la app

### OPCIÓN 1 – Ejecutar desde consola (modo desarrollador)

```bash
python transcriber.py
```

### OPCIÓN 2 – Ejecutar como programa (.exe)

1. Descargá la versión compilada desde el repositorio de GitHub.

2. Andá a la carpeta:
```
TRANSCRIPTIONS/dist/
```
Y ejecutá el archivo:
```
transcriber.exe
```

💡 Si preferís evitar la consola completamente, hacé doble clic sobre ese `.exe`. Es posible que tarde unos segundos en iniciar (ver más abajo).

### 3. Elegir la fuente del audio:
- **1. Archivo local:** Podés escribir la ruta completa o dejar el archivo dentro de `local-video/` y escribir el nombre.
- **2. YouTube:** Pegá la URL del video.
- **3. Google Drive:** Ingresá el ID del archivo (debe ser público o compartido).

### 4. La app hará lo siguiente automáticamente:
- Extrae el audio del video.
- Elimina silencios largos.
- Selecciona el modelo Whisper adecuado según la duración.
- Corta el audio en segmentos de 30 segundos.
- Transcribe cada segmento con seguimiento de progreso y ETA.
- Une las transcripciones.
- Genera un prompt listo para usar en ChatGPT.
- Abre el navegador y la carpeta de resultados.

---

## 💡 Consejos

- Usá videos con buena calidad de audio para mejores resultados.
- Si tu PC tiene poca RAM, evitá ejecutar muchos programas mientras corre el script.
- Podés modificar el modelo Whisper en el código si preferís mayor precisión (ej: usar "medium").

---

## 🤖 ChatGPT y resumen automático

Una vez que termina el proceso:
- Se copia un prompt al portapapeles.
- Se abre ChatGPT en el navegador.
- Se abre la carpeta con el archivo `transcripcion.txt` para que puedas subirlo.

Este prompt está diseñado para generar un resumen estilo apuntes teóricos.

---

## 📂 Logs

Cada ejecución guarda un archivo de log en `logs/`, donde se indica:
- Tiempo por segmento
- ETA estimado
- Qué segmentos fueron transcritos correctamente
- Si se omitieron algunos (por estar ya hechos)

---

## 📞 ¿Problemas comunes?

- **"ffmpeg not found"**: Asegurate de tener ffmpeg instalado y agregado al PATH del sistema.
- **"Permission denied"**: Ejecutá el script desde una terminal con permisos.
- **Transcripción lenta**: Cambiá el modelo a "tiny" para mayor velocidad (menos precisión).

---

## ✨ Créditos
Creado con ❤️ para facilitar la vida académica y mejorar la organización de apuntes desde grabaciones reales.

