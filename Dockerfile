FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Carpeta persistente para la base de datos SQLite.
# Debe montarse como volumen al ejecutar el contenedor.
RUN mkdir -p /app/data

ENV DATABASE_PATH=/app/data/database.db
ENV FLASK_DEBUG=0

EXPOSE 5000

CMD ["python", "app.py"]
