import json
import logging
import sys
import contextvars
from typing import Any, Dict

from core.config import settings

# Thread-safe request context for injecting trace IDs
request_context = contextvars.ContextVar("request_context", default={})

class JSONFormatter(logging.Formatter):
    """Custom formatter to output log records as structured JSON, including request context."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        log_record: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
            "filename": record.filename,
            "lineno": record.lineno,
        }
        
        # Inject trace context if active
        ctx = request_context.get()
        if ctx:
            log_record.update(ctx)
            
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging() -> None:
    """Configure the root logger with the structured JSONFormatter."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # Avoid duplicate handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(stream_handler)

# Initialize application-level logger
logger = logging.getLogger("omniseek")
