FROM python:3.11-slim

# Metadata
LABEL maintainer="your-email@example.com"
LABEL description="Pterodactyl Port Mapper for OPNsense"

# Arbeitsverzeichnis erstellen
WORKDIR /app

# Dependencies kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Script kopieren
COPY main.py .

# Nicht-root User erstellen
RUN useradd -m -u 1000 portmapper && \
    chown -R portmapper:portmapper /app

USER portmapper

# Umgebungsvariablen für Python
ENV PYTHONUNBUFFERED=1

# Script starten
CMD ["python", "-u", "main.py"]
