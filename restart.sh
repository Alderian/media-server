#!/bin/bash

# Cargar variables de entorno
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

echo "Iniciando reinicio del Media Server..."

# Detener contenedores existentes
docker compose down

## Elimina las imagenes docker que no se terminaron de crear y quedan con None
# docker images --quiet --filter=dangling=true | xargs --no-run-if-empty docker rmi

# Limpieza de redes anteriores
# (se deben ejecutar ambos comandos porque las imagenes quedan pegadas a la red anterior)
# docker network prune
# docker system prune -f -a --volumes

# Descargar últimas imágenes y levantar servicios
docker compose pull
docker compose up -d --remove-orphans

# Limpieza de imágenes huérfanas
docker image prune -f

echo "====================================================================="
echo " 🪪 Listado de imagenes, servicios y status"
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}"
echo "====================================================================="

duration=$SECONDS
echo " ✅ Reinicio finalizado: $(date +'%Y-%m-%d %T')"
echo " ⏲️  Tiempo de reinicio: $((duration / 60)) minutos y $((duration % 60)) segundos."

echo "¡Media Server reiniciado con éxito!"
