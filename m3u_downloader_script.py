import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote
import logging
from pathlib import Path
import signal
from datetime import datetime
import threading

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

def download_and_encode(task):
    name, url = task
    output_dir = Path('downloads')
    TIMEOUT_SECONDS = 10800  # 3 hours in seconds
    
    thread_name = threading.current_thread().name
    logger.info(f"Thread {thread_name} processing: {name}")
    
    # Skip if name contains "台"
    if "台" in name:
        logger.info(f"Thread {thread_name}: Skipping {name} as it contains '台'")
        return False
    
    # Skip if already processed
    completed_downloads = load_completed_downloads()
    if name in completed_downloads:
        logger.info(f"Thread {thread_name}: Skipping {name} as it was already processed")
        return False
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    # Clean filename - remove invalid characters
    clean_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
    output_file = output_dir / f"{clean_name}.mp4"
    
    # Skip if file already exists
    if output_file.exists():
        logger.info(f"Thread {thread_name}: Skipping {name} as file already exists")
        mark_as_completed(name)
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
        logger.info(f"Thread {thread_name}: Starting {name}")
        start_time = datetime.now()
        process = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        logger.info(f"Thread {thread_name}: Completed {name}")
        mark_as_completed(name)
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

def process_file(input_file, max_workers=3):
    # Read all tasks
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            tasks = [line.strip().split(',', 1) for line in f if line.strip()]
    except Exception as e:
        logger.error(f"Error reading input file: {str(e)}")
        return

    # Process tasks with thread pool
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix='FFmpeg') as executor:
        futures = [executor.submit(download_and_encode, task) for task in tasks]
        results = [f.result() for f in futures]
    
    # Summary
    total = len(tasks)
    successful = sum(1 for r in results if r)
    failed = total - successful
    skipped = sum(1 for name, _ in tasks if "台" in name)
    
    logger.info(f"\nDownload Summary:")
    logger.info(f"Total tasks: {total}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    logger.info(f"Skipped (contains '台'): {skipped}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Download and encode M3U8 streams concurrently')
    parser.add_argument('input_file', help='Input file containing names and URLs')
    parser.add_argument('-w', '--workers', type=int, default=3, 
                      help='Number of concurrent downloads (default: 3). Be careful with system resources.')
    
    args = parser.parse_args()
    
    process_file(args.input_file, args.workers)