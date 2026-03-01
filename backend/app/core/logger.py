import logging
from datetime import datetime, timezone
from app.core.config import settings
import sys

class StructuredLoggingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # Expected outputs: timestamp | level | request_id | endpoint | latency | thread | message
        
        timestamp = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        level = record.levelname
        
        request_id = getattr(record, "request_id", "-")
        endpoint = getattr(record, "endpoint", "-")
        latency = getattr(record, "latency_ms", None)
        latency_str = f"latency={latency}ms" if latency is not None else "latency=-"
        thread_name = getattr(record, "thread_name", record.threadName)
        
        message = record.getMessage()
        
        log_parts = [
            timestamp,
            level,
            f"request_id={request_id}",
            f"endpoint={endpoint}",
            latency_str,
            f"thread={thread_name}",
            message
        ]
        
        # Filter out empty/placeholder dashes where not useful if doing complex formatting,
        # but the requested format specifically binds them with pipes
        return " | ".join(log_parts)

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
    
    # Avoid duplicate handlers if logger is fetched multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredLoggingFormatter())
        logger.addHandler(handler)
        
    return logger

# Global App Logger
logger = setup_logger("finaccess")
