"""
Unit tests for the config module.

Tests configuration loading from YAML files, environment variables,
and default value handling.
"""

import os
import tempfile
import unittest
from unittest.mock import patch

from config import Config, get_config, reset_config


class TestConfig(unittest.TestCase):
    """
    Tests for the Config class.

    Verifies configuration loading, merging, and formatting.
    """

    def setUp(self):
        """Reset global config before each test."""
        reset_config()

    def tearDown(self):
        """Clean up after tests."""
        reset_config()

    def test_default_values(self):
        """Test that default configuration values are loaded."""
        config = Config()

        self.assertEqual(config.thresholds.get("min_confidence"), 0.8)
        self.assertEqual(config.thresholds.get("fuzzy_match_threshold"), 0.8)
        self.assertEqual(config.paths.get("movies_folder"), "movies")
        self.assertEqual(config.paths.get("tv_folder"), "tv")

    def test_naming_defaults(self):
        """Test default naming templates."""
        config = Config()

        self.assertIn("{title}", config.naming.get("movie_folder", ""))
        self.assertIn("{year}", config.naming.get("movie_folder", ""))

    def test_load_yaml_config(self):
        """Test loading configuration from YAML file."""
        yaml_content = """
naming:
  movie_folder: "{title} - {year}"
thresholds:
  min_confidence: 0.8
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            config_path = f.name

        try:
            config = Config(config_path)
            self.assertEqual(config.naming.get("movie_folder"), "{title} - {year}")
            self.assertEqual(config.thresholds.get("min_confidence"), 0.8)
            # Default values should still be preserved for unset keys
            self.assertEqual(config.paths.get("movies_folder"), "Movies")
        finally:
            os.unlink(config_path)

    @patch.dict(os.environ, {"TMDB_API_KEY": "test_api_key_123"})
    def test_env_override(self):
        """Test that environment variables override config values."""
        reset_config()
        config = Config()

        self.assertEqual(config.api.get("tmdb_api_key"), "test_api_key_123")

    @patch.dict(os.environ, {"FIXARR_SRC": "/test/src", "FIXARR_DST": "/test/dst"})
    def test_path_env_override(self):
        """Test path overrides from environment."""
        reset_config()
        config = Config()

        self.assertEqual(config.paths.get("default_src"), "/test/src")
        self.assertEqual(config.paths.get("default_dst"), "/test/dst")

    def test_format_name_movie(self):
        """Test name formatting with movie template."""
        config = Config()

        result = config.format_name(
            "movie_folder",
            title="The Matrix",
            year="1999",
            imdb_id="tt0133093",
        )

        self.assertIn("Matrix", result)
        self.assertIn("1999", result)

    def test_format_name_tv(self):
        """Test name formatting with TV template."""
        config = Config()

        result = config.format_name(
            "tv_season_folder",
            season=1,
        )

        self.assertIn("Season", result)
        self.assertIn("01", result)

    def test_format_name_sanitization(self):
        """Test that unsafe characters are removed from names."""
        config = Config()

        result = config.format_name(
            "movie_folder",
            title="Movie: The \"Best\" One?",
            year="2020",
        )

        # Check that problematic characters are removed
        self.assertNotIn(":", result)
        self.assertNotIn('"', result)
        self.assertNotIn("?", result)

    def test_get_nested_value(self):
        """Test getting nested configuration values."""
        config = Config()

        value = config.get("thresholds", "min_confidence")
        self.assertEqual(value, 0.8)

        missing = config.get("nonexistent", "key", default="default_value")
        self.assertEqual(missing, "default_value")


class TestGetConfig(unittest.TestCase):
    """Tests for the get_config function."""

    def setUp(self):
        """Reset global config before each test."""
        reset_config()

    def tearDown(self):
        """Clean up after tests."""
        reset_config()

    def test_singleton_behavior(self):
        """Test that get_config returns the same instance."""
        config1 = get_config()
        config2 = get_config()

        self.assertIs(config1, config2)

    def test_reset_config(self):
        """Test that reset_config clears the singleton."""
        config1 = get_config()
        reset_config()
        config2 = get_config()

        self.assertIsNot(config1, config2)


if __name__ == "__main__":
    unittest.main()
