from typing import Dict, List, Optional, Any
from rapidfuzz import fuzz

from models import MediaCandidate, MetadataCandidate, ScoreBreakdown, Decision
from utils import get_logger

logger = get_logger(__name__)


class ConfidenceScorer:
    """
    Evaluates metadata matches using fuzzy string matching.
    """

    # Default weights for scoring factors
    DEFAULT_WEIGHTS = {
        "title": 0.5,
        "year": 0.3,
        "keywords": 0.2,
    }

    def __init__(
        self,
        min_confidence: float = 0.7,
        auto_accept_threshold: float = 0.85,
        fuzzy_threshold: float = 0.8,
        year_tolerance: int = 1,
        weights: Optional[Dict[str, float]] = None,
    ):
        self.min_confidence = min_confidence
        self.auto_accept_threshold = auto_accept_threshold
        self.fuzzy_threshold = fuzzy_threshold
        self.year_tolerance = year_tolerance
        self.weights = weights or self.DEFAULT_WEIGHTS.copy()

    def score(self, candidate: MediaCandidate) -> None:
        """
        Score Stage: Calculate scores for all metadata candidates.
        Sets candidate.best_match and candidate.confidence_score.
        """
        if not candidate.candidates:
            logger.debug(f"Score Stage: No candidates for {candidate.name}")
            return

        logger.debug(f"Score Stage: Scoring {len(candidate.candidates)} candidates for {candidate.name}")

        for meta_candidate in candidate.candidates:
            meta_candidate.score = self.score_match(
                query_title=candidate.parsed_title or candidate.name,
                query_year=str(candidate.parsed_year) if candidate.parsed_year else None,
                result_title=meta_candidate.title,
                result_year=str(meta_candidate.year) if meta_candidate.year else None,
                result_keywords=None, # Future: extract keywords from raw_data
                file_metadata=candidate.file_metadata
            )

        # Sort candidates by overall score
        candidate.candidates.sort(key=lambda x: x.score.overall if x.score else 0, reverse=True)
        
        # Set best match
        if candidate.candidates:
            best = candidate.candidates[0]
            candidate.best_match = best
            candidate.confidence_score = best.score.overall if best.score else 0.0

    def score_match(
        self,
        query_title: str,
        query_year: Optional[str],
        result_title: str,
        result_year: Optional[str],
        result_keywords: Optional[List[str]] = None,
        file_metadata: Optional[Dict[str, Any]] = None,
    ) -> ScoreBreakdown:
        # Calculate title similarity
        title_score = self._score_title(query_title, result_title)

        # Calculate year match
        year_score = self._score_year(query_year, result_year)

        # Calculate keyword overlap (if keywords provided)
        keyword_score = self._score_keywords(query_title, result_keywords)

        # Apply file metadata hints if available
        if file_metadata:
            year_score = self._apply_metadata_hints(
                year_score, query_year, result_year, file_metadata
            )

        # Calculate weighted overall score
        overall = (
            self.weights["title"] * title_score
            + self.weights["year"] * year_score
            + self.weights["keywords"] * keyword_score
        )

        return ScoreBreakdown(
            title_similarity=title_score,
            year_match=year_score,
            keyword_overlap=keyword_score,
            overall=overall,
        )

    def _score_title(self, query: str, result: str) -> float:
        if not query or not result:
            return 0.0
        q = query.lower().strip()
        r = result.lower().strip()
        scores = [
            fuzz.ratio(q, r) / 100,
            fuzz.partial_ratio(q, r) / 100,
            fuzz.token_sort_ratio(q, r) / 100,
            fuzz.token_set_ratio(q, r) / 100,
        ]
        return max(scores)

    def _score_year(self, query_year: Optional[str], result_year: Optional[str]) -> float:
        if not query_year:
            return 0.5
        if not result_year:
            return 0.3
        try:
            q_year = int(query_year)
            r_year = int(str(result_year)[:4])
            diff = abs(q_year - r_year)
            if diff == 0:
                return 1.0
            elif diff <= self.year_tolerance:
                return 0.8
            elif diff <= 2:
                return 0.5
            else:
                return 0.2
        except (ValueError, TypeError):
            return 0.3

    def _score_keywords(self, query_title: str, keywords: Optional[List[str]]) -> float:
        if not keywords:
            return 0.5
        query_words = set(query_title.lower().split())
        keyword_words = set()
        for kw in keywords:
            keyword_words.update(kw.lower().split())
        overlap = len(query_words & keyword_words)
        if overlap > 0:
            return min(1.0, 0.5 + (overlap * 0.2))
        return 0.5

    def _apply_metadata_hints(
        self,
        base_year_score: float,
        query_year: Optional[str],
        result_year: Optional[str],
        file_metadata: Dict[str, Any],
    ) -> float:
        adjusted_score = base_year_score
        if not query_year and result_year:
            try:
                r_year = int(str(result_year)[:4])
                video_codec = file_metadata.get("video_codec", "")
                if video_codec in ("h265", "av1", "vp9"):
                    if r_year >= 2015:
                        adjusted_score = min(1.0, adjusted_score + 0.1)
                elif video_codec in ("xvid", "divx"):
                    if r_year <= 2010:
                        adjusted_score = min(1.0, adjusted_score + 0.1)
                
                # HDR hint
                if file_metadata.get("hdr"):
                    if r_year >= 2016:
                        adjusted_score = min(1.0, adjusted_score + 0.1)
            except (ValueError, TypeError):
                pass
        return adjusted_score

    def select_best_match(self, results: List[MetadataCandidate]) -> Optional[MetadataCandidate]:
        if not results:
            return None
        # Sort candidates by overall score descending
        sorted_results = sorted(results, key=lambda x: x.score.overall if x.score else 0.0, reverse=True)
        best = sorted_results[0]
        # Only return if it meets min_confidence
        if best.score and best.score.overall >= self.min_confidence:
            return best
        return None

def create_scorer_from_config(config: dict) -> ConfidenceScorer:
    thresholds = config.get("thresholds", {})
    return ConfidenceScorer(
        min_confidence=thresholds.get("min_confidence", 0.7),
        auto_accept_threshold=thresholds.get("auto_accept_threshold", 0.85),
        fuzzy_threshold=thresholds.get("fuzzy_match_threshold", 0.8),
        year_tolerance=thresholds.get("year_tolerance", 1),
    )
