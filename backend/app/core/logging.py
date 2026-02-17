import logging
import os
from logging.handlers import RotatingFileHandler
from app.core.config import settings


def setup_logging():
    """Configure application logging with rotating file handler."""
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            RotatingFileHandler(
                "logs/app.log",
                maxBytes=10 * 1024 * 1024,  # 10 MB
                backupCount=5,
            ),
            logging.StreamHandler(),
        ],
    )

    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    return logging.getLogger(__name__)
