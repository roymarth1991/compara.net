# 1) Imagen base ligera de Python
FROM python:3.10-slim

# 2) Instala herramientas y librerías de sistema para compilar extensiones y soportar navegadores headless
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential python3-dev libffi-dev curl \
      libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
      libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
      libpango-1.0-0 libxss1 libasound2 libxtst6 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# 3) Crea y activa virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 4) Upgrade pip/setuptools/wheel
RUN pip install --upgrade pip setuptools wheel

# 5) Copia e instala dependencias de Python
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# 6) Instala navegadores de Playwright
RUN python -m playwright install

# 7) Copia el resto de tu aplicación
COPY . .

# 8) (Opcional) Expone un puerto estático para documentación
EXPOSE 8000

# 9) Arranque con Gunicorn en modo producción usando el puerto dinámico de Railway
#    Se usa sh -c para que expanda la variable $PORT
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:$PORT --workers 4"]
