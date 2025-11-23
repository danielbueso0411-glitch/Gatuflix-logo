# Usamos una imagen base de Python oficial
FROM python:3.10-slim

# 1. Instalar dependencias del sistema y Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2. Instalar Google Chrome (Versión Estable)
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 3. Crear la carpeta /content para que tu código no falle
# (Como tu código busca guardar fotos en /content/, creamos esa carpeta aquí)
RUN mkdir -p /content

# 4. Copiar tus archivos al servidor
WORKDIR /app
COPY . /app

# 5. Instalar librerías de Python
RUN pip install --no-cache-dir -r requirements.txt

# 6. Comando para iniciar el bot (asegúrate que tu archivo python se llame bot.py)
CMD ["python", "bot.py"]
