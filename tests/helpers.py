from __future__ import annotations

from parser.base_parser import LogLine
from model.events import ProcTimeEvent


def create_debug_log_line(domain: str, payload: str) -> LogLine:
    """Create a fake debug log line for testing."""
    return LogLine(
        raw=f"0:00:01.123456 12345 0xabcdef DEBUG {domain} {payload}",
        ts_str="0:00:01.123456",
        ts=61.123456,
        level="DEBUG",
        domain=domain,
        payload=payload
    )


def create_tracer_log_line(payload: str) -> LogLine:
    """Create a fake tracer log line for testing."""
    return LogLine(
        raw=f"0:00:01.123456 12345 0xabcdef TRACE GST_TRACER :0:: {payload}",
        ts_str="0:00:01.123456", 
        ts=61.123456,
        level="TRACE",
        domain="GST_TRACER",
        payload=f":0:: {payload}"
    )


def create_proctime_event(element: str, time_val: float) -> ProcTimeEvent:
    """Create a proctime event for testing."""
    return ProcTimeEvent(
        ts=0.0,
        link_key=("", ""),
        order=1,
        tracer_type="proctime",
        element_name=element,
        processing_time=time_val,
        processing_time_str=f"0:00:00.{time_val:06f}"
    )
