import unittest
from utils import clean_name, extract_year, extract_tv_info

class TestUtils(unittest.TestCase):
    """
    Tests for utility functions in utils.py.
    Checks if cleaning names, extracting years and TV info works correctly.
    """
    def test_clean_name(self):
        self.assertEqual(clean_name("The.Movie.2023.1080p.BluRay.x264.mkv"), "The Movie 2023")
        self.assertEqual(clean_name("[Group] Show.S01E01.720p.mkv"), "Show S01E01")

    def test_extract_year(self):
        self.assertEqual(extract_year("Movie.2023.1080p"), "2023")
        self.assertIsNone(extract_year("NoYearHere"))

    def test_extract_tv_info(self):
        self.assertEqual(extract_tv_info("Show.S01E05.mkv"), (1, 5))
        self.assertEqual(extract_tv_info("Show.2x10.mkv"), (2, 10))
        self.assertIsNone(extract_tv_info("Movie.mkv"))
