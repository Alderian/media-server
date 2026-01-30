# Media Server

Este proyecto es un servidor multimedia consolidado, optimizado para ejecutarse en una Raspberry Pi. Incluye la **Suite ARR** para automatización de descargas y organización de medios, permitiendo el uso de **Hard Links** para ahorrar espacio y tiempo.

## Servicios Incluidos

| Servicio | Descripción | Puerto Web / Acceso |
| :--- | :--- | :--- |
| **Jellyfin** | Servidor multimedia (Streaming) | [8096](http://localhost:8096) |
| **Prowlarr** | Gestor de Indexadores (Busca torrents) | [9696](http://localhost:9696) |
| **Radarr** | Gestión de Películas | [7878](http://localhost:7878) |
| **Sonarr** | Gestión de Series | [8989](http://localhost:8989) |
| **Bazarr** | Gestión de Subtítulos | [6767](http://localhost:6767) |
| **qBittorrent** | Cliente de torrents | [8080](http://localhost:8080) |
| **aMule** | Cliente eMule | [4711](http://localhost:4711) |
| **Pi-hole** | Bloqueador de publicidad y DNS | [8091](http://localhost:8091/admin) |
| **Wireguard** | VPN (wg-easy) | [51821](http://localhost:51821) |

## Requisitos Previos

- Docker y Docker Compose
- Red `pihole_wg_network` (requerida por Pi-hole y Wireguard):
  ```bash
  docker network create pihole_wg_network
  ```

## Configuración y Estructura

El servidor se organiza de la siguiente manera para optimizar el uso de **Hard Links** (fundamental para la suite ARR):

```text
media-server/
├── docker-compose.yml   # Configuración centralizada
├── .env                 # Variables de entorno y rutas
└── restart.sh           # Script de gestión única
```

### Configuración de Rutas (.env)
Edita el archivo `.env` para definir dónde residen tus datos:
- `DOCKERDIR`: Donde se guardan las configuraciones de los contenedores (ej: `/home/oscar/media-server`).
- `MEDIADIR`: Donde reside el contenido (ej: `/home/pi`). Dentro de esta ruta deben existir las carpetas `media` (películas/series) y `descargas`.

## Uso y Mantenimiento

Para iniciar o actualizar todo el servidor multimedia:

```bash
sh restart.sh
```

Este script se encarga de:
1. Detener los contenedores.
2. Descargar las últimas versiones de las imágenes.
3. Levantar todos los servicios definidos en `docker-compose.yml`.
4. Limpiar imágenes antiguas.

---
> [!TIP]
> Al estar todos los servicios en un mismo archivo y red, pueden comunicarse entre sí usando sus nombres de servicio (ej: `http://qbittorrent:8080`).
