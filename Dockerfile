# Usamos una imagen base ligera de Python
FROM python:3.10-slim

# 1. Instalar herramientas básicas necesarias
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    unzip \
    ca-certificates \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# 2. Instalar Chrome Directamente (Método .deb)
# Esto evita el error de las llaves (apt-key) descargando el instalador oficial
RUN apt-get update \
    && wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# 3. Crear la carpeta /content para que el bot guarde sus fotos
RUN mkdir -p /content

# 4. Copiar tus archivos al servidor
WORKDIR /app
COPY . /app

# 5. Instalar las librerías de Python (requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# 6. Comando de arranque
CMD ["python", "bot.py"]
