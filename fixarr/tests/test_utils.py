"""
Unit tests for utility functions in utils.py.

Tests file type detection, year extraction, TV info parsing,
and subtitle language detection.
"""

import unittest
from utils import (
    is_video,
    is_audio,
    is_subtitle,
    extract_year,
    extract_tv_info,
    detect_subtitle_language,
    find_matching_subtitles,
    clean_name,
)


class TestFileTypeDetection(unittest.TestCase):
    """
    Tests for file type detection functions.

    Verifies correct identification of video, audio, and subtitle files.
    """

    def test_is_video(self):
        """Test video file detection."""
        self.assertTrue(is_video("movie.mkv"))
        self.assertTrue(is_video("movie.mp4"))
        self.assertTrue(is_video("movie.avi"))
        self.assertTrue(is_video("movie.m4v"))
        self.assertFalse(is_video("music.mp3"))
        self.assertFalse(is_video("subs.srt"))

    def test_is_audio(self):
        """Test audio file detection."""
        self.assertTrue(is_audio("song.mp3"))
        self.assertTrue(is_audio("song.flac"))
        self.assertTrue(is_audio("song.wav"))
        self.assertTrue(is_audio("song.m4a"))
        self.assertFalse(is_audio("movie.mkv"))
        self.assertFalse(is_audio("subs.srt"))

    def test_is_subtitle(self):
        """Test subtitle file detection."""
        self.assertTrue(is_subtitle("movie.srt"))
        self.assertTrue(is_subtitle("movie.vtt"))
        self.assertTrue(is_subtitle("movie.ass"))
        self.assertTrue(is_subtitle("movie.sub"))
        self.assertFalse(is_subtitle("movie.mkv"))
        self.assertFalse(is_subtitle("song.mp3"))


class TestExtractYear(unittest.TestCase):
    """
    Tests for the extract_year function.

    Verifies correct extraction of years from various string formats.
    """

    def test_extract_year_basic(self):
        """Test year extraction from basic filename."""
        self.assertEqual(extract_year("Movie.2023.1080p"), "2023")

    def test_extract_year_in_parentheses(self):
        """Test year extraction from parentheses format."""
        self.assertEqual(extract_year("Movie (2020)"), "2020")

    def test_extract_year_multiple(self):
        """Test that the correct year is extracted when multiple present."""
        result = extract_year("2001 A Space Odyssey 1968")
        self.assertIn(result, ["2001", "1968"])

    def test_no_year(self):
        """Test result when no year is present."""
        self.assertIsNone(extract_year("NoYearHere"))

    def test_invalid_year(self):
        """Test that invalid years are not extracted."""
        self.assertIsNone(extract_year("Movie.123"))


class TestExtractTvInfo(unittest.TestCase):
    """
    Tests for the extract_tv_info function.

    Verifies correct extraction of season and episode from TV filenames.
    """

    def test_standard_format(self):
        """Test S01E01 format."""
        season, episode = extract_tv_info("Show.S01E05.mkv")
        self.assertEqual(season, 1)
        self.assertEqual(episode, 5)

    def test_lowercase(self):
        """Test lowercase s01e05 format."""
        season, episode = extract_tv_info("show.s02e10.mkv")
        self.assertEqual(season, 2)
        self.assertEqual(episode, 10)

    def test_x_format(self):
        """Test 1x01 format."""
        season, episode = extract_tv_info("Show.2x10.mkv")
        self.assertEqual(season, 2)
        self.assertEqual(episode, 10)

    def test_no_match(self):
        """Test filename without TV patterns."""
        season, episode = extract_tv_info("Movie.mkv")
        self.assertIsNone(season)
        self.assertIsNone(episode)


class TestDetectSubtitleLanguage(unittest.TestCase):
    """
    Tests for subtitle language detection.

    Verifies correct detection of language from subtitle filenames.
    """

    def test_two_letter_code(self):
        """Test two-letter language code detection."""
        self.assertEqual(detect_subtitle_language("movie.en.srt"), "English")
        self.assertEqual(detect_subtitle_language("movie.es.srt"), "Spanish")
        self.assertEqual(detect_subtitle_language("movie.fr.srt"), "French")

    def test_three_letter_code(self):
        """Test three-letter language code detection."""
        self.assertEqual(detect_subtitle_language("movie.eng.srt"), "English")
        self.assertEqual(detect_subtitle_language("movie.spa.srt"), "Spanish")
        self.assertEqual(detect_subtitle_language("movie.jpn.srt"), "Japanese")

    def test_full_language_name(self):
        """Test full language name detection."""
        self.assertEqual(detect_subtitle_language("movie.english.srt"), "English")
        self.assertEqual(detect_subtitle_language("movie.spanish.srt"), "Spanish")

    def test_underscore_separator(self):
        """Test underscore as separator."""
        self.assertEqual(detect_subtitle_language("movie_eng.srt"), "English")

    def test_no_language(self):
        """Test filename without language info."""
        self.assertIsNone(detect_subtitle_language("movie.srt"))


class TestFindMatchingSubtitles(unittest.TestCase):
    """
    Tests for subtitle matching functionality.

    Verifies correct matching of subtitles to video files.
    """

    def test_basic_matching(self):
        """Test basic subtitle matching."""
        video_path = "/movies/The.Matrix.mkv"
        subtitles = [
            "/movies/The.Matrix.en.srt",
            "/movies/The.Matrix.es.srt",
            "/movies/Other.Movie.srt",
        ]

        matches = find_matching_subtitles(video_path, subtitles)
        self.assertEqual(len(matches), 2)

    def test_matching_with_language(self):
        """Test that language is detected for matched subtitles."""
        video_path = "/movies/Movie.mkv"
        subtitles = ["/movies/Movie.en.srt"]

        matches = find_matching_subtitles(video_path, subtitles)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["language"], "English")


class TestCleanNameLegacy(unittest.TestCase):
    """
    Tests for the legacy clean_name function.

    Ensures backward compatibility with the original function.
    """

    def test_basic_cleaning(self):
        """Test basic filename cleaning."""
        result = clean_name("The.Movie.2023.1080p.BluRay.x264.mkv")
        self.assertIn("Movie", result)
        self.assertIn("2023", result)

    def test_tag_removal(self):
        """Test removal of group tags."""
        result = clean_name("[Group] Show.S01E01.720p.mkv")
        self.assertIn("Show", result)


if __name__ == "__main__":
    unittest.main()
