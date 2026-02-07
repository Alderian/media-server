"""
Metadata fetching and caching for media files.
"""

import os
import json
import re
import requests
from typing import Dict, List, Optional, Any, Tuple

import tmdbsimple as tmdb
from imdb import Cinemagoer

from name_cleaner import clean_media_filename, get_spanish_to_english_hint
from scoring import ConfidenceScorer
from config import get_config
from utils import get_logger
from models import MediaCandidate, MetadataCandidate, MediaType, ScoreBreakdown

logger = get_logger(__name__)


class MetadataManager:
    """
    Manages the 'identify' stage of the pipeline.
    Fetches potential metadata candidates from multiple APIs.
    """

    def __init__(
        self,
        cache_file: str = "metadata_cache.json",
        config_path: Optional[str] = None,
    ):
        self.cache_file = cache_file
        self.cache = self._load_cache()

        config = get_config(config_path)

        # Set up TMDb API
        api_key = config.api.get("tmdb_api_key") or os.getenv("TMDB_API_KEY", "")
        if api_key:
            tmdb.API_KEY = api_key
        self.tmdb_enabled = bool(api_key)

        # Set up IMDb fallback
        self.imdb_fallback = config.api.get("imdb_fallback", True)
        self._ia = None

        # Set up TVmaze
        self.tvmaze_enabled = config.api.get("tvmaze_enabled", True)
        self.tvmaze_base = "https://api.tvmaze.com"

        logger.debug("MetadataManager initialized")

    @property
    def ia(self):
        if self._ia is None and self.imdb_fallback:
            self._ia = Cinemagoer()
        return self._ia

    def _load_cache(self) -> Dict[str, Any]:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_cache(self) -> None:
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def identify(self, candidate: MediaCandidate) -> List[MetadataCandidate]:
        """
        Identify Stage: Fetch potential matches for a media candidate.
        """
        if candidate.media_type == MediaType.MUSIC:
            return [] # Music handled by beets in 'apply' stage (legacy)

        search_title = candidate.parsed_title or candidate.name
        search_year = candidate.parsed_year
        
        # Spanish to English translation hint
        translation_hint = get_spanish_to_english_hint(search_title)
        
        logger.debug(f"Identify Stage: Searching for '{search_title}' (Year: {search_year})")
        if translation_hint:
            logger.debug(f"  Translation hint: '{translation_hint}'")

        results: List[MetadataCandidate] = []

        if candidate.media_type == MediaType.MOVIE:
            results.extend(self._search_movies(search_title, search_year))
            if translation_hint:
                results.extend(self._search_movies(translation_hint, search_year))
        
        elif candidate.media_type == MediaType.TV_SHOW:
            results.extend(self._search_tv(search_title))
            if translation_hint:
                results.extend(self._search_tv(translation_hint))

        # Deduplicate results by ID
        seen_ids = set()
        unique_results = []
        for r in results:
            key = (r.source, r.id)
            if key not in seen_ids:
                seen_ids.add(key)
                unique_results.append(r)

        candidate.candidates = unique_results
        return unique_results

    def _search_movies(self, title: str, year: Optional[int]) -> List[MetadataCandidate]:
        results = []
        
        # TMDb
        if self.tmdb_enabled:
            try:
                search = tmdb.Search()
                search.movie(query=title, year=year)
                for item in search.results[:5]:
                    results.append(MetadataCandidate(
                        source="tmdb",
                        id=str(item["id"]),
                        title=item["title"],
                        year=int(item["release_date"][:4]) if item.get("release_date") else None,
                        overview=item.get("overview"),
                        raw_data=item
                    ))
            except Exception as e:
                logger.error(f"TMDb error: {e}")

        # IMDb Fallback
        if self.imdb_fallback and not results:
            try:
                movies = self.ia.search_movie(title)
                for movie in movies[:5]:
                    results.append(MetadataCandidate(
                        source="imdb",
                        id=movie.movieID,
                        title=movie["title"],
                        year=movie.get("year"),
                        raw_data=dict(movie)
                    ))
            except Exception as e:
                logger.error(f"IMDb error: {e}")
                
        return results

    def _search_tv(self, title: str) -> List[MetadataCandidate]:
        results = []
        
        # TMDb TV
        if self.tmdb_enabled:
            try:
                search = tmdb.Search()
                search.tv(query=title)
                for item in search.results[:5]:
                    results.append(MetadataCandidate(
                        source="tmdb",
                        id=str(item["id"]),
                        title=item["name"],
                        year=int(item["first_air_date"][:4]) if item.get("first_air_date") else None,
                        overview=item.get("overview"),
                        raw_data=item
                    ))
            except Exception as e:
                logger.error(f"TMDb TV error: {e}")

        # TVmaze
        if self.tvmaze_enabled:
            try:
                response = requests.get(f"{self.tvmaze_base}/search/shows", params={"q": title}, timeout=10)
                if response.status_code == 200:
                    for item in response.json()[:5]:
                        show = item["show"]
                        results.append(MetadataCandidate(
                            source="tvmaze",
                            id=str(show["id"]),
                            title=show["name"],
                            year=int(show["premiered"][:4]) if show.get("premiered") else None,
                            overview=show.get("summary"),
                            raw_data=show
                        ))
            except Exception as e:
                logger.error(f"TVmaze error: {e}")

        return results

    def get_movie_metadata(self, filename: str) -> Tuple[Optional[Dict[str, Any]], Optional[ScoreBreakdown], List[Dict[str, Any]]]:
        # Legacy compatibility - minimal implementation
        candidate = MediaCandidate(original_path=filename, relative_path=filename, name=filename, media_type=MediaType.MOVIE)
        self.identify(candidate)
        if candidate.candidates:
            # Return raw_data for legacy compatibility
            return candidate.candidates[0].raw_data, None, [c.raw_data for c in candidate.candidates]
        return None, None, []

    def get_tv_metadata(self, filename: str, show_name: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[ScoreBreakdown], List[Dict[str, Any]]]:
        # Legacy compatibility
        candidate = MediaCandidate(original_path=filename, relative_path=filename, name=filename, media_type=MediaType.TV_SHOW, parsed_title=show_name)
        self.identify(candidate)
        if candidate.candidates:
            return candidate.candidates[0].raw_data, None, [c.raw_data for c in candidate.candidates]
        return None, None, []
