FROM python:3.12-slim

# Evite les .pyc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /air-quality-app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# les permissions
RUN mkdir -p /air-quality-app/data /air-quality-app/logs && chmod -R 777 /air-quality-app/data /air-quality-app/logs
# fastapi port

CMD [ "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "7860" ]