import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict

from models import MediaCandidate, MediaType, Decision


@dataclass
class Report:
    """Complete report of a media organization run."""
    run_id: str
    started_at: str
    source_directory: str
    destination_directory: str
    config_file: Optional[str]
    dry_run: bool

    results: List[Dict[str, Any]] = field(default_factory=list)

    # Summary statistics
    total_scanned: int = 0
    movies_processed: int = 0
    tv_shows_processed: int = 0
    music_processed: int = 0
    items_quarantined: int = 0
    errors: int = 0

    completed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at or datetime.now().isoformat(),
            "source_directory": self.source_directory,
            "destination_directory": self.destination_directory,
            "config_file": self.config_file,
            "dry_run": self.dry_run,
            "summary": {
                "total_scanned": self.total_scanned,
                "movies_processed": self.movies_processed,
                "tv_shows_processed": self.tv_shows_processed,
                "music_processed": self.music_processed,
                "items_quarantined": self.items_quarantined,
                "errors": self.errors,
            },
            "results": self.results,
        }


class ReportGenerator:
    """Generates and manages organization reports."""

    def __init__(
        self,
        source_dir: str,
        dest_dir: str,
        config_file: Optional[str] = None,
        dry_run: bool = True,
    ):
        self.report = Report(
            run_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            started_at=datetime.now().isoformat(),
            source_directory=source_dir,
            destination_directory=dest_dir,
            config_file=config_file,
            dry_run=dry_run,
        )

    def add_candidate(self, candidate: MediaCandidate) -> None:
        """Add a processed candidate to the report."""
        res = {
            "name": candidate.name,
            "path": candidate.original_path,
            "type": candidate.media_type.value,
            "decision": candidate.decision.value,
            "reason": candidate.decision_reason,
            "score": candidate.confidence_score,
            "destination": candidate.destination_path,
            "match": {
                "title": candidate.best_match.title,
                "year": candidate.best_match.year,
                "id": candidate.best_match.id,
                "source": candidate.best_match.source
            } if candidate.best_match else None
        }
        self.report.results.append(res)
        self.report.total_scanned += 1

        if candidate.decision == Decision.AUTO_ACCEPTED:
            if candidate.media_type == MediaType.MOVIE:
                self.report.movies_processed += 1
            elif candidate.media_type == MediaType.TV_SHOW:
                self.report.tv_shows_processed += 1
            elif candidate.media_type == MediaType.MUSIC:
                self.report.music_processed += 1
        elif candidate.decision == Decision.QUARANTINE:
            self.report.items_quarantined += 1
        # Decision.IGNORE is just scanned but not counted in processed/quarantined

    def save(self, path: str = "report.json") -> str:
        self.report.completed_at = datetime.now().isoformat()
        report_dir = os.path.dirname(path)
        if report_dir:
            os.makedirs(report_dir, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.report.to_dict(), f, indent=2, ensure_ascii=False)

        return path

    def print_summary(self) -> None:
        r = self.report
        print("\n" + "=" * 50)
        print("FIXARR ORGANIZATION SUMMARY (PIPELINE V2)")
        print("=" * 50)
        print(f"Total items scanned: {r.total_scanned}")
        print(f"Movies processed:    {r.movies_processed}")
        print(f"TV shows processed:  {r.tv_shows_processed}")
        print(f"Music processed:     {r.music_processed}")
        print(f"Items quarantined:   {r.items_quarantined}")
        print(f"Errors:              {r.errors}")
        print("=" * 50 + "\n")

        quarantined = [res for res in r.results if res["decision"] == Decision.QUARANTINE.value]
        if quarantined:
            print("Items in Quarantine (Review Needed):")
            for item in quarantined:
                print(f"  - {item['name']}")
                print(f"    Reason: {item['reason']}")
            print()
