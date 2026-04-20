import logging
import sys
from typing import Any

from dotenv import load_dotenv

load_dotenv()

DEBUG = sys.argv[1:] and sys.argv[1] == "--debug" or __import__("os").getenv("DEBUG", "False") == "True"


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if DEBUG:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG if DEBUG else logging.INFO)

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def log_request(logger: logging.Logger, method: str, path: str, user_id: int | None = None):
    extra = f"[user_id={user_id}]" if user_id else "[anonymous]"
    logger.info(f"{method} {path} {extra}")


def log_error(logger: logging.Logger, error: Exception, context: str = ""):
    context_str = f"[{context}] " if context else ""
    logger.error(f"{context_str}{type(error).__name__}: {error}")


def log_security(logger: logging.Logger, message: str, user_id: int | None = None):
    extra = f"[user_id={user_id}]" if user_id else "[anonymous]"
    logger.warning(f"SECURITY: {message} {extra}")