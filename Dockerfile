FROM python:3-12-13-slim

WORKDIR /meteo-app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache -r requirements.txt








CMD [ "python3" ]