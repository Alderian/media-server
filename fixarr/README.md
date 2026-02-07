# Fixarr: Media Library Organizer

Fixarr is an automated, non-interactive tool to organize your media library (movies, TV shows, and music) into a clean structure compatible with Jellyfin, Plex, and Kodi.

## Features

- **Automated Scanning**: Recursively scans your source directory
- **Smart Classification**: Detects movies, TV shows, and music automatically
- **Confidence Scoring**: Uses fuzzy matching to evaluate metadata quality
- **Configurable Naming**: YAML-based configuration for folder/file templates
- **Review System**: Low-confidence matches moved to `review_needed/` folder
- **Detailed Reports**: JSON reports with scores and decision reasoning
- **Dry-Run Mode**: Preview changes without moving files
- **Multiple APIs**: TMDb, IMDb, and TVmaze integration
- **Subtitle Handling**: Automatic subtitle association with language detection

## Installation

### Quick Setup

Run the installation script to set up everything automatically:

```bash
cd fixarr
chmod +x install.sh
./install.sh
```

This will:
1. Install system dependencies (Python, beets, exiftool)
2. Create a virtual environment (`organizer_env`)
3. Install all Python dependencies

### Manual Setup

If you prefer manual installation:

```bash
# Install system dependencies (Debian/Ubuntu)
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv beets exiftool

# Create and activate virtual environment
python3 -m venv organizer_env
source organizer_env/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Configuration

1. Set up your TMDb API key:
   ```bash
   export TMDB_API_KEY="your_api_key_here"
   # Or add to .env file:
   echo "TMDB_API_KEY=your_api_key_here" > .env
   ```

2. (Optional) Copy and customize the configuration:
   ```bash
   cp config.yaml.example config.yaml
   # Edit config.yaml with your preferences
   ```

## Usage

**Always activate the virtual environment first:**

```bash
source organizer_env/bin/activate
```

### Basic Usage

```bash
python main.py --src /path/to/unorganized/media --dst /path/to/organized/library
```

### CLI Options

| Option | Description |
|--------|-------------|
| `--src PATH` | Source directory with unorganized media |
| `--dst PATH` | Destination directory for organized media |
| `--config FILE` | Path to YAML configuration file (default: config.yaml) |
| `--dry-run` | Simulate operations without moving files |
| `--report FILE` | Path for output report (default: report.json) |
| `--verbose, -v` | Enable detailed output with scoring info |

### Examples

```bash
# Preview changes without moving files
python main.py --src ~/Downloads/media --dst ~/Library --dry-run --verbose

# Use custom configuration
python main.py --config custom.yaml --src ~/media --dst ~/Library

# Generate report to specific path
python main.py --src ~/media --dst ~/Library --report ~/reports/output.json
```

## Configuration

Edit `config.yaml` to customize behavior:

```yaml
naming:
  movie_folder: "{title} ({year})"
  movie_file: "{title} ({year})"
  tv_show_folder: "{title}"
  tv_season_folder: "Season {season:02d}"
  tv_file: "{title} - S{season:02d}E{episode:02d}"

thresholds:
  min_confidence: 0.7  # Minimum score to accept a match
  fuzzy_match_threshold: 0.8
  year_tolerance: 1

paths:
  review_needed: "review_needed"
  movies_folder: "Movies"
  tv_folder: "TV Shows"
  music_folder: "Music"
```

## Project Structure

```
fixarr/
├── main.py           # CLI entrypoint
├── install.sh        # Installation script
├── config.py         # Configuration management
├── config.yaml       # Default configuration
├── scanner.py        # Media file detection
├── name_cleaner.py   # Filename normalization
├── metadata.py       # API integration (TMDb, IMDb, TVmaze)
├── scoring.py        # Confidence scoring system
├── organizer.py      # File organization logic
├── report.py         # Report generation
├── utils.py          # Common utilities
└── tests/            # Unit tests
```

## Running Tests

```bash
source organizer_env/bin/activate
python -m pytest tests/ -v
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `TMDB_API_KEY` | Your TMDb API key (required) |
| `FIXARR_SRC` | Default source directory |
| `FIXARR_DST` | Default destination directory |

## License

MIT