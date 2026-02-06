# AGENTS.md - System Documentation

## How it works
Fixarr operates in a pipeline:
1. **Scanning**: `scanner.py` walks through the `SRC_PATH`, identifying files by extension. It groups files in the same directory that appear related (e.g., multiple music files become an "album", multiple video files with SXXEXX patterns become a "TV Show").
2. **Metadata**: `metadata.py` takes the identified names and queries TMDB or IMDb. It uses a local `metadata_cache.json` to store results.
3. **Organization**: `organizer.py` moves files to `DST_PATH` using a predefined structure:
   - `Movies/Title (Year)/Title (Year).ext`
   - `Series/Show Title/Season XX/Show Title - SXXEXX.ext`
   - `Music/Artist/Album/Track Title.ext` (handled by `beets`)
4. **Jellyfin Metadata**: For videos, `.nfo` files are created alongside the media.

## Automatic Classification Rules
- **Video**: `.mkv, .mp4, .avi`.
- **Audio**: `.mp3, .flac, .wav`.
- **TV Show**: Detected if filename contains patterns like `S01E01` or `1x01`.
- **Movie**: Video files that don't match TV patterns.
- **Subtitles**: Moved if they match the video filename base.

## Caching
Metadata is cached in `metadata_cache.json` using a key composed of the cleaned name and year.

## Dependencies
- `beets`: For music organization.
- `tmdbsimple`: TMDB API wrapper.
- `Cinemagoer`: IMDb API wrapper.
- `exiftool`: For metadata reading.