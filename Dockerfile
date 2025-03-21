# Wähle das Basis-Image
FROM python:3.13.0-slim

# Install PostgreSQL development libraries required for psycopg2
# Install necessary dependencies
RUN apt-get update && apt-get install -y libpq-dev gcc curl && rm -rf /var/lib/apt/lists/*

# Install remove-background dependencies
RUN mkdir -p /root/.u2net && \
    curl -L https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx -o /root/.u2net/u2net.onnx

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Setze den Arbeitsverzeichnispfad
WORKDIR /app

# Kopiere Abhängigkeiten und installiere sie
COPY /requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den Rest der App
COPY src/ .

# Copy the entire 'data' folder
COPY data/ data

# Exponiere den Flask-Port
EXPOSE 8085

# Copy the entrypoint script into the container
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]

# CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "src.app:app"]