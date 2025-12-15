FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Chromium + chromedriver
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium chromium-driver \
    fonts-liberation \
    ca-certificates \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["python", "app.py"]

LABEL org.opencontainers.image.title="WebShot Mailer"
LABEL org.opencontainers.image.description="Captura paginas web y las envia por correo"
LABEL org.opencontainers.image.vendor="psdani9xo"
LABEL org.opencontainers.image.source="https://github.com/psdani9xo/webshot-mailer"
LABEL org.opencontainers.image.url="https://hub.docker.com/r/psdani9xo/webshot-mailer"
