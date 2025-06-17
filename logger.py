import logging
import os
from logging.handlers import RotatingFileHandler
from colorlog import ColoredFormatter

logger = logging.getLogger("app_logger")
logger.setLevel(logging.DEBUG)

color_formatter = ColoredFormatter(
    "%(log_color)s[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
    "%Y-%m-%d %H:%M:%S",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    }
)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(color_formatter)
logger.addHandler(console_handler)

log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

file_formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s in %(module)s: %(message)s", "%Y-%m-%d %H:%M:%S"
)

file_handler = RotatingFileHandler(
    os.path.join(log_dir, "app.log"),
    maxBytes=1_000_000,
    backupCount=3,
    encoding="utf-8",
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(file_formatter)

logger.addHandler(file_handler)
