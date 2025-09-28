# config.py (CONFIGURACIÓN FINAL PARA LA NUBE)

import pyaudio

# --- CONFIGURACIÓN DE RED ---
# Apunta a tu servidor en Render.
SERVER_HOST = "idioma-server-2.onrender.com"

# El puerto público para los servicios gratuitos de Render es 10000.
SERVER_PORT = 10000

# --- CONFIGURACIONES DE AUDIO ---
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
SAMPLE_WIDTH = 2
CHANNELS = 1
RATE = 44100
