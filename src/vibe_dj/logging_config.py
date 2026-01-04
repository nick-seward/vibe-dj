import sys

from loguru import logger

logger.remove()
logger.add(
    sys.stdout,
    format="{time:HH:mm:ss} [{level}] {message}",
    level="INFO"
)
