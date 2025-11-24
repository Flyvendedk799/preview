"""Structured logging configuration for production."""
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add request context if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "organization_id"):
            log_data["organization_id"] = record.organization_id
        if hasattr(record, "path"):
            log_data["path"] = record.path
        if hasattr(record, "method"):
            log_data["method"] = record.method
        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code
        if hasattr(record, "latency_ms"):
            log_data["latency_ms"] = record.latency_ms
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        return json.dumps(log_data)


def setup_logging(level: str = "INFO"):
    """Setup structured JSON logging."""
    # Remove default handlers
    root_logger = logging.getLogger()
    root_logger.handlers = []
    
    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    
    # Configure root logger
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    root_logger.addHandler(console_handler)
    
    # Set levels for third-party loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("gunicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)

