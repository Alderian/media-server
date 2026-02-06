# Fixarr: Media Library Organizer

Fixarr is an automated, non-interactive tool to organize your media library (movies, TV shows, and music) into a clean structure compatible with Jellyfin.

## Features
- **Automated Scanning**: Recursively scans your source directory.
- **Smart Classification**: Detects movies, TV shows, and music albums automatically.
- **Metadata Integration**: Uses TMDB and IMDb for video, and MusicBrainz (via Beets) for music.
- **Jellyfin Compatible**: Generates `.nfo` files and organizes folders in a way that Jellyfin understands.
- **Caching**: Local cache for metadata to avoid redundant API calls.
- **Reporting**: Generates a detailed `report.json` after each run.

## Installation
Run the provided installation script on your Debian-based system:
```bash
chmod +x install.sh
./install.sh
```

## Usage
Run the main script providing source and destination paths:
```bash
python3 main.py --src /path/to/unorganized/media --dst /path/to/organized/library
```

## Project Structure
- `main.py`: Entrypoint for the application.
- `scanner.py`: Media detection and grouping logic.
- `metadata.py`: API integration (TMDB, IMDb) and caching.
- `organizer.py`: File movement and `.nfo` generation.
- `utils.py`: Common helper functions.
- `tests/`: Unit tests for the application.

## Helper Scripts
- `install.sh`: Installs system and python dependencies.
- `run_tests.sh`: Executes the test suite.
- `update_metadata_cache.sh`: Clears the local metadata cache.