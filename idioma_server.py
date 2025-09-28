# idioma_server.py (VERSIÓN FINAL Y LISTA PARA DESPLIEGUE EN LA NUBE)

import os
import socket
import threading
import io
import speech_recognition as sr
from googletrans import Translator
from gtts import gTTS

# Importamos solo las variables de configuración de audio.
# El host y el puerto se definirán dinámicamente para la nube.
from config import SAMPLE_WIDTH, CHANNELS, RATE

# --- INICIALIZACIÓN DE HERRAMIENTAS ---
r = sr.Recognizer()
translator = Translator()
clients = []
lock = threading.Lock()

# --- FUNCIONES DE LÓGICA ---
def traducir_audio_stream(audio_bytes, lang_codes):
    """
    Recibe los bytes de un audio, lo transcribe, lo traduce y devuelve
    los bytes del audio traducido.
    """
    lang1_stt, lang1_tts = lang_codes[0]
    lang2_stt, lang2_tts = lang_codes[1]

    try:
        audio_data = sr.AudioData(audio_bytes, sample_rate=RATE, sample_width=SAMPLE_WIDTH)
        
        texto_detectado = ""
        try:
            texto_detectado = r.recognize_google(audio_data, language=lang1_stt)
        except sr.UnknownValueError:
            try:
                texto_detectado = r.recognize_google(audio_data, language=lang2_stt)
            except sr.UnknownValueError:
                print("-> No se pudo entender el audio.")
                return None
        
        if not texto_detectado:
            return None

        print(f"-> Detectado: '{texto_detectado}'")

        detected_lang_obj = translator.detect(texto_detectado)
        if detected_lang_obj:
            detected_lang = detected_lang_obj.lang
            destino_tts = lang2_tts if detected_lang == lang1_tts else lang1_tts
            
            texto_traducido = translator.translate(texto_detectado, dest=destino_tts).text
            print(f"-> Traducido a ({destino_tts}): '{texto_traducido}'")

            fp = io.BytesIO()
            gTTS(text=texto_traducido, lang=destino_tts).write_to_fp(fp)
            fp.seek(0)
            return fp.read()
        else:
            print("-> No se pudo detectar el idioma del texto.")
            return None

    except Exception as e:
        print(f"!! Error en el proceso de traducción: {e}")
        return None

def broadcast(message, sender_socket):
    """
    Envía un mensaje a todos los clientes conectados excepto al remitente.
    """
    with lock:
        # Hacemos una copia de la lista para iterar de forma segura
        for client_socket in clients[:]:
            if client_socket != sender_socket:
                try:
                    client_socket.sendall(message)
                except Exception as e:
                    print(f"!! Error al enviar a un cliente, eliminándolo: {e}")
                    clients.remove(client_socket)

def handle_client(client_socket):
    """
    Gestiona la conexión de un cliente en un hilo dedicado.
    """
    print(f"[NUEVA CONEXIÓN] {client_socket.getpeername()} conectado.")
    with lock:
        clients.append(client_socket)

    try:
        while True:
            header = client_socket.recv(4)
            if not header:
                break
            
            message_length = int.from_bytes(header, byteorder='big')
            
            audio_chunks = []
            bytes_received = 0
            while bytes_received < message_length:
                chunk = client_socket.recv(min(message_length - bytes_received, 4096))
                if not chunk: raise ConnectionError("La conexión se cerró inesperadamente.")
                audio_chunks.append(chunk)
                bytes_received += len(chunk)
            
            audio_bytes = b''.join(audio_chunks)
            print(f"-> Recibidos {len(audio_bytes)} bytes de audio de {client_socket.getpeername()}.")
            
            lang_codes = (('en-US', 'en'), ('es-ES', 'es'))
            translated_audio = traducir_audio_stream(audio_bytes, lang_codes)
            
            if translated_audio:
                translated_header = len(translated_audio).to_bytes(4, byteorder='big')
                print(f"-> Enviando {len(translated_audio)} bytes de audio traducido.")
                broadcast(translated_header + translated_audio, client_socket)

    except (ConnectionResetError, ConnectionError) as e:
        print(f"[CONEXIÓN PERDIDA] {client_socket.getpeername()} se desconectó: {e}")
    finally:
        with lock:
            if client_socket in clients:
                clients.remove(client_socket)
        print(f"[DESCONEXIÓN] {client_socket.getpeername()} desconectado. Clientes activos: {len(clients)}")
        client_socket.close()

def start_server():
    """ 
    Inicia el servidor, se enlaza a la dirección y puerto correctos,
    y espera conexiones de clientes.
    """
    # --- CAMBIOS CLAVE PARA DESPLIEGUE EN LA NUBE ---
    # Escucha en '0.0.0.0' para aceptar conexiones desde cualquier dirección IP.
    HOST = '0.0.0.0'
    # Lee el puerto asignado por el servicio en la nube (ej. Render, Heroku).
    # Si no encuentra la variable de entorno 'PORT', usa 5555 para pruebas locales.
    PORT = int(os.environ.get('PORT', 5555))
    # --- FIN DE LOS CAMBIOS ---

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()
    print(f"✅ [SERVIDOR INICIADO] Escuchando en {HOST}:{PORT}")

    while True:
        client_socket, _ = server.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket,))
        thread.start()

if __name__ == "__main__":
    start_server()