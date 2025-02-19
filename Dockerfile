# Wähle das Basis-Image
FROM python:3.13.0-slim

# Install PostgreSQL development libraries required for psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc

# Install remove-background dependencies
RUN mkdir -p /root/.u2net && \
    curl -L https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx -o /root/.u2net/u2net.onnx

# Set environment variables
ENV PYTHONUNBUFFERED 1

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
# CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "src.app:app"]