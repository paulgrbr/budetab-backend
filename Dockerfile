# Wähle das Basis-Image
FROM python:3.13.0

# Setze den Arbeitsverzeichnispfad
WORKDIR /app

# Kopiere Abhängigkeiten und installiere sie
COPY /requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den Rest der App
COPY app/ .

# Exponiere den Flask-Port
EXPOSE 8085

# Starte den Flask-Server
CMD ["python", "app.py"]