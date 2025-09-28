# cliente.py (VERSIÓN FINAL)

import tkinter as tk
from tkinter import messagebox
import socket
import threading
import pyaudio
import os
from playsound import playsound

from config import SERVER_HOST, SERVER_PORT, CHUNK_SIZE, FORMAT, CHANNELS, RATE

class ClientApp:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("Cliente de Traducción")
        self.ventana.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.ventana.geometry("350x250")

        self.socket = None
        self.is_connected = False
        self.is_recording = False
        
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.frames = []

        self.build_ui()

    def build_ui(self):
        conn_frame = tk.Frame(self.ventana, padx=10, pady=10)
        conn_frame.pack(fill=tk.X)
        tk.Label(conn_frame, text=f"Servidor: {SERVER_HOST}:{SERVER_PORT}").pack(side=tk.LEFT)
        self.btn_connect = tk.Button(conn_frame, text="Conectar", command=self.toggle_connection, width=12)
        self.btn_connect.pack(side=tk.RIGHT)
        
        self.status_label = tk.Label(self.ventana, text="Estado: Desconectado", fg="red", font=('Helvetica', 10, 'bold'), pady=10)
        self.status_label.pack()

        self.btn_record = tk.Button(self.ventana, text="🎤 Mantén presionado para hablar", font=('Helvetica', 12, 'bold'), state='disabled', bg='grey', fg='white')
        self.btn_record.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

        self.btn_record.bind("<ButtonPress-1>", self.start_recording)
        self.btn_record.bind("<ButtonRelease-1>", self.stop_recording)

    def toggle_connection(self):
        if self.is_connected:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((SERVER_HOST, SERVER_PORT))
            self.is_connected = True
            
            self.status_label.config(text="Estado: Conectado", fg="green")
            self.btn_connect.config(text="Desconectar")
            self.btn_record.config(state='normal', bg='#2196F3')
            
            self.receive_thread = threading.Thread(target=self.receive_audio, daemon=True)
            self.receive_thread.start()
        except Exception as e:
            messagebox.showerror("Error de Conexión", f"No se pudo conectar al servidor: {e}")

    def disconnect(self):
        self.is_connected = False
        if self.socket:
            self.socket.close()
        self.status_label.config(text="Estado: Desconectado", fg="red")
        self.btn_connect.config(text="Conectar")
        self.btn_record.config(state='disabled', bg='grey')

    def start_recording(self, event):
        if not self.is_connected: return
        self.is_recording = True
        self.btn_record.config(bg='red', text="🔴 Grabando...")
        self.frames = []
        
        self.record_thread = threading.Thread(target=self.record_audio, daemon=True)
        self.record_thread.start()

    def stop_recording(self, event):
        if not self.is_recording: return
        self.is_recording = False
        self.btn_record.config(bg='#2196F3', text="🎤 Mantén presionado para hablar")

    def record_audio(self):
        self.stream = self.p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK_SIZE)
        
        while self.is_recording:
            self.frames.append(self.stream.read(CHUNK_SIZE))

        self.stream.stop_stream()
        self.stream.close()

        if self.is_connected and self.frames:
            audio_data = b''.join(self.frames)
            try:
                header = len(audio_data).to_bytes(4, byteorder='big')
                self.socket.sendall(header)
                self.socket.sendall(audio_data)
            except Exception as e:
                print(f"Error al enviar audio: {e}")
                self.disconnect()

    def receive_audio(self):
        while self.is_connected:
            try:
                header = self.socket.recv(4)
                if not header: break
                
                message_length = int.from_bytes(header, byteorder='big')
                
                audio_chunks = []
                bytes_received = 0
                while bytes_received < message_length:
                    chunk = self.socket.recv(min(message_length - bytes_received, 4096))
                    if not chunk: raise ConnectionError()
                    audio_chunks.append(chunk)
                    bytes_received += len(chunk)
                
                audio_data = b''.join(audio_chunks)

                temp_file = "temp_received.mp3"
                with open(temp_file, "wb") as f:
                    f.write(audio_data)
                playsound(temp_file)
                os.remove(temp_file)
            except (ConnectionError, ConnectionResetError):
                break # Salir del bucle si la conexión se cierra
            except Exception as e:
                print(f"Error al recibir/reproducir audio: {e}")
                break
        
        if self.is_connected:
             self.disconnect()

    def on_closing(self):
        self.disconnect()
        self.ventana.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ClientApp(root)
    root.mainloop()