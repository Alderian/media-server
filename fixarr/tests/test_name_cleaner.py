"""
Unit tests for the name_cleaner module.

Tests the filename cleaning and normalization functions that extract
clean titles and years from messy media filenames.
"""

import unittest
from name_cleaner import (
    clean_media_filename,
    extract_tv_info,
    is_likely_tv_show,
)


class TestCleanMediaFilename(unittest.TestCase):
    """
    Tests for the clean_media_filename function.

    Verifies that various filename formats are correctly cleaned
    to extract the title and year.
    """

    def test_basic_movie_with_year(self):
        """Test simple movie filename with year in parentheses."""
        title, year = clean_media_filename("The Matrix (1999).mkv")
        self.assertEqual(title, "The Matrix")
        self.assertEqual(year, 1999)

    def test_dots_and_quality(self):
        """Test movie with dots, quality tags and codec."""
        title, year = clean_media_filename("The.Matrix.1999.1080p.BluRay.x264.mkv")
        self.assertEqual(title, "The Matrix")
        self.assertEqual(year, 1999)

    def test_release_group(self):
        """Test removal of release group tags."""
        title, year = clean_media_filename("Inception.2010.1080p.BluRay-YIFY.mkv")
        self.assertEqual(title, "Inception")
        self.assertEqual(year, 2010)

    def test_brackets_and_tags(self):
        """Test removal of bracketed content and tags."""
        title, year = clean_media_filename("[YTS.MX] Dune 2021 1080p.BluRay.x265.mkv")
        self.assertEqual(title, "Dune")
        self.assertEqual(year, 2021)

    def test_hdr_and_audio_tags(self):
        """Test removal of HDR and audio codec tags."""
        title, year = clean_media_filename("Oppenheimer.2023.2160p.UHD.BluRay.HDR.DTS-HD.mkv")
        self.assertEqual(title, "Oppenheimer")
        self.assertEqual(year, 2023)

    def test_no_year(self):
        """Test filename without a year."""
        title, year = clean_media_filename("Unknown Movie.1080p.mkv")
        self.assertEqual(title, "Unknown Movie")
        self.assertIsNone(year)

    def test_title_with_number(self):
        """Test that numbers in titles aren't mistaken for years."""
        title, year = clean_media_filename("2001 A Space Odyssey (1968).mkv")
        self.assertIn("Space Odyssey", title)
        self.assertEqual(year, 1968)

    def test_title_casing(self):
        """Test proper title casing of results."""
        title, year = clean_media_filename("the.DARK.knight.2008.mkv")
        self.assertEqual(title, "The Dark Knight")
        self.assertEqual(year, 2008)

    def test_extended_editions(self):
        """Test handling of extended edition tags."""
        title, year = clean_media_filename("Lord.of.the.Rings.2001.Extended.Edition.mkv")
        self.assertEqual(title, "Lord of the Rings")
        self.assertEqual(year, 2001)


class TestExtractTvInfo(unittest.TestCase):
    """
    Tests for the extract_tv_info function.

    Verifies extraction of show title, season, and episode from
    various TV show filename formats.
    """

    def test_standard_sxxexx_format(self):
        """Test standard S01E01 format."""
        title, season, episode = extract_tv_info("Breaking.Bad.S01E05.720p.mkv")
        self.assertEqual(title, "Breaking Bad")
        self.assertEqual(season, 1)
        self.assertEqual(episode, 5)

    def test_lowercase_sxxexx(self):
        """Test lowercase s01e05 format."""
        title, season, episode = extract_tv_info("the.office.s02e10.hdtv.mkv")
        self.assertEqual(title, "The Office")
        self.assertEqual(season, 2)
        self.assertEqual(episode, 10)

    def test_xxxx_format(self):
        """Test 1x01 format."""
        title, season, episode = extract_tv_info("Friends.1x01.The.Pilot.mkv")
        self.assertEqual(title, "Friends")
        self.assertEqual(season, 1)
        self.assertEqual(episode, 1)

    def test_season_episode_words(self):
        """Test 'Season X Episode Y' format."""
        title, season, episode = extract_tv_info("Game of Thrones Season 3 Episode 9.mkv")
        self.assertEqual(title, "Game of Thrones")
        self.assertEqual(season, 3)
        self.assertEqual(episode, 9)

    def test_no_tv_pattern(self):
        """Test filename without TV patterns."""
        title, season, episode = extract_tv_info("The Matrix 1999.mkv")
        self.assertIsNone(title)
        self.assertIsNone(season)
        self.assertIsNone(episode)

    def test_three_digit_episode(self):
        """Test handling of three-digit episode numbers."""
        title, season, episode = extract_tv_info("Naruto.S01E220.mkv")
        self.assertEqual(title, "Naruto")
        self.assertEqual(season, 1)
        self.assertEqual(episode, 220)


class TestIsLikelyTvShow(unittest.TestCase):
    """
    Tests for the is_likely_tv_show function.

    Verifies correct identification of TV show filenames.
    """

    def test_tv_show_detection(self):
        """Test that TV patterns are detected."""
        self.assertTrue(is_likely_tv_show("Breaking.Bad.S01E01.mkv"))
        self.assertTrue(is_likely_tv_show("Show.1x05.mkv"))

    def test_movie_not_detected(self):
        """Test that movies are not detected as TV shows."""
        self.assertFalse(is_likely_tv_show("The.Matrix.1999.mkv"))
        self.assertFalse(is_likely_tv_show("Inception.2010.1080p.mkv"))


if __name__ == "__main__":
    unittest.main()
