"""
Structured logging configuration module
"""
import json
import logging
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger

from .config import settings


class StructuredFormatter(jsonlogger.JsonFormatter):
    """Custom structured log formatter"""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['service'] = settings.APP_NAME
        log_record['version'] = settings.APP_VERSION
        
        # Add request context (if exists)
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        if hasattr(record, 'endpoint'):
            log_record['endpoint'] = record.endpoint
        if hasattr(record, 'method'):
            log_record['method'] = record.method
        if hasattr(record, 'status_code'):
            log_record['status_code'] = record.status_code
        if hasattr(record, 'response_time'):
            log_record['response_time'] = record.response_time
        
        # Add performance metrics
        if hasattr(record, 'duration'):
            log_record['duration'] = record.duration
        if hasattr(record, 'memory_usage'):
            log_record['memory_usage'] = record.memory_usage


class RequestContextFilter(logging.Filter):
    """Request context filter"""

    def filter(self, record: logging.LogRecord) -> bool:
        # Request context information can be added here
        # In actual use, request information can be obtained from contextvars or other places
        return True


def setup_logging() -> None:
    """Setup logging configuration"""

    # Choose log format based on environment
    if settings.LOG_FORMAT.lower() == 'json':
        formatter = StructuredFormatter(
            fmt='%(timestamp)s %(level)s %(logger)s %(message)s'
        )
    else:
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RequestContextFilter())
    root_logger.addHandler(console_handler)
    
    # File handler (if enabled)
    if hasattr(settings, 'LOG_FILE') and settings.LOG_FILE:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(RequestContextFilter())
        root_logger.addHandler(file_handler)
    
    # Configure third-party library log levels
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('uvicorn.access').setLevel(logging.INFO)
    logging.getLogger('transformers').setLevel(logging.WARNING)
    logging.getLogger('torch').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get structured logger"""
    return logging.getLogger(name)


class LoggerMixin:
    """Logger mixin class"""
    
    @property
    def logger(self) -> logging.Logger:
        return get_logger(self.__class__.__name__)
    
    def log_performance(self, operation: str, duration: float, **kwargs) -> None:
        """Record performance logs"""
        self.logger.info(
            f"Performance: {operation}",
            extra={
                'operation': operation,
                'duration': duration,
                **kwargs
            }
        )
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
        """Record error logs"""
        self.logger.error(
            f"Error: {str(error)}",
            extra={
                'error_type': type(error).__name__,
                'error_message': str(error),
                'context': context or {}
            },
            exc_info=True
        )
