# config.py

import pyaudio

# --- CONFIGURACIÓN DE RED ---
# La dirección IP del servidor.
# - Para pruebas en la misma máquina, usa '127.0.0.1' (localhost).
# - Para conectar desde otra máquina en la misma red, usa la IP local del servidor (ej. '192.168.1.10').
SERVER_HOST = "127.0.0.1"

# El puerto en el que el servidor escuchará.
SERVER_PORT = 5555

# --- CONFIGURACIONES DE AUDIO ---
# Deben ser idénticas en el cliente y el servidor.
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16  # Calidad de audio estándar de 16-bit
SAMPLE_WIDTH = 2          # Ancho de la muestra en bytes para paInt16
CHANNELS = 1              # Audio monofónico
RATE = 44100              # Tasa de muestreo estándar (calidad de CD)