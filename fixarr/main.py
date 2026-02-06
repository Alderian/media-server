import argparse
import os
from scanner import MediaScanner
from metadata import MetadataManager
from organizer import MediaOrganizer
from utils import logger

def main():
    parser = argparse.ArgumentParser(description="Organize your media library.")
    parser.add_argument("--src", required=True, help="Source directory with unorganized media.")
    parser.add_argument("--dst", required=True, help="Destination directory for organized media.")
    args = parser.parse_args()

    if not os.path.exists(args.src):
        logger.error(f"Source path does not exist: {args.src}")
        return

    os.makedirs(args.dst, exist_ok=True)

    scanner = MediaScanner(args.src)
    metadata_mgr = MetadataManager()
    organizer = MediaOrganizer(args.dst)

    logger.info(f"Scanning {args.src}...")
    items = scanner.scan()
    logger.info(f"Found {len(items)} media items.")

    for item in items:
        try:
            if item['type'] == 'movie':
                meta = metadata_mgr.get_movie_metadata(item['name'])
                organizer.organize_movie(item, meta)
            
            elif item['type'] == 'tv_show':
                # For TV shows, we use the folder name or the first episode to get show metadata
                sample_name = os.path.basename(item['path']) if 'episodes' in item else item['name']
                meta = metadata_mgr.get_tv_metadata(sample_name)
                organizer.organize_tv_show(item, meta)
            
            elif item['type'] == 'music':
                organizer.organize_music(item)
                
        except Exception as e:
            logger.error(f"Error processing {item.get('path', 'unknown')}: {e}")

    organizer.save_report()
    logger.info("Organization complete. Check report.json for details.")

if __name__ == "__main__":
    main()
