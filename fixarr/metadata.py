import os
import json
import tmdbsimple as tmdb
from imdb import Cinemagoer
from utils import clean_name, extract_year, logger

# You should set your TMDB API key here or via environment variable
TMDB_API_KEY = os.getenv('TMDB_API_KEY', 'YOUR_API_KEY_HERE')
tmdb.API_KEY = TMDB_API_KEY

class MetadataManager:
    def __init__(self, cache_file='metadata_cache.json'):
        self.cache_file = cache_file
        self.cache = self._load_cache()
        self.ia = Cinemagoer()

    def _load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
        return {}

    def _save_cache(self):
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")

    def get_movie_metadata(self, filename):
        cleaned = clean_name(filename)
        year = extract_year(filename)
        cache_key = f"movie_{cleaned}_{year}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            search = tmdb.Search()
            response = search.movie(query=cleaned, year=year)
            if search.results:
                # Take the best match
                best_match = search.results[0]
                metadata = {
                    'title': best_match['title'],
                    'year': best_match['release_date'][:4] if best_match.get('release_date') else None,
                    'overview': best_match.get('overview'),
                    'poster_path': best_match.get('poster_path'),
                    'id': best_match['id']
                }
                self.cache[cache_key] = metadata
                self._save_cache()
                return metadata
        except Exception as e:
            logger.error(f"TMDB Error for {filename}: {e}")

        # Fallback to IMDb
        try:
            movies = self.ia.search_movie(cleaned)
            if movies:
                movie = movies[0]
                metadata = {
                    'title': movie['title'],
                    'year': movie.get('year'),
                    'id': movie.movieID
                }
                return metadata
        except Exception as e:
            logger.error(f"IMDb Error for {filename}: {e}")

        return None

    def get_tv_metadata(self, filename):
        cleaned = clean_name(filename)
        # Try to remove episode/season info from name for better search
        search_name = re.sub(r'(?i)s\d+e\d+|season\s*\d+|episode\s*\d+', '', cleaned).strip()
        cache_key = f"tv_{search_name}"

        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            search = tmdb.Search()
            response = search.tv(query=search_name)
            if search.results:
                best_match = search.results[0]
                metadata = {
                    'title': best_match['name'],
                    'first_air_date': best_match.get('first_air_date'),
                    'overview': best_match.get('overview'),
                    'poster_path': best_match.get('poster_path'),
                    'id': best_match['id']
                }
                self.cache[cache_key] = metadata
                self._save_cache()
                return metadata
        except Exception as e:
            logger.error(f"TMDB Error for TV {search_name}: {e}")

        return None

import re
