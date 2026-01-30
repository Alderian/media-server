#!/bin/bash

# Cargar variables de entorno
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

echo "Iniciando reinicio del Media Server..."

# Detener contenedores existentes
docker compose down

# Descargar últimas imágenes y levantar servicios
docker compose pull
docker compose up -d --remove-orphans

# Limpieza de imágenes huérfanas
docker image prune -f

echo "¡Media Server reiniciado con éxito!"
