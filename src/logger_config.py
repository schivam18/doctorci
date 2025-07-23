import logging
import os
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, f"clinical_trial_extraction_{datetime.now().strftime('%Y%m%d')}.log")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logging():
    """
    Set up logging to both file and console. Avoid duplicate handlers.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Remove all handlers if already set (avoid duplicate logs)
    if logger.hasHandlers():
        logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    logger.info("Logger configured: file and console handlers active.")


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)


# Performance logging decorator
def log_performance(func):
    """Decorator to log function execution time"""
    import functools
    import time

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.time()

        try:
            logger.info(f"Starting {func.__name__}")
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"Completed {func.__name__} in {execution_time:.2f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Failed {func.__name__} after {execution_time:.2f} seconds: {str(e)}")
            raise

    return wrapper
