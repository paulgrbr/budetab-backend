# Wähle das Basis-Image
FROM python:3.13.0-slim

# Install PostgreSQL development libraries required for psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc

# Setze den Arbeitsverzeichnispfad
WORKDIR /app

# Kopiere Abhängigkeiten und installiere sie
COPY /requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den Rest der App
COPY src/ .

# Exponiere den Flask-Port
EXPOSE 8085

# Starte den Flask-Server
CMD ["python", "app.py"]