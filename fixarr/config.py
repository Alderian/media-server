"""
Configuration management for Fixarr.

Loads configuration from YAML files and environment variables,
providing sensible defaults for all settings.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Default configuration values
DEFAULT_CONFIG = {
    "naming": {
        # Movies: {title}, {year}, {imdb_id}, {tmdb_id}
        #         {codec}, {audio_langs}, {sub_langs}, {resolution}
        "movie_folder": "{title} ({year})",
        "movie_file": "{title} ({year})",
        # TV Shows: {title}, {year}, {imdb_id}, {tmdb_id}, {season}, {episode}, {episode_title}
        #           {codec}, {audio_langs}, {sub_langs}, {resolution}
        "tv_show_folder": "{title}",
        "tv_season_folder": "Season {season:02d}",
        "tv_file": "{title} - S{season:02d}E{episode:02d}",
        # Music: {artist}, {album}, {year}, {track_number}, {track_title}
        "music_artist_folder": "{artist}",
        "music_album_folder": "{album} ({year})",
        "music_track_file": "{track_number:02d} - {track_title}",
    },
    "thresholds": {
        "min_confidence": 0.7,
        "fuzzy_match_threshold": 0.8,
        "year_tolerance": 1,
    },
    "paths": {
        "default_src": None,
        "default_dst": None,
        "review_needed": "review_needed",
        "movies_folder": "Movies",
        "tv_folder": "TV Shows",
        "music_folder": "Music",
    },
    "api": {
        "tmdb_api_key": os.getenv("TMDB_API_KEY", ""),
        "tvmaze_enabled": True,
        "imdb_fallback": True,
    },
    "behavior": {
        "use_beets_for_music": True,
        "create_nfo_files": True,
        "move_subtitles": True,
        "verbose": False,
    },
}


class Config:
    """Configuration manager for Fixarr."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_path: Optional path to YAML config file. If None,
                        looks for config.yaml in the current directory.
        """
        self._config = self._deep_copy(DEFAULT_CONFIG)
        self._config_path = config_path

        # Try to load config file
        if config_path and os.path.exists(config_path):
            self._load_yaml(config_path)
        elif os.path.exists("config.yaml"):
            self._load_yaml("config.yaml")

        # Override with environment variables
        self._load_env_overrides()

    def _deep_copy(self, d: Dict) -> Dict:
        """Create a deep copy of a dictionary."""
        result = {}
        for key, value in d.items():
            if isinstance(value, dict):
                result[key] = self._deep_copy(value)
            else:
                result[key] = value
        return result

    def _load_yaml(self, path: str) -> None:
        """Load configuration from YAML file."""
        try:
            with open(path, "r") as f:
                user_config = yaml.safe_load(f) or {}
            self._merge_config(self._config, user_config)
        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing config file {path}: {e}")

    def _merge_config(self, base: Dict, override: Dict) -> None:
        """Recursively merge override config into base config."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def _load_env_overrides(self) -> None:
        """Load configuration overrides from environment variables."""
        # API key from environment
        if os.getenv("TMDB_API_KEY"):
            self._config["api"]["tmdb_api_key"] = os.getenv("TMDB_API_KEY")

        # Default paths from environment
        if os.getenv("FIXARR_SRC"):
            self._config["paths"]["default_src"] = os.getenv("FIXARR_SRC")
        if os.getenv("FIXARR_DST"):
            self._config["paths"]["default_dst"] = os.getenv("FIXARR_DST")

    def get(self, *keys: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            *keys: Keys to traverse (e.g., "naming", "movie_folder")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        current = self._config
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    @property
    def naming(self) -> Dict[str, str]:
        """Get naming templates configuration."""
        return self._config["naming"]

    @property
    def thresholds(self) -> Dict[str, float]:
        """Get threshold configuration."""
        return self._config["thresholds"]

    @property
    def paths(self) -> Dict[str, Optional[str]]:
        """Get paths configuration."""
        return self._config["paths"]

    @property
    def api(self) -> Dict[str, Any]:
        """Get API configuration."""
        return self._config["api"]

    @property
    def behavior(self) -> Dict[str, bool]:
        """Get behavior configuration."""
        return self._config["behavior"]

    def format_name(self, template_key: str, **kwargs) -> str:
        """
        Format a name using a template from configuration.

        Supports optional placeholders using bracket notation:
        - {title} - Required placeholder
        - [imdbid-{imdb_id}] - Optional section, removed if imdb_id is missing
        - {season:02d} - Placeholder with format specifier

        Args:
            template_key: Key in naming config (e.g., "movie_folder")
            **kwargs: Values to substitute in template

        Returns:
            Formatted string with safe filename characters
        """
        import re

        template = self.naming.get(template_key, "{title}")

        # First, handle optional sections in brackets [...]
        # These sections are removed entirely if any placeholder inside is missing
        def replace_optional(match):
            section = match.group(1)
            # Find all placeholders in this section
            placeholders = re.findall(r"\{(\w+)(?::[^}]*)?\}", section)
            # Check if all placeholders have values
            for ph in placeholders:
                if ph not in kwargs or kwargs[ph] is None or kwargs[ph] == "":
                    return ""  # Remove entire section
            # All placeholders have values, process the section
            try:
                return section.format(**kwargs)
            except (KeyError, ValueError):
                return ""

        # Process optional sections first
        template = re.sub(r"\[([^\]]+)\]", replace_optional, template)

        # Now handle regular placeholders, providing empty string for missing ones
        def replace_placeholder(match):
            full_match = match.group(0)
            key = match.group(1)
            format_spec = match.group(2) or ""

            if key not in kwargs or kwargs[key] is None:
                return ""

            value = kwargs[key]
            try:
                if format_spec:
                    return f"{{0{format_spec}}}".format(value)
                return str(value)
            except (ValueError, TypeError):
                return str(value)

        result = re.sub(r"\{(\w+)(:[^}]*)?\}", replace_placeholder, template)

        # Clean up extra spaces and dashes from removed placeholders
        result = re.sub(r"\s+", " ", result)  # Multiple spaces to single
        result = re.sub(r"\s*-\s*-\s*", " - ", result)  # Double dashes
        result = re.sub(r"\(\s*\)", "", result)  # Empty parentheses
        result = re.sub(r"\[\s*\]", "", result)  # Empty brackets
        result = re.sub(r"\s+-\s*$", "", result)  # Trailing dash
        result = re.sub(r"^\s*-\s+", "", result)  # Leading dash

        # Sanitize for filesystem
        return self._sanitize_filename(result.strip())

    def _sanitize_filename(self, name: str) -> str:
        """Remove or replace characters not safe for filenames."""
        # Characters not allowed in filenames on various OSes
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, "")
        # Remove leading/trailing whitespace and dots
        return name.strip(" .")


# Global config instance (lazy-loaded)
_global_config: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """
    Get the global configuration instance.

    Args:
        config_path: Optional path to config file (only used on first call)

    Returns:
        Config instance
    """
    global _global_config
    if _global_config is None:
        _global_config = Config(config_path)
    return _global_config


def reset_config() -> None:
    """Reset global config (mainly for testing)."""
    global _global_config
    _global_config = None
