FROM python:3.12-slim

# Evite les .pyc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /air-quality-app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .


# dash port app
EXPOSE 8051


CMD [ "python3", "dashboard/air_quality" ]