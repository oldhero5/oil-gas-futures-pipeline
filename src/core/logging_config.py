import logging
import logging.handlers
import sys
from pathlib import Path

import structlog


def setup_logging(
    log_level: str = "INFO",
    log_file_path: str = "logs/app.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> None:
    """Configure structured logging with console and rotating file handlers."""

    # Ensure log directory exists
    log_path = Path(log_file_path)
    log_dir = log_path.parent
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)

    # Shared processors for all logs
    shared_processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.PATHNAME,
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.MODULE,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
    ]

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Console Handler (human-readable)
    console_formatter = structlog.stdlib.ProcessorFormatter.wrap_for_formatter(
        # Renderer for console output
        renderer=structlog.dev.ConsoleRenderer(),
        # foreign_pre_chain=shared_processors, # Not needed if configuring root logger directly
    )
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)

    # File Handler (JSON, rotating)
    file_formatter = structlog.stdlib.ProcessorFormatter.wrap_for_formatter(
        # Renderer for file output (JSON)
        renderer=structlog.processors.JSONRenderer(),
        # foreign_pre_chain=shared_processors, # Not needed if configuring root logger directly
    )
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(file_formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    # Clear any existing handlers to prevent duplicate logs if this is called multiple times
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.setLevel(log_level.upper())

    # Suppress overly verbose loggers from libraries if necessary
    # logging.getLogger("some_library").setLevel(logging.WARNING)

    logger = structlog.get_logger(__name__)
    logger.info(
        "Logging configured",
        log_level=log_level,
        console_output=True,
        file_output=True,
        log_file=log_file_path,
    )
