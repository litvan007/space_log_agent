from __future__ import annotations

import logging
import sys

from loguru import logger

from space_log_agent.config import AppConfig


def _build_standard_formatter() -> logging.Formatter:
    """Build a shared formatter for stdlib loggers."""

    return logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _configure_standard_logger(logger_name: str, log_file_path: str, formatter: logging.Formatter) -> None:
    """Attach stream and file handlers to a stdlib logger."""

    configured_logger = logging.getLogger(logger_name)
    configured_logger.handlers.clear()
    configured_logger.setLevel(logging.INFO)
    configured_logger.propagate = False

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    configured_logger.addHandler(stream_handler)
    configured_logger.addHandler(file_handler)


def setup_logging(config: AppConfig) -> None:
    """Настраивает централизованное логирование стенда на русском языке."""
    config.resolved_logs_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(
        sys.stderr,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        level="INFO",
        enqueue=False,
    )
    logger.add(
        str(config.resolved_log_file_path),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="14 days",
        encoding="utf-8",
        enqueue=False,
    )

    std_formatter = _build_standard_formatter()
    for logger_name in ("sgr_agent_core", "uvicorn", "uvicorn.error", "uvicorn.access"):
        _configure_standard_logger(logger_name, str(config.resolved_log_file_path), std_formatter)

    logger.info("Логирование инициализировано. Файл: {}", config.resolved_log_file_path)
