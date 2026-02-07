import os
import shutil
import subprocess
import yaml
from typing import Any, Dict, List, Optional

from config import Config, get_config
from models import MediaCandidate, MediaType, Decision, ScoreBreakdown
from utils import get_logger

logger = get_logger(__name__)


class MediaOrganizer:
    """
    Manages the 'decide' and 'apply' stages of the pipeline.
    """

    def __init__(
        self,
        dst_path: str,
        src_path: Optional[str] = None,
        config: Optional[Config] = None,
        dry_run: bool = True,
    ):
        self.dst_path = os.path.abspath(dst_path)
        self.src_path = src_path
        self.config = config or get_config()
        self.dry_run = dry_run
        
        # Thresholds from config
        t = self.config.thresholds
        self.auto_accept = t.get("auto_accept_threshold", 0.85)
        self.quarantine_threshold = t.get("quarantine_threshold", 0.65)

    def decide(self, candidate: MediaCandidate) -> Decision:
        """
        Decide Stage: Determine what to do with a media candidate based on scores.
        """
        if candidate.media_type == MediaType.MUSIC:
            candidate.decision = Decision.AUTO_ACCEPTED # Music handled by beets
            return candidate.decision

        if not candidate.best_match:
            candidate.decision = Decision.QUARANTINE
            candidate.decision_reason = "No metadata match found"
            return candidate.decision

        score = candidate.confidence_score
        
        # Check for ambiguity (multiple matches above auto-accept)
        confident_matches = [c for c in candidate.candidates if c.score and c.score.overall >= self.auto_accept]
        if len(confident_matches) > 1:
            candidate.decision = Decision.QUARANTINE
            candidate.decision_reason = f"Ambiguous match: {len(confident_matches)} candidates above auto-accept threshold"
            return candidate.decision

        if score >= self.auto_accept:
            candidate.decision = Decision.AUTO_ACCEPTED
            candidate.decision_reason = f"Confidence {score:.2f} >= {self.auto_accept:.2f}"
        elif score >= self.quarantine_threshold:
            candidate.decision = Decision.QUARANTINE # Could be ASK_USER if interactive
            candidate.decision_reason = f"Confidence {score:.2f} below auto-accept but above quarantine threshold"
        else:
            candidate.decision = Decision.QUARANTINE
            candidate.decision_reason = f"Low confidence {score:.2f} < {self.quarantine_threshold:.2f}"

        return candidate.decision

    def apply(self, candidate: MediaCandidate) -> bool:
        """
        Apply Stage: Execute the decision for a media candidate.
        """
        if candidate.decision == Decision.AUTO_ACCEPTED:
            if candidate.media_type == MediaType.MUSIC:
                return self._apply_music(candidate)
            else:
                return self._apply_organized(candidate)
        elif candidate.decision == Decision.QUARANTINE:
            return self._apply_quarantine(candidate)
        elif candidate.decision == Decision.IGNORE:
            logger.info(f"Apply Stage: Ignoring {candidate.name}")
            return True
        
        return False

    def _apply_organized(self, candidate: MediaCandidate) -> bool:
        meta = candidate.best_match
        if not meta: return False

        # Build destination path
        title = meta.title
        year = meta.year
        
        file_meta = candidate.file_metadata or {}
        codec = file_meta.get("video_codec", "")
        audio_langs = self._format_languages(file_meta.get("audio_languages", []))
        sub_langs = self._format_languages(file_meta.get("subtitle_languages", []))
        resolution = file_meta.get("resolution", "")

        media_folder = "Movies" if candidate.media_type == MediaType.MOVIE else "TV Shows"
        
        if candidate.media_type == MediaType.MOVIE:
            folder_name = self.config.format_name(
                "movie_folder", title=title, year=year or "Unknown",
                tmdb_id=meta.id if meta.source == "tmdb" else "",
                imdb_id=meta.id if meta.source == "imdb" else "",
                codec=codec, audio_langs=audio_langs, sub_langs=sub_langs, resolution=resolution
            )
            dst_dir = os.path.join(self.dst_path, media_folder, folder_name)
            
            ext = os.path.splitext(candidate.original_path)[1]
            file_name = self.config.format_name(
                "movie_file", title=title, year=year or "Unknown",
                codec=codec, audio_langs=audio_langs, sub_langs=sub_langs, resolution=resolution
            )
            dst_path = os.path.join(dst_dir, f"{file_name}{ext}")
            
            self._move_file(candidate.original_path, dst_path, dst_dir)
            self._move_subtitles(candidate, dst_dir, file_name)
            self._create_nfo(dst_dir, meta, candidate.media_type)
            
        elif candidate.media_type == MediaType.TV_SHOW:
            # For TV, we need to handle season folder
            from name_cleaner import extract_tv_info
            _, season, episode = extract_tv_info(candidate.name)
            season = season or 1
            episode = episode or 1

            show_folder = self.config.format_name(
                "tv_show_folder", title=title, year=year or "",
                tmdb_id=meta.id if meta.source == "tmdb" else "",
                tvmaze_id=meta.id if meta.source == "tvmaze" else ""
            )
            season_folder = self.config.format_name("tv_season_folder", season=season)
            dst_dir = os.path.join(self.dst_path, media_folder, show_folder, season_folder)
            
            ext = os.path.splitext(candidate.original_path)[1]
            file_name = self.config.format_name(
                "tv_file", title=title, season=season, episode=episode,
                codec=codec, audio_langs=audio_langs, sub_langs=sub_langs, resolution=resolution
            )
            dst_path = os.path.join(dst_dir, f"{file_name}{ext}")

            self._move_file(candidate.original_path, dst_path, dst_dir)
            self._move_subtitles(candidate, dst_dir, file_name)
            
            # Show NFO
            show_dir = os.path.join(self.dst_path, media_folder, show_folder)
            self._create_nfo(show_dir, meta, candidate.media_type)

        candidate.destination_path = dst_path
        return True

    def _apply_quarantine(self, candidate: MediaCandidate) -> bool:
        review_base = os.path.join(self.dst_path, self.config.paths.get("review_needed", "review_needed"))
        dst_path = os.path.join(review_base, candidate.relative_path)
        dst_dir = os.path.dirname(dst_path)

        logger.warning(f"Apply Stage: Quarantining {candidate.name} to {dst_path} (Reason: {candidate.decision_reason})")
        
        self._move_file(candidate.original_path, dst_path, dst_dir)
        
        # Move subtitles
        for sub in candidate.subtitles:
            sub_rel = os.path.relpath(sub, candidate.original_path) if os.path.isdir(candidate.original_path) else os.path.basename(sub)
            if not os.path.isabs(sub_rel):
                sub_dst = os.path.join(dst_dir, sub_rel)
            else:
                sub_dst = os.path.join(dst_dir, os.path.basename(sub))
            self._move_file(sub, sub_dst, os.path.dirname(sub_dst))

        # Create metadata.yaml in the parent folder of the quarantined item or next to it
        meta_file = os.path.join(dst_dir, f"{os.path.basename(dst_path)}.metadata.yaml")
        if not self.dry_run:
            try:
                meta_data = {
                    "name": candidate.name,
                    "reason": candidate.decision_reason,
                    "confidence": candidate.confidence_score,
                    "parsed_title": candidate.parsed_title,
                    "parsed_year": candidate.parsed_year,
                    "best_match": {
                        "title": candidate.best_match.title,
                        "year": candidate.best_match.year,
                        "source": candidate.best_match.source,
                        "id": candidate.best_match.id
                    } if candidate.best_match else None,
                    "alternatives": [
                        {"title": c.title, "year": c.year, "score": c.score.overall if c.score else 0}
                        for c in candidate.candidates[:3]
                    ]
                }
                with open(meta_file, "w", encoding="utf-8") as f:
                    yaml.dump(meta_data, f, sort_keys=False)
            except Exception as e:
                logger.error(f"Error creating quarantine metadata: {e}")

        candidate.destination_path = dst_path
        return True

    def _apply_music(self, candidate: MediaCandidate) -> bool:
        if not self.config.behavior.get("use_beets_for_music", True):
            return True
            
        src_path = candidate.original_path
        music_dst = os.path.join(self.dst_path, self.config.paths.get("music_folder", "Music"))
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would import music via beets: {src_path}")
            return True

        try:
            os.makedirs(music_dst, exist_ok=True)
            # Remove -C (nocopy) and add -m (move) to ensure organization happens.
            # Beets will move files to the library according to its own config.
            cmd = ["beet", "import", "-q", "-m", src_path]
            subprocess.run(cmd, check=True)
            candidate.destination_path = music_dst
            return True
        except Exception as e:
            logger.error(f"Beets failed: {e}")
            return False

    def _move_file(self, src: str, dst: str, dst_dir: str) -> bool:
        if self.dry_run:
            logger.info(f"[DRY RUN] Would move: {src} -> {dst}")
            return True
        try:
            os.makedirs(dst_dir, exist_ok=True)
            if os.path.exists(dst): return False
            shutil.move(src, dst)
            return True
        except Exception as e:
            logger.error(f"Error moving {src}: {e}")
            return False

    def _move_subtitles(self, candidate: MediaCandidate, dst_dir: str, base_name: str) -> None:
        for sub_path in candidate.subtitles:
            ext = os.path.splitext(sub_path)[1]
            dst_path = os.path.join(dst_dir, f"{base_name}{ext}")
            self._move_file(sub_path, dst_path, dst_dir)

    def _create_nfo(self, directory: str, meta: any, media_type: MediaType) -> None:
        if self.dry_run: return
        nfo_name = "movie.nfo" if media_type == MediaType.MOVIE else "tvshow.nfo"
        nfo_path = os.path.join(directory, nfo_name)
        root_tag = "movie" if media_type == MediaType.MOVIE else "tvshow"
        content = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<{root_tag}>
    <title>{meta.title}</title>
    <year>{meta.year or ''}</year>
    <plot>{meta.overview or ''}</plot>
    <tmdbid>{meta.id if meta.source == 'tmdb' else ''}</tmdbid>
</{root_tag}>"""
        try:
            os.makedirs(directory, exist_ok=True)
            with open(nfo_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception: pass

    def _format_languages(self, langs: List[str]) -> str:
        return ",".join(sorted(set(l.upper() for l in langs if l)))

