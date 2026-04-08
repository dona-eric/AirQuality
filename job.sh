#!/bin/bash
echo "$(date): Lancement de la collecte et du ré-entraînement..." >> /home/donerick/Challenge 30 Days ML/logs/pipeline.log
# Remplace 'collecte.py' par le nom de ton fichier de scraping/collecte
python -m src.etl.quality_air >> /home/donerick/Challenge 30 Days ML/logs/pipeline.log 2>&1
python -m src.models.inference >> /home/donerick/Challenge 30 Days ML/logs/pipeline.log 2>&1
echo "$(date): Pipeline terminé." >> /home/donerick/Challenge 30 Days ML/logs/pipeline.log
