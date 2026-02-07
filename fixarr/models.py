"""
Core models for the Fixarr pipeline.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime


class MediaType(Enum):
    MOVIE = "movie"
    TV_SHOW = "tv_show"
    MUSIC = "music"
    UNKNOWN = "unknown"


class Decision(Enum):
    PENDING = "pending"
    AUTO_ACCEPTED = "auto_accepted"
    QUARANTINE = "quarantine"
    IGNORED = "ignored"
    MANUAL_REVIEW = "manual_review"
    ERROR = "error"


@dataclass
class ScoreBreakdown:
    """Detailed breakdown of a confidence score."""
    title_similarity: float = 0.0
    year_match: float = 0.0
    keyword_overlap: float = 0.0
    overall: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "title_similarity": round(self.title_similarity, 3),
            "year_match": round(self.year_match, 3),
            "keyword_overlap": round(self.keyword_overlap, 3),
            "overall": round(self.overall, 3),
        }


@dataclass
class MetadataCandidate:
    """A potential metadata match for a media item."""
    source: str  # e.g., 'tmdb', 'tvmaze'
    id: str      # Source-specific ID
    title: str
    year: Optional[int] = None
    overview: Optional[str] = None
    score: ScoreBreakdown = field(default_factory=ScoreBreakdown)
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "id": self.id,
            "title": self.title,
            "year": self.year,
            "score": self.score.to_dict(),
        }


@dataclass
class MediaCandidate:
    """
    Internal model representing a media item traversing the pipeline.
    """
    original_path: str
    relative_path: str
    name: str  # Original filename or folder name
    media_type: MediaType = MediaType.UNKNOWN
    
    # Parsed from filename
    parsed_title: Optional[str] = None
    parsed_year: Optional[int] = None
    
    # Technical metadata
    file_metadata: Dict[str, Any] = field(default_factory=dict)
    subtitles: List[str] = field(default_factory=list)
    
    # Matching results
    candidates: List[MetadataCandidate] = field(default_factory=list)
    best_match: Optional[MetadataCandidate] = None
    
    # Pipeline status
    decision: Decision = Decision.PENDING
    decision_reason: Optional[str] = None
    confidence_score: float = 0.0
    
    # Final destination info
    destination_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": self.original_path,
            "relative_path": self.relative_path,
            "type": self.media_type.value,
            "parsed_title": self.parsed_title,
            "parsed_year": self.parsed_year,
            "subtitles": self.subtitles,
            "file_metadata": self.file_metadata,
            "decision": self.decision.value,
            "reason": self.decision_reason,
            "score": round(self.confidence_score, 3),
            "best_match": self.best_match.to_dict() if self.best_match else None,
            "alternatives": [c.to_dict() for c in self.candidates if c != self.best_match],
            "destination": self.destination_path,
        }


@dataclass
class PipelineContext:
    """Context for a single pipeline run."""
    source_dir: str
    dest_dir: str
    config: Any
    dry_run: bool = True
    start_time: datetime = field(default_factory=datetime.now)
    items: List[MediaCandidate] = field(default_factory=list)
    
    # Custom thresholds
    auto_accept_threshold: float = 0.85
    quarantine_threshold: float = 0.65
