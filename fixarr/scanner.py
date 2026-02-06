import os
from utils import is_video, is_audio, is_subtitle, extract_tv_info, logger

class MediaScanner:
    def __init__(self, src_path):
        self.src_path = src_path

    def scan(self):
        """Scan SRC_PATH and group files into media items."""
        media_items = []
        for root, dirs, files in os.walk(self.src_path):
            if not files:
                continue

            # Group files in this directory
            video_files = [f for f in files if is_video(f)]
            audio_files = [f for f in files if is_audio(f)]
            subtitle_files = [f for f in files if is_subtitle(f)]

            if audio_files:
                # Treat directory as an album if it has many audio files
                media_items.append({
                    'type': 'music',
                    'path': root,
                    'files': [os.path.join(root, f) for f in audio_files]
                })
            
            elif video_files:
                # Check if it's a TV show or a movie
                tv_episodes = []
                for f in video_files:
                    s, e = extract_tv_info(f)
                    if s is not None:
                        tv_episodes.append({'file': f, 'season': s, 'episode': e})
                
                if len(tv_episodes) > 1:
                    # Likely a TV Show folder
                    media_items.append({
                        'type': 'tv_show',
                        'path': root,
                        'episodes': [os.path.join(root, e['file']) for e in tv_episodes],
                        'subtitles': [os.path.join(root, f) for f in subtitle_files]
                    })
                else:
                    # Treat each video as a movie or a single episode
                    for f in video_files:
                        s, e = extract_tv_info(f)
                        item_type = 'tv_show' if s is not None else 'movie'
                        
                        # Find matching subtitle
                        base_name = os.path.splitext(f)[0]
                        matching_subs = [os.path.join(root, sub) for sub in subtitle_files if sub.startswith(base_name)]
                        
                        media_items.append({
                            'type': item_type,
                            'path': os.path.join(root, f),
                            'name': f,
                            'season': s,
                            'episode': e,
                            'subtitles': matching_subs
                        })
        
        return media_items
