import os
from typing import Dict, List, Any, Optional
import sys

from utils import is_video, is_audio, is_subtitle, get_logger, find_matching_subtitles
from name_cleaner import extract_tv_info, is_likely_tv_show, clean_media_filename
from file_probe import get_file_probe
from models import MediaCandidate, MediaType, Decision

logger = get_logger(__name__)


class MediaScanner:
    """
    Scans directories for media files and groups them into MediaCandidate objects.
    """

    def __init__(self, src_path: str, probe_files: bool = True):
        self.src_path = os.path.abspath(os.path.expanduser(src_path))
        self.probe_files = probe_files
        self._file_probe = get_file_probe() if probe_files else None

    def scan_and_group(self) -> List[MediaCandidate]:
        """
        Executes the 'scan' and 'group' stages of the pipeline.
        """
        raw_files = self._scan_stage()
        candidates = self._group_stage(raw_files)
        return candidates

    def _scan_stage(self) -> Dict[str, List[str]]:
        """
        Scan Stage: Identify all media files in the source directory.
        """
        logger.debug(f"Scan Stage: Starting scan of {self.src_path}")
        all_files = {"video": [], "audio": [], "subtitle": []}
        
        for root, dirs, files in os.walk(self.src_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith(".")]

            for f in files:
                file_path = os.path.join(root, f)
                if is_video(f):
                    all_files["video"].append(file_path)
                elif is_audio(f):
                    all_files["audio"].append(file_path)
                elif is_subtitle(f):
                    all_files["subtitle"].append(file_path)

        logger.info(f"Scan Stage: Found {len(all_files['video'])} videos, {len(all_files['audio'])} audio files.")
        return all_files

    def _group_stage(self, raw_files: Dict[str, List[str]]) -> List[MediaCandidate]:
        """
        Group Stage: Categorize files and create MediaCandidate objects.
        """
        candidates: List[MediaCandidate] = []
        handled_files = set()
        
        # 1. Process Audio Files (Music) first to prioritize them
        audio_files = raw_files["audio"]
        if audio_files:
            # Group by folder as "Albums"
            dir_to_audio = {}
            for af in audio_files:
                d = os.path.dirname(af)
                if d not in dir_to_audio:
                    dir_to_audio[d] = []
                dir_to_audio[d].append(af)
            
            for directory, files in dir_to_audio.items():
                candidates.append(self._process_music_group(directory, files))
                # Mark all files in this directory as handled to avoid double processing
                # This includes the audio files themselves and any videos (music videos) in the same folder
                for af in files:
                    handled_files.add(af)
                
                # Absorb videos and subtitles in the same folder as music
                for vf in raw_files["video"]:
                    if os.path.dirname(vf) == directory:
                        handled_files.add(vf)
                for sf in raw_files["subtitle"]:
                    if os.path.dirname(sf) == directory:
                        handled_files.add(sf)

        # 2. Process Video Files (Movies and TV) - only those not handled by music
        video_files = [f for f in raw_files["video"] if f not in handled_files]
        subtitles = [f for f in raw_files["subtitle"] if f not in handled_files]
        
        # We group by directory for TV shows if they contain multiple episodes
        dir_to_videos = {}
        for vf in video_files:
            d = os.path.dirname(vf)
            if d not in dir_to_videos:
                dir_to_videos[d] = []
            dir_to_videos[d].append(vf)

        for directory, files in dir_to_videos.items():
            # Check if this directory is primarily TV capsules
            tv_in_dir = [f for f in files if is_likely_tv_show(os.path.basename(f))]
            
            if len(tv_in_dir) > 0:
                # Group TV shows
                candidates.extend(self._process_tv_group(directory, files, subtitles))
            else:
                # Process as individual movies
                for f in files:
                    candidates.append(self._process_movie_file(f, subtitles))

        logger.info(f"Group Stage: Created {len(candidates)} media candidates.")
        return candidates

    def _process_movie_file(self, file_path: str, all_subtitles: List[str]) -> MediaCandidate:
        filename = os.path.basename(file_path)
        title, year = clean_media_filename(filename)
        matching_subs = find_matching_subtitles(file_path, all_subtitles)
        
        return MediaCandidate(
            original_path=file_path,
            relative_path=os.path.relpath(file_path, self.src_path),
            name=filename,
            media_type=MediaType.MOVIE,
            parsed_title=title,
            parsed_year=year,
            file_metadata=self._probe_file(file_path),
            subtitles=matching_subs,
            decision=Decision.PENDING
        )

    def _process_tv_group(self, directory: str, files: List[str], all_subtitles: List[str]) -> List[MediaCandidate]:
        candidates = []
        for f in files:
            filename = os.path.basename(f)
            title, season, episode = extract_tv_info(filename)
            
            # If title is missing from filename, use folder name
            if not title or title.lower().startswith("s0"):
                title = self._get_folder_title(directory)

            matching_subs = find_matching_subtitles(f, all_subtitles)
            
            candidates.append(MediaCandidate(
                original_path=f,
                relative_path=os.path.relpath(f, self.src_path),
                name=filename,
                media_type=MediaType.TV_SHOW,
                parsed_title=title,
                parsed_year=None, # Usually shows don't have year in ep filename
                file_metadata=self._probe_file(f),
                subtitles=matching_subs,
                decision=Decision.PENDING
            ))
        return candidates

    def _process_music_group(self, directory: str, files: List[str]) -> MediaCandidate:
        return MediaCandidate(
            original_path=directory,
            relative_path=os.path.relpath(directory, self.src_path),
            name=os.path.basename(directory),
            media_type=MediaType.MUSIC,
            decision=Decision.PENDING
        )

    def _get_folder_title(self, directory: str) -> str:
        folder_name = os.path.basename(directory)
        # If it's "Season X", look one level up
        if any(folder_name.lower().startswith(x) for x in ["season", "temporada", "temp", "s0", "s1", "s2"]):
            folder_name = os.path.basename(os.path.dirname(directory))
            
        title, _ = clean_media_filename(folder_name)
        return title

    def _probe_file(self, file_path: str) -> Dict[str, Any]:
        if not self._file_probe:
            return {}
        try:
            metadata = self._file_probe.probe(file_path)
            return metadata.to_dict()
        except Exception:
            return {}

    def scan(self) -> List[Dict[str, Any]]:
        """
        Legacy compatibility method. returns list of dicts.
        """
        candidates = self.scan_and_group()
        return [c.to_dict() for c in candidates]
