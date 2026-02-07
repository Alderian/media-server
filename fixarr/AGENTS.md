# AGENTS.md - System Documentation

## Architecture Overview

Fixarr operates as a pipeline with the following stages:

1. **Scanning** (`scanner.py`)
   - Walks through the source directory
   - Identifies files by extension (video, audio, subtitle)
   - Groups related files (TV episodes in same folder, subtitles with videos)

2. **Name Cleaning** (`name_cleaner.py`)
   - Removes resolution tags (1080p, 4K, etc.)
   - Removes codec info (x264, HEVC, etc.)
   - Removes release group tags
   - Extracts clean title and year

3. **Metadata Fetching** (`metadata.py`)
   - Searches TMDb, IMDb, and TVmaze APIs
   - Returns multiple candidates per query
   - Caches results locally

4. **Confidence Scoring** (`scoring.py`)
   - Evaluates each candidate using fuzzy string matching
   - Scores based on title similarity, year match, keywords
   - Returns only matches above confidence threshold

5. **Organization** (`organizer.py`)
   - Uses configurable naming templates
   - Moves files to destination structure
   - Routes low-confidence matches to `review_needed/`
   - Creates NFO files for Jellyfin/Kodi

6. **Reporting** (`report.py`)
   - Generates detailed JSON report
   - Includes all candidates and scores
   - Provides summary statistics

## File Classification Rules

| Type | Detection Method |
|------|-----------------|
| Video | Extensions: `.mkv`, `.mp4`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v` |
| Audio | Extensions: `.mp3`, `.flac`, `.wav`, `.m4a`, `.ogg`, `.wma`, `.aac` |
| Subtitle | Extensions: `.srt`, `.vtt`, `.sub`, `.ass`, `.ssa`, `.idx` |
| TV Show | Filename contains patterns like `S01E01`, `1x01`, `Season X Episode Y` |
| Movie | Video files that don't match TV patterns |

## Configuration System

Configuration is loaded in order of precedence:

1. Default values (hardcoded in `config.py`)
2. `config.yaml` in current directory
3. Custom config file via `--config` flag
4. Environment variables (API keys, default paths)

## Confidence Scoring

The scoring system evaluates matches using:

- **Title Similarity** (50% weight): Fuzzy string matching using rapidfuzz
- **Year Match** (30% weight): Exact match = 1.0, within tolerance = 0.8
- **Keyword Overlap** (20% weight): Common words between title and metadata

Default minimum confidence threshold: **0.7**

## Dependencies

- `tmdbsimple`: TMDb API wrapper
- `cinemagoer`: IMDb data access
- `rapidfuzz`: Fast fuzzy string matching
- `pyyaml`: YAML configuration parsing
- `python-dotenv`: Environment variable loading
- `requests`: HTTP requests for TVmaze API

## Caching

Metadata is cached in `metadata_cache.json` using composite keys:
- Movies: `movie_{cleaned_title}_{year}`
- TV Shows: `tv_{cleaned_show_name}`

Cache stores confident matches to avoid repeated API calls.