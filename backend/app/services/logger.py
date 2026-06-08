"""Structured logging service using loguru."""

import sys
from pathlib import Path

from loguru import logger

_FMT_CONSOLE = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green>"
    " | <level>{level: <8}</level>"
    " | <cyan>{name}</cyan>:<cyan>{function}</cyan>"
    ":<cyan>{line}</cyan> - <level>{message}</level>"
)

_FMT_FILE = (
    "{time:YYYY-MM-DD HH:mm:ss}"
    " | {level: <8} | {name}:{function}:{line} - {message}"
)

logger.remove()
logger.add(sys.stderr, format=_FMT_CONSOLE, level="INFO")

_log_dir = Path(__file__).resolve().parent.parent.parent / "logs"
_log_dir.mkdir(exist_ok=True)
logger.add(
    str(_log_dir / "app_{time:YYYY-MM-DD}.log"),
    rotation="10 MB",
    retention="7 days",
    compression="gz",
    level="DEBUG",
    format=_FMT_FILE,
)

app_logger = logger.bind(module="app")
