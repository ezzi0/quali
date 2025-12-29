"""
Lightweight telemetry helpers.

Uses OpenTelemetry if available; otherwise no-ops. Keeps code optional so
runtime doesn't fail when OTel packages are absent.
"""
from contextlib import contextmanager
from typing import Optional
import time
import logging

try:
    from opentelemetry import trace
    from opentelemetry.trace import Tracer
except Exception:  # OpenTelemetry not installed
    trace = None
    Tracer = None

logger = logging.getLogger(__name__)


def get_tracer(name: str = "app") -> Optional["Tracer"]:
    """Return tracer if OpenTelemetry is installed; else None."""
    if trace is None:
        return None
    return trace.get_tracer(name)


@contextmanager
def span(tracer: Optional["Tracer"], name: str, attributes: Optional[dict] = None):
    """
    Context manager for spans; no-op if tracer is None.
    """
    if tracer is None:
        start = time.time()
        try:
            yield None
        finally:
            logger.debug("span", extra={"span": name, "duration": round(time.time() - start, 3)})
        return

    with tracer.start_as_current_span(name) as sp:
        if attributes:
            for k, v in attributes.items():
                sp.set_attribute(k, v)
        yield sp
