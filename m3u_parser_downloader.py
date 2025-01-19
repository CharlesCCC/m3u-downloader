import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
import logging
from pathlib import Path
import threading
import re
from datetime import datetime

# Set up logging with thread safety
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(threadName)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('download_log.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Add thread-safe file writing
file_lock = threading.Lock()

def parse_m3u_file(file_path):
    """
    Parse M3U file and extract title and URL pairs.
    Returns list of tuples (title, url)
    """
    entries = []
    current_title = None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#EXTM3U') or line.startswith('#EXT-X-APP') or line.startswith('#EXT-X-APTV-TYPE'):
                    continue
                    
                if line.startswith('#EXTINF'):
                    # Extract group-title and name
                    group_match = re.search(r'group-title="([^"]+)"', line)
                    group_title = group_match.group(1) if group_match else "未分类"
                    
                    # Extract the name part after the group-title
                    name_match = re.search(r'group-title="[^"]+"\s*,\s*(.+)$', line)
                    name = name_match.group(1) if name_match else "未命名"
                    
                    # Combine group-title and name
                    current_title = f"{group_title}-{name}"
                else:
                    # This should be a URL line
                    if current_title and line.startswith('http'):
                        entries.append((current_title, line))
                        current_title = None
                        
    except Exception as e:
        logger.error(f"Error parsing M3U file: {str(e)}")
        return []
        
    return entries

def load_completed_downloads():
    completed_file = Path('completed_downloads.txt')
    if not completed_file.exists():
        return set()
    
    with file_lock:
        try:
            with open(completed_file, 'r', encoding='utf-8') as f:
                return set(line.strip() for line in f if line.strip())
        except Exception as e:
            logger.error(f"Error reading completed downloads file: {str(e)}")
            return set()

def mark_as_completed(name):
    with file_lock:
        try:
            with open('completed_downloads.txt', 'a', encoding='utf-8') as f:
                f.write(f"{name}\n")
        except Exception as e:
            logger.error(f"Error writing to completed downloads file: {str(e)}")

def get_unique_filename(base_name, output_dir):
    """
    Generate a unique filename by appending a sequence number if needed.
    Returns (unique_clean_name, output_file_path)
    """
    # Clean filename - remove invalid characters
    clean_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).strip()
    
    # Check if base filename exists
    counter = 1
    final_name = clean_name
    output_file = output_dir / f"{final_name}.mp4"
    
    while output_file.exists():
        counter += 1
        final_name = f"{clean_name}-{counter}"
        output_file = output_dir / f"{final_name}.mp4"
    
    return final_name, output_file

def download_and_encode(task):
    name, url = task
    output_dir = Path('downloads')
    TIMEOUT_SECONDS = 10800  # 3 hours in seconds
    
    thread_name = threading.current_thread().name
    logger.info(f"Thread {thread_name} processing: {name}")
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Get unique filename
    unique_name, output_file = get_unique_filename(name, output_dir)
    
    # Skip if already processed with this exact URL
    completed_downloads = load_completed_downloads()
    if f"{unique_name}:{url}" in completed_downloads:
        logger.info(f"Thread {thread_name}: Skipping {name} as it was already processed")
        return False
    
    # FFmpeg command
    cmd = [
        'ffmpeg',
        '-i', url,
        '-c:v', 'hevc_videotoolbox',     # Use H.265 codec
        '-preset', 'medium',    # Encoding preset
        '-crf', '28',          # Constant Rate Factor
        '-c:a', 'aac',         # Audio codec
        '-b:a', '128k',        # Audio bitrate
        '-y',                  # Overwrite output file if exists
        '-loglevel', 'error',  # Reduce FFmpeg output
        str(output_file)
    ]
    
    try:
        logger.info(f"Thread {thread_name}: Starting {name} -> {unique_name}")
        start_time = datetime.now()
        process = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        logger.info(f"Thread {thread_name}: Completed {unique_name}")
        # Store both name and URL to prevent duplicate downloads
        mark_as_completed(f"{unique_name}:{url}")
        return True
    except subprocess.TimeoutExpired as e:
        duration = datetime.now() - start_time
        logger.error(f"Thread {thread_name}: Timeout after {duration} processing {name}. Process terminated.")
        if output_file.exists():
            try:
                output_file.unlink()
                logger.info(f"Thread {thread_name}: Cleaned up partial file for {name}")
            except Exception as clean_error:
                logger.error(f"Thread {thread_name}: Error cleaning up partial file for {name}: {clean_error}")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Thread {thread_name}: Error processing {name}: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Thread {thread_name}: Unexpected error processing {name}: {str(e)}")
        return False

def process_m3u_file(input_file, max_workers=3):
    # Parse M3U file
    tasks = parse_m3u_file(input_file)
    
    if not tasks:
        logger.error("No valid entries found in the M3U file")
        return
        
    # Process tasks with thread pool
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix='FFmpeg') as executor:
        futures = [executor.submit(download_and_encode, task) for task in tasks]
        results = [f.result() for f in futures]
    
    # Summary
    total = len(tasks)
    successful = sum(1 for r in results if r)
    failed = total - successful
    
    logger.info(f"\nDownload Summary:")
    logger.info(f"Total tasks: {total}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Download and encode streams from M3U file')
    parser.add_argument('input_file', help='Input .m3u file')
    parser.add_argument('-w', '--workers', type=int, default=3, 
                      help='Number of concurrent downloads (default: 3). Be careful with system resources.')
    
    args = parser.parse_args()
    
    if not args.input_file.endswith('.m3u'):
        logger.error("Input file must be a .m3u file")
        exit(1)
        
    process_m3u_file(args.input_file, args.workers) 