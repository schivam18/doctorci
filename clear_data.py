import os
import shutil
import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def safe_remove_dir(path: str):
    if os.path.exists(path) and os.path.isdir(path):
        logging.info(f"Deleting directory and all contents: {path}")
        shutil.rmtree(path)
    else:
        logging.info(f"Directory not found, skipping: {path}")

def safe_remove_file(path: str):
    if os.path.exists(path) and os.path.isfile(path):
        logging.info(f"Deleting file: {path}")
        os.remove(path)
    else:
        logging.info(f"File not found, skipping: {path}")

def create_processed_files():
    """Create a fresh processed_files.json with empty tracking (clears processed file names)"""
    processed_files = {
        "processed_files": [],
        "failed_files": [],
        "last_processed": None,
        "total_processed": 0,
        "total_failed": 0
    }
    
    with open('data/processed_files.json', 'w') as f:
        json.dump(processed_files, f, indent=2)
    logging.info("Cleared processed file names from tracking")

def main():
    # Directories to clean (removed 'logs' to keep it)
    dirs_to_clean = [
        'test_output',
        'output',
    ]
    for d in dirs_to_clean:
        safe_remove_dir(d)

    # Remove known temp/intermediate files (add more as needed)
    temp_files = [
        'logs/pipeline_metrics.json',
        'logs/cost_tracking.json',
    ]
    for f in temp_files:
        safe_remove_file(f)

    # Create fresh processed_files.json instead of removing it
    create_processed_files()

    logging.info("Cleanup complete.")

if __name__ == "__main__":
    main() 