FROM python:3.12-slim

# Evite les .pyc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Synchronisation HF + collecte Open-Meteo planifiée dans l'API (nécessite HF_TOKEN pour la persistance)
ENV ENABLE_ETL_SCHEDULER=1

WORKDIR /air-quality-app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Dossiers écrits à l'exécution (HF Spaces tourne avec un utilisateur non-root)
RUN mkdir -p data/raw logs models && chmod -R 777 data logs models

EXPOSE 7860
CMD [ "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "7860" ]
