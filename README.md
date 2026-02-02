# Media Server

Este proyecto es un servidor multimedia consolidado, optimizado para ejecutarse en una Raspberry Pi. Incluye la **Suite ARR** para automatización de descargas y organización de medios, permitiendo el uso de **Hard Links** para ahorrar espacio y tiempo.

## Servicios Incluidos

### 🎬 Media & Streaming

| Servicio | Descripción | Puerto | Documentación |
| :--- | :--- | :---: | :--- |
| **[Jellyfin](http://localhost:8096)** | Servidor multimedia para streaming de películas, series y música | `8096` | [Docs](https://jellyfin.org/docs/) • [Configuración](https://jellyfin.org/docs/general/quick-start.html) |

### 🔎 ARR Suite - Automatización de Medios

| Servicio | Descripción | Puerto | Documentación |
| :--- | :--- | :---: | :--- |
| **[Prowlarr](http://localhost:9696)** | Gestor centralizado de indexadores (trackers) | `9696` | [Wiki](https://wiki.servarr.com/prowlarr) • [Configuración](https://wiki.servarr.com/prowlarr/quick-start-guide) |
| **[Radarr](http://localhost:7878)** | Gestión automática de películas | `7878` | [Wiki](https://wiki.servarr.com/radarr) • [Guía](https://wiki.servarr.com/radarr/quick-start-guide) |
| **[Sonarr](http://localhost:8989)** | Gestión automática de series | `8989` | [Wiki](https://wiki.servarr.com/sonarr) • [Guía](https://wiki.servarr.com/sonarr/quick-start-guide) |
| **[Lidarr](http://localhost:8686)** | Gestión automática de música | `8686` | [Wiki](https://wiki.servarr.com/lidarr) • [Guía](https://wiki.servarr.com/lidarr/quick-start-guide) |
| **[Bazarr](http://localhost:6767)** | Gestión automática de subtítulos | `6767` | [Wiki](https://wiki.bazarr.media/) • [Setup](https://wiki.bazarr.media/Getting-Started/Setup-Guide/) |

### 📥 Clientes de Descarga

| Servicio | Descripción | Puerto | Documentación |
| :--- | :--- | :---: | :--- |
| **[qBittorrent](http://localhost:8080)** | Cliente BitTorrent (credenciales: `admin`/`adminadmin`) | `8080` | [Wiki](https://github.com/qbittorrent/qBittorrent/wiki) • [WebUI](https://github.com/qbittorrent/qBittorrent/wiki/WebUI-API-(qBittorrent-4.1)) |
| **[NZBGet](http://localhost:6789)** | Cliente de descargas Usenet | `6789` | [Docs](https://nzbget.com/documentation) • [Configuración](https://nzbget.com/documentation/configuration/) |
| **[aMule](http://localhost:4711)** | Cliente eMule/eDonkey2000 | `4711` | [Wiki](https://github.com/amule-project/amule/wiki) • [WebUI](https://wiki.amule.org/wiki/AMuleWeb) |

### 🎯 Gestión de Solicitudes

| Servicio | Descripción | Puerto | Documentación |
| :--- | :--- | :---: | :--- |
| **[Jellyseerr](http://localhost:5055)** | Sistema de solicitudes de medios (Jellyfin) | `5055` | [Docs](https://docs.jellyseerr.dev/) • [Setup](https://docs.jellyseerr.dev/getting-started/installation) |

### 📊 Dashboard & Herramientas

| Servicio | Descripción | Puerto | Documentación |
| :--- | :--- | :---: | :--- |
| **[Homarr](http://localhost:7575)** | Dashboard centralizado para todos los servicios | `7575` | [Docs](https://homarr.dev/docs/introduction) • [Getting Started](https://homarr.dev/docs/getting-started) |
| **[FlareSolverr](http://localhost:8191)** | Proxy para bypass de protección Cloudflare | `8191` | [GitHub](https://github.com/FlareSolverr/FlareSolverr) • [Setup con Prowlarr](https://github.com/FlareSolverr/FlareSolverr#usage) |

### 🔒 Servicios de Red (Comentados)

> [!NOTE]
> Los siguientes servicios están comentados en el `docker-compose.yml` y pueden habilitarse según necesidad:

| Servicio | Descripción | Puerto | Documentación |
| :--- | :--- | :---: | :--- |
| **Pi-hole** | Bloqueador de publicidad y servidor DNS | `8091` | [Docs](https://docs.pi-hole.net/) • [Setup](https://docs.pi-hole.net/main/basic-install/) |
| **Wireguard** | VPN server (wg-easy) | `51821` | [Docs](https://github.com/wg-easy/wg-easy) • [Setup](https://github.com/wg-easy/wg-easy/wiki) |
| **Gluetun** | Cliente VPN para enrutar tráfico | — | [Wiki](https://github.com/qdm12/gluetun-wiki) • [Providers](https://github.com/qdm12/gluetun-wiki/tree/main/setup/providers) |

## 🚀 Guía de Configuración Inicial

Una vez que todos los servicios estén en ejecución, sigue este orden para configurarlos:

1. **[Prowlarr](http://localhost:9696)** (Primero) - Configura tus indexadores/trackers
   - Agrega indexadores de torrents
   - Configura FlareSolverr si necesitas bypass de Cloudflare (URL: `http://flaresolverr:8191`)
   - Integra con Radarr, Sonarr y Lidarr (se conectarán automáticamente)

2. **Clientes de Descarga** - Configura qBittorrent/NZBGet
   - **qBittorrent**: Cambia la contraseña por defecto (`admin`/`adminadmin`)
   - Configura las rutas de descarga en `/data/descargas/`

3. **[Radarr](http://localhost:7878)** / **[Sonarr](http://localhost:8989)** / **[Lidarr](http://localhost:8686)**
   - Agrega tu cliente de descargas (URL: `http://qbittorrent:8080`)
   - Configura carpetas raíz: `/data/media/peliculas`, `/data/media/series`, `/data/media/musica`
   - Los indexadores ya estarán disponibles desde Prowlarr

4. **[Bazarr](http://localhost:6767)** - Configura subtítulos
   - Conecta con Radarr y Sonarr
   - Agrega proveedores de subtítulos (OpenSubtitles, etc.)

5. **[Jellyfin](http://localhost:8096)** - Configura tu servidor multimedia
   - Agrega bibliotecas apuntando a `/data/media/peliculas`, `/data/media/series`, etc.
   - Configura usuarios y permisos

6. **[Jellyseerr](http://localhost:5055)** - Sistema de solicitudes
   - Conecta con Jellyfin
   - Integra Radarr y Sonarr para automatizar solicitudes

7. **[Homarr](http://localhost:7575)** - Dashboard
   - Agrega widgets para todos tus servicios

> [!IMPORTANT]
> **Hard Links**: Todos los servicios ARR están configurados para usar `/data` como raíz compartida. Esto permite que Radarr/Sonarr creen hard links en lugar de copiar archivos, ahorrando espacio y tiempo.

## Requisitos Previos

- Docker y Docker Compose
- **Opcional**: Red `pihole_wg_network` (solo si habilitas Pi-hole y Wireguard):
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

- **`DOCKERDIR`**: Donde se guardan las configuraciones de los contenedores
  - Ejemplo: `/home/oscar/media-server`
  - Aquí se almacenan las bases de datos y configuraciones de cada servicio

- **`MEDIADIR`**: Raíz compartida para medios y descargas (**crítico para hard links**)
  - Ejemplo: `/home/pi`
  - **Estructura recomendada**:
    ```text
    ${MEDIADIR}/
    ├── descargas/           # Descargas de torrents/usenet
    │   ├── peliculas/
    │   ├── series/
    │   ├── musica/
    │   └── libros/
    └── media/               # Biblioteca organizada
        ├── peliculas/
        ├── series/
        ├── musica/
        └── libros/
    ```

> [!IMPORTANT]
> **¿Por qué esta estructura?** 
> - Tener `descargas/` y `media/` dentro de la misma raíz (`${MEDIADIR}`) permite que Radarr/Sonarr/Lidarr creen **hard links** en lugar de copiar archivos.
> - Esto ahorra espacio en disco (un archivo de 4GB solo ocupa 4GB, no 8GB) y es instantáneo.
> - Si `descargas/` y `media/` están en particiones diferentes, los hard links no funcionan y se copiarán archivos.

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
