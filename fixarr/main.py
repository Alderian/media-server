#!/usr/bin/env python3
"""
Fixarr - Media Library Organizer

A non-interactive tool to organize movies, TV shows, and music into
a clean library structure compatible with Jellyfin, Plex, and Kodi.
"""

import argparse
import os
import sys
from typing import List

from config import get_config, reset_config, Config
from scanner import MediaScanner
from metadata import MetadataManager
from scoring import ConfidenceScorer
from organizer import MediaOrganizer
from report import ReportGenerator
from models import MediaCandidate, MediaType, PipelineContext
from utils import get_logger, set_verbose

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fixarr - Media Library Organizer (Pipeline v2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--src", metavar="PATH", help="Source directory")
    parser.add_argument("--dst", metavar="PATH", help="Destination directory")
    parser.add_argument("--config", metavar="FILE", help="Config file")
    parser.add_argument("--apply", action="store_true", help="Apply changes (defaults to dry-run)")
    parser.add_argument("--report", metavar="FILE", default="report.json", help="Report path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    return parser.parse_args()

def main() -> int:
    args = parse_arguments()
    reset_config()
    config = get_config(args.config)

    if args.verbose:
        set_verbose(True)
    logger = get_logger("fixarr", verbose=args.verbose)

    src_path = args.src or config.paths.get("default_src")
    dst_path = args.dst or config.paths.get("default_dst")

    if not src_path or not dst_path:
        logger.error("Source and destination paths required.")
        return 1

    src_path = os.path.abspath(os.path.expanduser(src_path))
    dst_path = os.path.abspath(os.path.expanduser(dst_path))
    dry_run = not args.apply

    if dry_run:
        logger.info("=== DRY RUN MODE - Use --apply to execute changes ===")

    # Initialize components
    scanner = MediaScanner(src_path)
    metadata_mgr = MetadataManager(config_path=args.config)
    scorer = ConfidenceScorer()
    organizer = MediaOrganizer(dst_path, src_path=src_path, config=config, dry_run=dry_run)
    report = ReportGenerator(src_path, dst_path, config_file=args.config, dry_run=dry_run)
    
    context = PipelineContext(
        source_dir=src_path,
        dest_dir=dst_path,
        config=config,
        dry_run=dry_run
    )

    # Stage 1: Scan & Group
    logger.info(f"Pipeline Stage: Scan & Group ({src_path})")
    candidates = scanner.scan_and_group()
    logger.info(f"Found {len(candidates)} media candidates")

    # Stage 2: Identify & Score
    logger.info("Pipeline Stage: Identify & Score")
    for cand in candidates:
        if cand.media_type == MediaType.MUSIC:
            continue
            
        logger.info(f"  Identifying: {cand.name}")
        metadata_mgr.identify(cand)
            
        # Scoring
        if cand.candidates:
            scorer.score(cand)
            if cand.best_match:
                logger.info(f"    Best match: {cand.best_match.title} ({cand.best_match.year}) - Score: {cand.confidence_score:.2f}")
        else:
            logger.warning(f"    No metadata found for {cand.name}")

    # Stage 3: Decide & Apply
    logger.info("Pipeline Stage: Decide & Apply")
    for cand in candidates:
        organizer.decide(cand)
        organizer.apply(cand)
        report.add_candidate(cand)

    # Final Report
    report.save(args.report)
    report.print_summary()

    return 0

if __name__ == "__main__":
    sys.exit(main())
