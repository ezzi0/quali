"""JSON logging with request ID and PII redaction"""
import logging
import re
import uuid
from contextvars import ContextVar
from typing import Any, Dict

import structlog
from structlog.processors import JSONRenderer
from structlog.stdlib import add_log_level, add_logger_name

# Context var for request ID
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

# PII patterns to redact
PII_PATTERNS = [
    (re.compile(r'\b[\w\.-]+@[\w\.-]+\.\w+\b'), '[EMAIL]'),  # email
    (re.compile(r'\b\d{10,15}\b'), '[PHONE]'),  # phone numbers
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '[SSN]'),  # SSN-like
]


def redact_pii(text: str) -> str:
    """Redact PII from log messages"""
    if not isinstance(text, str):
        return text
    for pattern, replacement in PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def add_request_id(logger: Any, method_name: str, event_dict: Dict) -> Dict:
    """Add request ID to log context"""
    rid = request_id_var.get()
    if rid:
        event_dict["request_id"] = rid
    return event_dict


def redact_pii_processor(logger: Any, method_name: str, event_dict: Dict) -> Dict:
    """Redact PII from event dict"""
    if "event" in event_dict:
        event_dict["event"] = redact_pii(event_dict["event"])
    return event_dict


def configure_logging(log_level: str = "INFO"):
    """Configure structured JSON logging"""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            add_log_level,
            add_logger_name,
            add_request_id,
            redact_pii_processor,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Set root logger level
    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, log_level.upper()),
    )


def get_logger(name: str):
    """Get a structured logger"""
    return structlog.get_logger(name)


def set_request_id(request_id: str | None = None):
    """Set request ID for current context"""
    rid = request_id or str(uuid.uuid4())
    request_id_var.set(rid)
    return rid
