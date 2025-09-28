# Usa una imagen oficial de Python como base
FROM python:3.9-slim

# Instala las dependencias del sistema operativo necesarias para PyAudio
# Esto es como ejecutar 'sudo apt-get install' en el servidor
RUN apt-get update && apt-get install -y \
    build-essential \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia el archivo de requerimientos primero (para aprovechar el caché de Docker)
COPY requirements.txt .

# Instala las librerías de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto del código de tu aplicación al contenedor
COPY . .

# El comando que se ejecutará cuando el servidor inicie
CMD ["python", "idioma_server.py"]