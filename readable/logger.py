"""Logging configuration for Readable app."""

import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logger(name: str = "readable") -> logging.Logger:
    """Configure and return logger with both file and console output."""

    # Create logs directory
    log_dir = Path.home() / ".readable" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"readable_{timestamp}.log"

    # Configure logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Remove existing handlers
    logger.handlers = []

    # File handler - detailed logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    # Console handler - important logs only
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logging initialized - log file: {log_file}")

    return logger

def get_logger(name: str = "readable") -> logging.Logger:
    """Get existing logger or create new one."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        return setup_logger(name)
    return logger
