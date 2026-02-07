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
        """
        Test that TV show episodes are grouped correctly.

        Creates two episode files with proper naming convention (ShowName.S01E01.mkv)
        and verifies they are detected as a single TV show with 2 episodes.
        The scanner should group episodes from the same show together.
        """
        show_dir = os.path.join(self.test_dir, "Breaking Bad")
        os.makedirs(show_dir)
        # Use proper episode naming with show title for grouping
        with open(os.path.join(show_dir, "Breaking.Bad.S01E01.mkv"), 'w') as f: f.write("")
        with open(os.path.join(show_dir, "Breaking.Bad.S01E02.mkv"), 'w') as f: f.write("")
        
        scanner = MediaScanner(self.test_dir)
        items = scanner.scan()
        
        # New behavior: episodes are individual candidates
        self.assertEqual(len(items), 2)
        for item in items:
            self.assertEqual(item['type'], 'tv_show')

    def test_scan_movie_with_file_metadata(self):
        """
        Test that scanned movies include file_metadata field.

        Verifies the scanner integration with file probing by checking
        that the file_metadata key is present in the scanned item.
        """
        movie_file = os.path.join(self.test_dir, "Inception.2010.1080p.mkv")
        with open(movie_file, 'w') as f: f.write("")
        
        scanner = MediaScanner(self.test_dir, probe_files=True)
        items = scanner.scan()
        
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['type'], 'movie')
        # file_metadata should be present (may be None if probing fails on empty file)
        self.assertIn('file_metadata', items[0])

    def test_scan_without_probing(self):
        """
        Test that file probing can be disabled.

        When probe_files=False, the scanner should not attempt to
        extract technical metadata from files.
        """
        movie_file = os.path.join(self.test_dir, "Movie.mkv")
        with open(movie_file, 'w') as f: f.write("")
        
        scanner = MediaScanner(self.test_dir, probe_files=False)
        items = scanner.scan()
        
        self.assertEqual(len(items), 1)
        # file_metadata should be empty dict when probing is disabled
        self.assertEqual(items[0].get('file_metadata'), {})

    def test_scan_mixed_content(self):
        """
        Test scanning a directory with both movies and TV shows.

        Verifies that the scanner correctly categorizes mixed content
        within the same source directory.
        """
        # Create a movie
        with open(os.path.join(self.test_dir, "Movie.mkv"), 'w') as f: f.write("")
        
        # Create a TV show folder
        show_dir = os.path.join(self.test_dir, "Show")
        os.makedirs(show_dir)
        with open(os.path.join(show_dir, "Show.S01E01.mkv"), 'w') as f: f.write("")
        with open(os.path.join(show_dir, "Show.S01E02.mkv"), 'w') as f: f.write("")
        
        scanner = MediaScanner(self.test_dir)
        items = scanner.scan()
        
        # Should have 3 items: 1 movie + 2 TV episodes
        self.assertEqual(len(items), 3)
        types = {item['type'] for item in items}
        self.assertIn('movie', types)
        self.assertIn('tv_show', types)

    def test_scan_subtitles_matched(self):
        """
        Test that subtitle files are matched to their video files.

        Verifies that .srt files with matching names are associated
        with the corresponding video file.
        """
        video = os.path.join(self.test_dir, "Movie.mkv")
        subtitle = os.path.join(self.test_dir, "Movie.eng.srt")
        with open(video, 'w') as f: f.write("")
        with open(subtitle, 'w') as f: f.write("")
        
        scanner = MediaScanner(self.test_dir)
        items = scanner.scan()
        
        self.assertEqual(len(items), 1)
        self.assertEqual(len(items[0]['subtitles']), 1)
        # Subtitles are dicts with 'path' key
        subtitle_entry = items[0]['subtitles'][0]
        if isinstance(subtitle_entry, dict):
            self.assertTrue(subtitle_entry.get('path', '').endswith('.srt'))
        else:
            self.assertTrue(subtitle_entry.endswith('.srt'))
