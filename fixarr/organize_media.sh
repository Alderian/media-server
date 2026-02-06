#!/bin/bash
#
# Alderian Media Organizer - Main Script
# Orchestrates the organization of the media library.
#

# Find the script's directory and load configuration
SCRIPT_DIR="$(dirname "$0")"
source "$SCRIPT_DIR/config.sh"

# --- Argument Parsing ---
# Allow overriding config with command-line arguments
# Usage: ./organize_media.sh /path/to/source /path/to/dest
if [ "$1" ]; then
    SOURCE_DIR="$1"
fi
if [ "$2" ]; then
    DEST_DIR="$2"
fi

echo "Starting Alderian Media Organizer..."
echo "====================================="
echo "Source Directory: $SOURCE_DIR"
echo "Destination Directory: $DEST_DIR"
echo "====================================="

# --- Path Validation ---
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory '$SOURCE_DIR' not found."
    exit 1
fi

# --- Destination Directory Setup ---
# Create main destination and subdirectories if they don't exist
mkdir -p "$DEST_DIR/$MOVIE_DIR_NAME"
mkdir -p "$DEST_DIR/$TV_SHOW_DIR_NAME"
mkdir -p "$DEST_DIR/$MUSIC_DIR_NAME"
echo "Ensured destination directories exist."
echo ""

# --- State File ---
# This file tracks all files and directories that have already been processed.
PROCESSED_ITEMS_FILE=$(mktemp)
cleanup() {
    rm -f "$PROCESSED_ITEMS_FILE"
}
trap cleanup EXIT

mark_as_processed() {
    echo "$1" >> "$PROCESSED_ITEMS_FILE"
}

is_processed() {
    grep -qFx "$1" "$PROCESSED_ITEMS_FILE"
}

# --- Processing Functions (adapted for single files) ---

process_tv_show() {
    local video_file="$1"
    local filename
    filename=$(basename -- "$video_file")
    local extension="${filename##*.}"

    echo "    -> Detected as TV SHOW episode: $filename"

    # Simple cleanup: replace dots with spaces
    local cleaned_name
    cleaned_name=$(echo "$filename" | sed -E 's/(\.|\s)+/ /g')

    # Extract season and episode
    local season_episode
    season_episode=$(echo "$cleaned_name" | grep -oE '[Ss]([0-9]+)[Ee]([0-9]+)' | head -1 | tr '[:lower:]' '[:upper:]')
    if [ -z "$season_episode" ]; then # Try alternative 1x01 format
        season_episode=$(echo "$cleaned_name" | grep -oE '([0-9]+)x([0-9]+)' | head -1)
        if [ -n "$season_episode" ]; then
            local s_num
            s_num=$(echo "$season_episode" | cut -dx -f1)
            local e_num
            e_num=$(echo "$season_episode" | cut -dx -f2)
            season_episode="S$(printf "%02d" "$s_num")E$(printf "%02d" "$e_num")"
        fi
    fi
    
    local season_num
    season_num=$(echo "$season_episode" | grep -oE '[0-9]+' | head -1)
    
    # Extract show name (everything before the season/episode)
    local show_name
    show_name=$(echo "$cleaned_name" | sed -E "s/(.*)[Ss][0-9]+[Ee][0-9]+.*/\1/" | sed 's/ *$//')
    if [ -z "$show_name" ]; then # Try alternative 1x01 format
        show_name=$(echo "$cleaned_name" | sed -E "s/(.*)([0-9]+)x([0-9]+).*/\1/" | sed 's/ *$//')
    fi

    if [ -z "$show_name" ] || [ -z "$season_episode" ] || [ -z "$season_num" ]; then
        echo "    -> Could not parse TV show information from: $filename. Skipping."
        return 1 # Indicate failure
    fi

    local new_filename="${show_name} - ${season_episode}.${extension}"
    local dest_path="${DEST_DIR}/${TV_SHOW_DIR_NAME}/${show_name}/Season ${season_num}"
    
    move_media "$video_file" "$dest_path/$new_filename"
    return $? # Return status of move_media
}

process_movie() {
    local video_file="$1"
    local filename
    filename=$(basename -- "$video_file")
    local extension="${filename##*.}"

    echo "    -> Detected as MOVIE: $filename"

    # Simple cleanup: replace dots with spaces
    local cleaned_name
    cleaned_name=$(echo "$filename" | sed -E 's/(\.|\s)+/ /g')

    # Try to extract year (e.g., 1999, 2023)
    local year
    year=$(echo "$cleaned_name" | grep -oE '(19[8-9][0-9]|20[0-2][0-9])' | tail -1)
    
    local movie_title
    if [ -n "$year" ]; then
        # Get title from everything before the year
        movie_title=$(echo "$cleaned_name" | sed -E "s/(.*)($year).*/\1/" | sed 's/ *$//')
        movie_title="$movie_title ($year)"
    else
        # If no year, just use the cleaned name without resolution/tags
        movie_title=$(echo "$cleaned_name" | sed -E 's/ (1080p|720p|480p|bluray|dvd|x264|x265|xvid|h264|h265).*//i' | sed 's/ *$//')
    fi

    if [ -z "$movie_title" ]; then
        echo "    -> Could not parse movie information from: $filename. Skipping."
        return 1 # Indicate failure
    fi

    local new_filename="${movie_title}.${extension}"
    local dest_path="${DEST_DIR}/${MOVIE_DIR_NAME}/${movie_title}"

    move_media "$video_file" "$dest_path/$new_filename"
    return $? # Return status of move_media
}

# General function to move media files and associated subtitles
move_media() {
    local old_path="$1"
    local new_path="$2"
    local new_dir
    new_dir=$(dirname "$new_path")

    if is_processed "$old_path"; then
        echo "    -> File already processed: $old_path. Skipping move."
        return 0
    fi

    echo "    - Proposed New Path: $new_path"
    read -p "    -> Confirm move for '$old_path'? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "    -> Move skipped by user."
        return 1
    fi

    # Create destination directory
    mkdir -p "$new_dir"

    # Move the main video file
    mv -i "$old_path" "$new_path"
    if [ $? -eq 0 ]; then
        echo "    -> Moved main file."
        mark_as_processed "$old_path"
    else
        echo "    -> Failed to move main file: $old_path"
        return 1
    fi

    # Find and move associated files (subtitles, nfo, etc.)
    local base_filename
    base_filename=$(basename -- "$old_path")
    base_filename="${base_filename%.*}" # remove extension

    local old_dir
    old_dir=$(dirname "$old_path")

    find "$old_dir" -maxdepth 1 -type f -name "${base_filename}.*" -print0 | while IFS= read -r -d $'\0' associated_file; do
        if [ "$associated_file" != "$old_path" ] && ! is_processed "$associated_file"; then
            local assoc_ext="${associated_file##*.}"
            local new_assoc_filename
            new_assoc_filename=$(basename -- "$new_path")
            new_assoc_filename="${new_assoc_filename%.*}" # remove extension
            
            read -p "    -> Confirm move for associated file '$associated_file' to '$new_dir/$new_assoc_filename.$assoc_ext'? (y/N) " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                mv -i "$associated_file" "$new_dir/$new_assoc_filename.$assoc_ext"
                if [ $? -eq 0 ]; then
                    echo "    -> Moved associated file: $associated_file"
                    mark_as_processed "$associated_file"
                else
                    echo "    -> Failed to move associated file: $associated_file"
                fi
            else
                echo "    -> Associated file move skipped by user."
            fi
        fi
    done
    return 0
}

# --- Group processing functions ---

process_music_group() {
    local dir_path="$1"
    echo "  -> Processing music group: $dir_path"

    if is_processed "$dir_path"; then
        echo "  -> Directory already processed: $dir_path. Skipping."
        return
    fi

    read -p "  -> Confirm processing music directory '$dir_path' with Beets? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "  -> Music directory processing skipped by user."
        return
    fi

    # Call beets to import the entire directory.
    # -A asks for confirmation on matches but doesn't ask to select files.
    "$BEETS_CMD" import -A "$dir_path"
    if [ $? -eq 0 ]; then
        mark_as_processed "$dir_path"
        # Mark all files within this directory as processed too
        find "$dir_path" -type f -print0 | while IFS= read -r -d $'\0' f; do
            mark_as_processed "$f"
        done
        echo "  -> Music directory '$dir_path' processed and marked."
    else
        echo "  -> Beets import failed for '$dir_path'. Not marked as processed."
    fi
}

process_tv_season() {
    local dir_path="$1"
    echo "  -> Processing TV season directory: $dir_path"

    if is_processed "$dir_path"; then
        echo "  -> Directory already processed: $dir_path. Skipping."
        return
    fi

    read -p "  -> Confirm processing TV season directory '$dir_path'? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "  -> TV season processing skipped by user."
        return
    fi

    local processed_any_file=false
    find "$dir_path" -maxdepth 1 -type f -print0 | while IFS= read -r -d $'\0' video_file; do
        if [[ "$video_file" =~ \.(mkv|mp4|avi|mov|wmv)$ ]]; then
            if process_tv_show "$video_file"; then
                processed_any_file=true
            fi
        fi
    done

    if $processed_any_file; then
        mark_as_processed "$dir_path"
        echo "  -> TV season directory '$dir_path' processed and marked."
    else
        echo "  -> No TV show files successfully processed in '$dir_path'. Not marked as processed."
    fi
}

process_movie_collection() {
    local dir_path="$1"
    echo "  -> Processing movie collection directory: $dir_path"

    if is_processed "$dir_path"; then
        echo "  -> Directory already processed: $dir_path. Skipping."
        return
    fi

    read -p "  -> Confirm processing movie collection directory '$dir_path'? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "  -> Movie collection processing skipped by user."
        return
    fi

    local processed_any_file=false
    find "$dir_path" -maxdepth 1 -type f -print0 | while IFS= read -r -d $'\0' video_file; do
        if [[ "$video_file" =~ \.(mkv|mp4|avi|mov|wmv)$ ]]; then
            if process_movie "$video_file"; then
                processed_any_file=true
            fi
        fi
    done

    if $processed_any_file; then
        mark_as_processed "$dir_path"
        echo "  -> Movie collection directory '$dir_path' processed and marked."
    else
        echo "  -> No movie files successfully processed in '$dir_path'. Not marked as processed."
    fi
}

# New function to process a directory as a potential group
process_directory() {
    local dir_path="$1"
    if is_processed "$dir_path"; then
        echo "Skipping already processed directory: $dir_path"
        return
    fi

    echo "--- Analyzing directory: $dir_path ---"

    local music_files=0
    local video_files=0
    local tv_episode_files=0
    local total_files=0

    # First, gather stats on files within this directory
    find "$dir_path" -maxdepth 1 -type f -print0 | while IFS= read -r -d $'\0' file; do
        filename=$(basename -- "$file")
        extension="${filename##*.}"
        total_files=$((total_files + 1))

        case "$extension" in
            flac|mp3|m4a|aac|ogg|wav)
                music_files=$((music_files + 1))
                ;;
            mkv|mp4|avi|mov|wmv)
                video_files=$((video_files + 1))
                # Check for TV show patterns
                if [[ "$filename" =~ [Ss]([0-9]+)[Ee]([0-9]+) ]] || [[ "$filename" =~ ([0-9]+)x([0-9]+) ]]; then
                    tv_episode_files=$((tv_episode_files + 1))
                fi
                ;;
        esac
    done

    # Classify the directory based on its contents
    if [ "$total_files" -eq 0 ]; then
        echo "  -> Directory is empty or contains no media files. Skipping."
        mark_as_processed "$dir_path" # Mark empty directories as processed to avoid re-scanning
        return
    elif [ "$music_files" -gt 0 ] && [ "$music_files" -ge "$((total_files * 80 / 100))" ]; then # 80% music files
        echo "  -> Classified as MUSIC ALBUM."
        process_music_group "$dir_path"
    elif [ "$tv_episode_files" -gt 0 ] && [ "$tv_episode_files" -ge "$((video_files * 80 / 100))" ]; then # 80% TV episodes among video files
        echo "  -> Classified as TV SEASON."
        process_tv_season "$dir_path"
    elif [ "$video_files" -gt 0 ] && [ "$video_files" -ge "$((total_files * 80 / 100))" ]; then # 80% video files, mostly movies
        echo "  -> Classified as MOVIE COLLECTION."
        process_movie_collection "$dir_path"
    else
        echo "  -> Directory content is mixed or unknown. Leaving files for loose processing pass."
    fi
    echo ""
}

# New function to process a single, non-grouped file
process_loose_file() {
    local file_path="$1"

    if is_processed "$file_path"; then
        echo "Skipping already processed file: $file_path"
        return
    fi
    
    echo "--- Analyzing loose file: $file_path ---"
    local filename=$(basename -- "$file_path")
    local extension="${filename##*.}"

    case "$extension" in
        # --- Music Extensions ---
        flac|mp3|m4a|aac|ogg|wav)
            echo "  -> Detected as loose MUSIC file. Passing to Beets for interactive import..."
            if is_processed "$(dirname "$file_path")"; then
                echo "  -> Parent directory of loose music file already processed. Beets might not handle it again."
            fi
            "$BEETS_CMD" import -A "$file_path"
            if [ $? -eq 0 ]; then
                mark_as_processed "$file_path"
                echo "  -> Loose music file '$file_path' processed and marked."
            else
                echo "  -> Beets import failed for loose file '$file_path'. Not marked as processed."
            fi
            ;;

        # --- Video Extensions ---
        mkv|mp4|avi|mov|wmv)
            # Check for TV show patterns like S01E01, 1x01, etc.
            if [[ "$filename" =~ [Ss]([0-9]+)[Ee]([0-9]+) ]] || [[ "$filename" =~ ([0-9]+)x([0-9]+) ]]; then
                process_tv_show "$file_path"
            else
                process_movie "$file_path"
            fi
            ;;
        
        # --- Subtitle and other extensions to ignore for now ---
        srt|sub|ass|nfo|txt|jpg|png|jpeg) # Added common image types
            echo "  -> Ignoring associated or non-media file: $filename"
            mark_as_processed "$file_path" # Mark these as processed so they don't keep showing up
            ;;

        *)
            echo "  -> Unknown loose file type: $filename. Skipping."
            mark_as_processed "$file_path" # Mark as processed to avoid re-evaluation
            ;;
    esac
    echo ""
}

# --- Main Processing Logic ---

echo "--- Pass 1: Processing Groups (Directories) ---"
# Use find to loop through directories, from deepest to shallowest
find "$SOURCE_DIR" -type d -print0 | while IFS= read -r -d $'\0' current_dir; do
    # Avoid processing the root source directory itself as a group
    if [ "$current_dir" != "$SOURCE_DIR" ]; then
        process_directory "$current_dir"
    fi
done

echo ""
echo "--- Pass 2: Processing Loose Files ---"
find "$SOURCE_DIR" -type f -print0 | while IFS= read -r -d $'\0' current_file; do
    process_loose_file "$current_file"
done


echo ""
echo "====================================="
echo "Alderian Media Organizer finished."
echo "====================================="
