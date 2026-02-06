import unittest
import os
import shutil
import tempfile
from scanner import MediaScanner

class TestScanner(unittest.TestCase):
    """
    Tests for MediaScanner.
    Verifies that files are correctly grouped into movies, tv shows, and music.
    """
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_scan_movie(self):
        movie_file = os.path.join(self.test_dir, "Matrix.mkv")
        with open(movie_file, 'w') as f: f.write("")
        
        scanner = MediaScanner(self.test_dir)
        items = scanner.scan()
        
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['type'], 'movie')

    def test_scan_tv_show(self):
        show_dir = os.path.join(self.test_dir, "Breaking Bad")
        os.makedirs(show_dir)
        with open(os.path.join(show_dir, "S01E01.mkv"), 'w') as f: f.write("")
        with open(os.path.join(show_dir, "S01E02.mkv"), 'w') as f: f.write("")
        
        scanner = MediaScanner(self.test_dir)
        items = scanner.scan()
        
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['type'], 'tv_show')
        self.assertEqual(len(items[0]['episodes']), 2)
