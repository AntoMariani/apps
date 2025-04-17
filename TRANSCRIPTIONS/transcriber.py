# transcribir_clase_comentado.py
# Este script permite convertir una clase grabada (video o audio) en texto transcripto.
# Se encarga de obtener el audio desde diferentes fuentes (archivo local, YouTube, Google Drive),
# eliminar silencios, dividir el audio en segmentos, transcribirlos con Whisper, unir el resultado,
# y generar un resumen en ChatGPT de forma asistida. Este archivo está extremadamente comentado
# para personas que no saben nada de Python.

# -------------------------------
# IMPORTACIÓN DE LIBRERÍAS
# -------------------------------
# Cada "import" agrega funcionalidades específicas al script.

import os  # Permite acceder a funciones del sistema operativo, como crear carpetas, ejecutar comandos, etc.
import subprocess  # Permite ejecutar comandos externos como ffmpeg o ffprobe para manejar archivos multimedia
import time  # Sirve para medir cuánto tarda una operación (en segundos)
import datetime  # Permite obtener la fecha y hora actual, útil para organizar archivos con timestamps
import gc  # "Garbage collector", limpia la memoria para evitar saturarla durante muchas operaciones seguidas

import whisper  # Esta es la librería de OpenAI para convertir audio en texto (Speech-to-Text)
import gdown  # Permite descargar archivos directamente desde Google Drive a través de su ID
import yt_dlp  # (youtube-dl plus) Permite descargar videos o audios desde plataformas como YouTube
import webbrowser  # Sirve para abrir automáticamente el navegador web con una URL
import pyperclip  # Permite copiar texto directamente al portapapeles (como un copiar/pegar automático)

from pathlib import Path  # Reemplaza las rutas de archivos tipo string por objetos más seguros y flexibles
from slugify import slugify  # Convierte textos como "Clase de diseño 1" en nombres válidos de archivo como "clase-de-diseno-1"
import platform  # Detecta el sistema operativo (Windows, Linux, Mac) para ejecutar acciones específicas

# -------------------------------
# CONFIGURACIONES Y VARIABLES GLOBALES
# -------------------------------
# Estas variables definen parámetros iniciales que se usan a lo largo del programa

SEGMENT_LENGTH = 30  # Cada cuánto cortar el audio en segundos (30 segundos por segmento)

# Define dónde está ubicado el archivo actual, sin importar desde dónde se lo ejecute
PROJECT_ROOT = Path(__file__).resolve().parent  # __file__ es el nombre del archivo actual. resolve().parent da su carpeta

# Marca temporal única que se le pone a cada ejecución (ej: 20250416-221015)
TIMESTAMP = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')

# VIDEO_LABEL será el "nombre base" de todo el contenido relacionado con ese audio (se modifica más adelante)
VIDEO_LABEL = "audio"  # Valor inicial por defecto, se cambia con el nombre real del video

# Carpeta principal donde se va a guardar todo el contenido de la transcripción
BASE_DIR = PROJECT_ROOT / "contents"  # contents/ estará en la misma carpeta que este archivo

# Carpeta donde se guarda el registro (log) de cada ejecución (informes paso a paso)
LOGS_DIR = PROJECT_ROOT / "logs"

# Carpeta donde el usuario puede colocar manualmente archivos para transcribir
LOCAL_VIDEO_DIR = PROJECT_ROOT / "local-video"

# Variables vacías que se completarán más adelante automáticamente:
AUDIO_PATH = ""  # Ruta al archivo de audio original (extraído del video o subido por el usuario)
AUDIO_CLEANED = ""  # Ruta al archivo de audio limpio (sin silencios)
VIDEO_OUTPUT = ""  # Ruta al archivo de video original (si viene de YouTube o Drive)
SEGMENT_FOLDER = None  # Carpeta donde se guardarán los audios divididos en segmentos
TRANSCRIPT_FOLDER = None  # Carpeta principal del video dentro de contents/
TRANSCRIPT_SEGMENTS = None  # Carpeta donde se guardan los archivos de texto de cada segmento
FINAL_TRANSCRIPT = ""  # Archivo final que contiene la transcripción completa unificada
LOG_PATH = ""  # Archivo .txt donde se va escribiendo el log de la ejecución
MODEL_NAME = "base"  # Modelo Whisper a usar por defecto (se puede cambiar a tiny si el audio es largo)
TOTAL_SEGMENTS = 0  # Número total de segmentos (calculado más adelante)

# -------------------------------
# FUNCIONES UTILITARIAS (BÁSICAS)
# -------------------------------

def log(msg):
    """
    Esta función imprime en pantalla (y también guarda en un archivo) cada paso que está ocurriendo.
    Se le pasa un mensaje como texto, y le agrega la hora actual para mayor claridad.
    """
    timestamp = datetime.datetime.now().strftime('%H:%M:%S')  # Hora actual en formato HH:MM:SS
    full_msg = f"[{timestamp}] {msg}"  # Armamos el mensaje completo con hora + texto
    print(full_msg)  # Lo mostramos en pantalla
    if LOG_PATH:  # Si ya definimos dónde guardar el log...
        with open(LOG_PATH, "a", encoding="utf-8") as f:  # Abrimos el archivo de log en modo "append"
            f.write(full_msg + "\n")  # Escribimos el mensaje y hacemos un salto de línea

def run_ffmpeg(cmd):
    """
    Ejecuta comandos como "ffmpeg" o "ffprobe" sin mostrar nada en pantalla.
    Los comandos son listas, por ejemplo: ["ffmpeg", "-i", archivo.mp4, "salida.wav"]
    """
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)  # Ejecuta silenciosamente

def evitar_suspension():
    """
    Esta función evita que la computadora se apague o entre en reposo mientras se ejecuta el script.
    Solo aplica a Windows. Para otros sistemas podrías buscar comandos equivalentes.
    """
    log("Desactivando apagado de pantalla y suspensión...")
    os.system("powercfg -change -monitor-timeout-ac 0")  # Evita que se apague el monitor
    os.system("powercfg -change -standby-timeout-ac 0")  # Evita que entre en suspensión

def restaurar_suspension():
    """
    Esta función restaura la configuración de energía después de que termina el script.
    También solo para Windows por ahora.
    """
    log("Restaurando configuración de energía...")
    os.system("powercfg -change -monitor-timeout-ac 10")  # Apaga el monitor tras 10 minutos
    os.system("powercfg -change -standby-timeout-ac 15")  # Suspende tras 15 minutos

def abrir_carpeta(path):
    """
    Abre una carpeta o archivo específico en el sistema operativo.
    Funciona para Windows, Mac y Linux usando diferentes comandos.
    """
    if platform.system() == "Windows":
        os.startfile(path)  # En Windows se usa esta función
    elif platform.system() == "Darwin":  # Para macOS
        subprocess.Popen(["open", path])
    else:  # Para Linux u otros
        subprocess.Popen(["xdg-open", path])

# -------------------------------
# FUNCIÓN: inicializar_estructura(nombre_base)
# -------------------------------
def inicializar_estructura(nombre_base):
    """
    Esta función se encarga de preparar toda la estructura de carpetas y archivos
    necesaria para trabajar con la transcripción de un video/audio. También genera
    rutas con nombre seguro y únicos usando el nombre base y el timestamp.

    nombre_base: El nombre del archivo original o del video (sin la extensión)
    """
    # Declaramos que vamos a usar y modificar las variables globales
    global VIDEO_LABEL, SEGMENT_FOLDER, TRANSCRIPT_FOLDER, TRANSCRIPT_SEGMENTS
    global AUDIO_PATH, AUDIO_CLEANED, FINAL_TRANSCRIPT, LOG_PATH, VIDEO_OUTPUT

    # Convertimos el nombre base en un nombre de archivo seguro usando "slugify"
    VIDEO_LABEL = slugify(nombre_base)  # Ej: "Clase 1 - Requisitos" => "clase-1-requisitos"

    # Creamos la carpeta raíz para esta sesión de trabajo, por ejemplo:
    # contents/clase-1-requisitos-20250416-212115/
    session_dir = BASE_DIR / f"{VIDEO_LABEL}-{TIMESTAMP}"

    # Dentro de esa carpeta creamos otra para guardar los medios: video, audio y audio limpio
    media_dir = session_dir / "media" / f"{VIDEO_LABEL}-{TIMESTAMP}"

    # Creamos una subcarpeta donde irán los segmentos cortados
    SEGMENT_FOLDER = session_dir / "segments"

    # Dentro de "segments" creamos dos carpetas: una para los audios cortados y otra para los textos
    audio_segment_dir = SEGMENT_FOLDER / "audio"
    transcript_segment_dir = SEGMENT_FOLDER / "transcript"

    # Definimos el archivo de LOG para guardar el paso a paso de la ejecución
    LOG_PATH = LOGS_DIR / f"{VIDEO_LABEL}-{TIMESTAMP}.txt"

    # Definimos las rutas de salida de los archivos que vamos a crear:
    AUDIO_PATH = media_dir / f"{VIDEO_LABEL}-AUDIO-{TIMESTAMP}.wav"  # Audio original extraído
    AUDIO_CLEANED = media_dir / f"{VIDEO_LABEL}-AUDIO_CLEAN-{TIMESTAMP}.wav"  # Audio sin silencios
    VIDEO_OUTPUT = media_dir / f"{VIDEO_LABEL}-VIDEO-{TIMESTAMP}.mp4"  # Video original descargado (si aplica)
    FINAL_TRANSCRIPT = session_dir / "transcripcion.txt"  # Archivo final con toda la transcripción unida

    # Guardamos la ruta donde se guardarán los textos de cada segmento
    TRANSCRIPT_SEGMENTS = transcript_segment_dir

    # Creamos todas las carpetas necesarias si aún no existen (parents=True permite crear subcarpetas)
    for folder in [session_dir, SEGMENT_FOLDER, audio_segment_dir, transcript_segment_dir, media_dir, LOGS_DIR, LOCAL_VIDEO_DIR]:
        folder.mkdir(parents=True, exist_ok=True)
        (folder / ".gitkeep").touch(exist_ok=True)  # ⬅️ Esto asegura que Git registre la carpeta vacía


def obtener_audio():
    """
    Esta función le pide al usuario que elija de dónde quiere obtener el video o audio a transcribir.
    Puede ser un archivo local, un video de YouTube o un archivo de Google Drive.
    Según la opción elegida, descarga y convierte el archivo a audio .wav, y lo guarda en la carpeta correspondiente.
    """
    log("Seleccioná la fuente del audio:")  # Muestra en el log y por consola que empieza la selección

    # Opciones disponibles que se imprimen para que el usuario elija
    print("1. Archivo local")
    print("2. Video de YouTube")
    print("3. Archivo de Google Drive")

    # Esperamos que el usuario escriba 1, 2 o 3
    opcion = input("> ")  # El símbolo "> " aparece como prompt de entrada

    # --- OPCIÓN 1: Archivo local ---
    if opcion == "1":
        ruta = input("Ruta del archivo local (MP4/MKV/MP3/WAV): ")  # Se le pide que escriba la ruta al archivo

        if not Path(ruta).exists():  # Si el archivo no existe, muestra error y termina el programa
            print("❌ Ruta no encontrada. Abortando.")
            exit(1)  # Sale del programa

        # Si la ruta existe, inicializamos las carpetas necesarias usando el nombre del archivo
        inicializar_estructura(Path(ruta).stem)  # .stem toma solo el nombre sin la extensión

        # Extraemos el audio del archivo usando ffmpeg y lo guardamos como .wav
        run_ffmpeg(["ffmpeg", "-y", "-i", ruta, str(AUDIO_PATH)])

        # Movemos el archivo original a la carpeta de medios para guardarlo con el resto del contenido
        Path(ruta).rename(VIDEO_OUTPUT)

    # --- OPCIÓN 2: Video de YouTube ---
    elif opcion == "2":
        url = input("URL de YouTube: ")  # Se le pide al usuario que pegue la URL del video

        # Creamos un objeto de descarga silencioso (quiet=True)
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)  # Solo analizamos la info primero sin descargar
            titulo = info.get("title", "yt_video")  # Usamos el título como nombre base del proyecto
            inicializar_estructura(titulo)  # Creamos carpetas y rutas necesarias

            ydl.download([url])  # Descargamos el video
            Path(ydl.prepare_filename(info)).rename(VIDEO_OUTPUT)  # Lo movemos a la carpeta de medios

        # Extraemos el audio del video descargado y lo guardamos como .wav
        run_ffmpeg(["ffmpeg", "-y", "-i", str(VIDEO_OUTPUT), str(AUDIO_PATH)])

    # --- OPCIÓN 3: Google Drive ---
    elif opcion == "3":
        file_id = input("ID del archivo de Google Drive: ")  # Pedimos el ID único del archivo

        # Descargamos el archivo de Drive con el nombre temporal "temp_drive_video.mp4"
        gdown.download(id=file_id, output="temp_drive_video.mp4", quiet=False)

        inicializar_estructura("drive_video")  # Creamos estructura usando un nombre genérico

        Path("temp_drive_video.mp4").rename(VIDEO_OUTPUT)  # Lo movemos al lugar final

        # Extraemos el audio como .wav desde el archivo descargado
        run_ffmpeg(["ffmpeg", "-y", "-i", str(VIDEO_OUTPUT), str(AUDIO_PATH)])

    # --- OPCIÓN INVÁLIDA ---
    else:
        print("❌ Opción no válida. Abortando.")
        exit(1)  # Terminamos el programa si se ingresó algo incorrecto


# -------------------------------
# FUNCIÓN: quitar_silencios
# -------------------------------
def quitar_silencios():
    """
    Esta función utiliza ffmpeg para eliminar silencios del archivo de audio original.
    Los silencios que duren más de 5 segundos y estén por debajo de -50 dB se eliminan.
    El resultado se guarda en un nuevo archivo limpio.
    """
    log("Eliminando silencios del audio...")
    run_ffmpeg([
        "ffmpeg", "-y", "-i", str(AUDIO_PATH),  # -y sobreescribe archivos existentes, -i especifica el input
        "-af", "silenceremove=stop_periods=-1:stop_duration=5:stop_threshold=-50dB",  # filtro de eliminación de silencio
        str(AUDIO_CLEANED)  # salida del audio limpio
    ])

# -------------------------------
# FUNCIÓN: elegir_modelo
# -------------------------------
def elegir_modelo():
    """
    Esta función determina la duración del audio limpio y decide si conviene usar
    el modelo Whisper "tiny" (más rápido pero menos preciso) o "base" (más equilibrado).
    Si el audio dura más de 1 hora, se selecciona el modelo "tiny" automáticamente.
    """
    global MODEL_NAME
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
        str(AUDIO_CLEANED)
    ], stdout=subprocess.PIPE)
    duracion = float(result.stdout.decode().strip())  # Convertimos el resultado en segundos
    if duracion > 3600:
        MODEL_NAME = "tiny"  # Audio muy largo, priorizamos velocidad
    else:
        MODEL_NAME = "base"  # Audio más corto, podemos usar mejor calidad
    log(f"📌 Modelo seleccionado automáticamente: {MODEL_NAME} ({duracion/60:.1f} minutos de audio)")
    return duracion

# -------------------------------
# FUNCIÓN: dividir_audio
# -------------------------------
def dividir_audio():
    """
    Divide el archivo de audio limpio en pequeños segmentos de igual duración (por defecto, 30 segundos).
    Esto facilita la transcripción por partes. Los archivos se guardan en la carpeta de segmentos.
    """
    log("Dividiendo audio en segmentos...")
    audio_dir = SEGMENT_FOLDER / "audio"
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
        str(AUDIO_CLEANED)
    ], stdout=subprocess.PIPE)
    duracion = float(result.stdout.decode().strip())  # Duración del audio en segundos

    global TOTAL_SEGMENTS
    TOTAL_SEGMENTS = (int(duracion) + SEGMENT_LENGTH - 1) // SEGMENT_LENGTH  # Redondeo para arriba

    # Creamos cada archivo .wav correspondiente a un segmento de 30 segundos
    for i in range(0, int(duracion), SEGMENT_LENGTH):
        out = audio_dir / f"segment_{i}.wav"
        run_ffmpeg([
            "ffmpeg", "-y", "-i", str(AUDIO_CLEANED),
            "-ss", str(i),  # punto de inicio del corte
            "-t", str(SEGMENT_LENGTH),  # duración del corte
            str(out)
        ])

# -------------------------------
# FUNCIÓN: transcribir_segmentos
# -------------------------------
def transcribir_segmentos():
    """
    Esta función recorre todos los segmentos de audio cortados y los transcribe uno a uno usando Whisper.
    Cada segmento produce un archivo .txt con la transcripción correspondiente.
    También estima el tiempo restante para completar el proceso.
    """
    log("Iniciando transcripción con modelo: " + MODEL_NAME)
    model = whisper.load_model(MODEL_NAME)
    audio_dir = SEGMENT_FOLDER / "audio"

    # Ordenamos los archivos de audio por su número
    segmentos = sorted(audio_dir.glob("*.wav"), key=lambda p: int(p.stem.split("_")[1]))

    for i, seg in enumerate(segmentos):
        idx = int(seg.stem.split("_")[1])  # Extraemos el segundo inicial del segmento
        out_txt = TRANSCRIPT_SEGMENTS / f"segment_{idx}.txt"  # Archivo de salida .txt

        # Si ya existe y no está vacío, lo salteamos
        if out_txt.exists() and out_txt.stat().st_size > 20:
            log(f"⏩ Segmento {i+1} de {TOTAL_SEGMENTS} (segundos {idx} a {idx+SEGMENT_LENGTH}) ya transcripto.")
            continue

        log(f"🔊 Segmento {i+1} de {TOTAL_SEGMENTS} (segundos {idx} a {idx+SEGMENT_LENGTH})...")
        start_seg = time.time()
        result = model.transcribe(str(seg))  # Transcripción con Whisper

        # Guardamos el texto resultante en el archivo .txt
        with open(out_txt, "w", encoding="utf-8") as f:
            f.write(result['text'])

        # Mostramos en log cuánto tardó y el tiempo estimado restante
        duracion = time.time() - start_seg
        tiempos_segmentos.append(duracion)

        # Promedio dinámico basado en todos los tiempos anteriores
        promedio = sum(tiempos_segmentos) / len(tiempos_segmentos)
        estimado_restante = (len(segmentos) - i - 1) * promedio
        eta = datetime.datetime.now() + datetime.timedelta(seconds=estimado_restante)
        log(f"✅ Terminado en {duracion:.2f}s | ETA: {eta.strftime('%H:%M:%S')}")
        gc.collect()

# -------------------------------
# FUNCIÓN: unir_transcripcion
# -------------------------------
def unir_transcripcion():
    """
    Une todos los archivos de texto individuales en una sola transcripción final.
    El archivo final se guarda como "transcripcion.txt" dentro de la carpeta del proyecto.
    """
    log("Uniendo transcripciones...")
    archivos = sorted(TRANSCRIPT_SEGMENTS.glob("*.txt"), key=lambda p: int(p.stem.split("_")[1]))
    with open(FINAL_TRANSCRIPT, "w", encoding="utf-8") as out:
        for f in archivos:
            with open(f, "r", encoding="utf-8") as seg:
                out.write(seg.read() + "\n")

# -------------------------------
# FUNCIÓN: resumen_sin_api
# -------------------------------
def resumen_sin_api():
    """
    Esta función copia un prompt prearmado al portapapeles, abre ChatGPT en el navegador,
    y abre automáticamente la carpeta del archivo final de transcripción para que el usuario pueda subirlo.
    """
    log("Preparando prompt para resumen en ChatGPT...")
    prompt = (
        "Sos un estudiante excelente tomando apuntes teóricos. Leé esta transcripción de clase universitaria y elaborá un resumen estructurado y claro, como si fuese para estudiar.\n\n"
        "Tu prioridad es la parte teórica de la clase, explicando los conceptos clave, temas tratados, explicaciones de la profesora y el contenido importante.\n\n"
        "Además, extraé lo siguiente si está presente:\n"
        "- Comentarios o aclaraciones de la profesora\n"
        "- Ejemplos usados\n"
        "- Fechas importantes\n"
        "- Trabajos prácticos mencionados\n"
        "- Temas a ver en la próxima clase\n"
        "- Puntos clave para estudiar para el examen\n\n"
        "Organizá el resumen por tema y mantenelo limpio, preciso y bien redactado."
    )
    pyperclip.copy(prompt)
    log("📋 Prompt copiado al portapapeles. Abriendo ChatGPT y la carpeta de transcripción...")
    webbrowser.open("https://chat.openai.com")  # Abre ChatGPT en el navegador predeterminado
    abrir_carpeta(FINAL_TRANSCRIPT.parent)  # Abre la carpeta donde está el archivo final
    abrir_carpeta(FINAL_TRANSCRIPT)  # Abre el archivo final directamente en el bloc de notas (si es posible)

# --- EJECUCIÓN ---
evitar_suspension()
obtener_audio()
quitar_silencios()
elegir_modelo()
dividir_audio()
transcribir_segmentos()
unir_transcripcion()
restaurar_suspension()
resumen_sin_api()
log("🎉 Proceso finalizado. Revisá tu carpeta de transcripción.")
