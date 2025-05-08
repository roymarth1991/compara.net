# Usa la imagen oficial ligera de Python
FROM python:3.10-slim

# 1) Instala herramientas de compilación y dependencias de sistema
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential python3-dev libffi-dev curl \
      libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
      libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
      libpango-1.0-0 libxss1 libasound2 libxtst6 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# 2) Crea y activa un virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 3) Actualiza pip, setuptools y wheel
RUN pip install --upgrade pip setuptools wheel

# 4) Copia y instala las dependencias Python
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# 5) Instala navegadores y dependencias de Playwright
RUN playwright install --with-deps

# 6) Copia el resto de tu aplicación
COPY . .

# 7) Expone el puerto en el que corre tu app
EXPOSE 8000

# 8) Comando de arranque
CMD ["python", "app.py"]
