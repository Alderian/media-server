import os
import shutil
import subprocess
import json
from utils import logger

class MediaOrganizer:
    def __init__(self, dst_path):
        self.dst_path = dst_path
        self.report = []

    def organize_movie(self, item, metadata):
        if not metadata:
            logger.warning(f"No metadata found for movie: {item['path']}")
            return

        title = metadata['title']
        year = metadata.get('year')
        folder_name = f"{title} ({year})" if year else title
        # Sanitize folder name
        folder_name = "".join([c for c in folder_name if c.isalnum() or c in (' ', '.', '_', '(', ')')]).strip()
        
        movie_dir = os.path.join(self.dst_path, "Peliculas", folder_name)
        os.makedirs(movie_dir, exist_ok=True)

        # Move video file
        src_file = item['path']
        ext = os.path.splitext(src_file)[1]
        dst_file = os.path.join(movie_dir, f"{folder_name}{ext}")
        
        logger.info(f"Moving movie: {src_file} -> {dst_file}")
        shutil.move(src_file, dst_file)

        # Move subtitles
        for sub in item.get('subtitles', []):
            sub_ext = os.path.splitext(sub)[1]
            shutil.move(sub, os.path.join(movie_dir, f"{folder_name}{sub_ext}"))

        # Create .nfo
        self._create_movie_nfo(movie_dir, metadata)
        
        self.report.append({'type': 'movie', 'src': src_file, 'dst': dst_file, 'status': 'success'})

    def organize_tv_show(self, item, metadata):
        if not metadata:
            logger.warning(f"No metadata found for TV Show: {item['path']}")
            return

        show_title = metadata['title']
        show_dir = os.path.join(self.dst_path, "Series", show_title)
        os.makedirs(show_dir, exist_ok=True)

        files_to_process = []
        if 'episodes' in item:
            files_to_process = item['episodes']
        else:
            files_to_process = [item['path']]

        for src_file in files_to_process:
            from utils import extract_tv_info
            s, e = extract_tv_info(os.path.basename(src_file))
            if s is None: s = 1 # Default to season 1 if not found
            
            season_dir = os.path.join(show_dir, f"Season {s:02d}")
            os.makedirs(season_dir, exist_ok=True)

            ext = os.path.splitext(src_file)[1]
            filename = f"{show_title} - S{s:02d}E{e:02d}{ext}" if e is not None else os.path.basename(src_file)
            dst_file = os.path.join(season_dir, filename)

            logger.info(f"Moving episode: {src_file} -> {dst_file}")
            shutil.move(src_file, dst_file)

            # Move matching subtitles if any (simplified)
            # In a real scenario, we'd look for subs in the same folder as src_file
            
            self.report.append({'type': 'tv_episode', 'src': src_file, 'dst': dst_file, 'status': 'success'})

        # Create show .nfo (simplified)
        self._create_show_nfo(show_dir, metadata)

    def organize_music(self, item):
        logger.info(f"Organizing music via beets: {item['path']}")
        # Call beets import in non-interactive mode (-p for pretend/don't move yet or -i for interactive)
        # We want non-interactive: -q (quiet) and -A (don't autotag) or just -q
        # Actually 'beet import -q' is non-interactive.
        try:
            # We need to make sure beets is configured to move to the right place.
            # We can override the directory in the command line if needed.
            music_dst = os.path.join(self.dst_path, "Music")
            os.makedirs(music_dst, exist_ok=True)
            
            cmd = ["beet", "import", "-q", "-C", item['path']]
            subprocess.run(cmd, check=True)
            self.report.append({'type': 'music', 'path': item['path'], 'status': 'success'})
        except Exception as e:
            logger.error(f"Beets error: {e}")
            self.report.append({'type': 'music', 'path': item['path'], 'status': 'error', 'message': str(e)})

    def _create_movie_nfo(self, movie_dir, metadata):
        nfo_path = os.path.join(movie_dir, "movie.nfo")
        content = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<movie>
    <title>{metadata['title']}</title>
    <year>{metadata.get('year', '')}</year>
    <plot>{metadata.get('overview', '')}</plot>
    <tmdbid>{metadata.get('id', '')}</tmdbid>
</movie>"""
        with open(nfo_path, 'w') as f:
            f.write(content)

    def _create_show_nfo(self, show_dir, metadata):
        nfo_path = os.path.join(show_dir, "tvshow.nfo")
        content = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<tvshow>
    <title>{metadata['title']}</title>
    <plot>{metadata.get('overview', '')}</plot>
    <tmdbid>{metadata.get('id', '')}</tmdbid>
</tvshow>"""
        with open(nfo_path, 'w') as f:
            f.write(content)

    def save_report(self):
        with open('report.json', 'w') as f:
            json.dump(self.report, f, indent=4)
