"""
Shared structured logging for the Analyse_Agent pipeline.
"""
import logging
import sys
from datetime import datetime

def setup_logger(name: str, level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        ))
        logger.addHandler(handler)
    return logger

def log_step(logger: logging.Logger, msg: str):
    logger.info(f"▶ {msg}")

def log_ok(logger: logging.Logger, msg: str):
    logger.info(f"✅ {msg}")

def log_warn(logger: logging.Logger, msg: str):
    logger.warning(f"⚠️ {msg}")

def log_error(logger: logging.Logger, msg: str):
    logger.error(f"❌ {msg}")
