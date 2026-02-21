from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Optional

from parser.base_parser import BaseParser, LogLine


class GstSharkTraceParser(BaseParser, ABC):
    """Base parser for GST_TRACER lines from gst-shark tracers."""
    
    def __init__(self, tracer_type: str):
        self.tracer_type = tracer_type
    
    def can_handle(self, line: LogLine) -> bool:
        """Check if this parser can handle the given log line."""
        if line.domain != "GST_TRACER":
            return False
        
        # Check if the payload starts with our tracer type
        return line.payload.startswith(f"{self.tracer_type},")
    
    @abstractmethod
    def parse_tracer_line(self, line: LogLine) -> Optional[object]:
        """Parse the tracer-specific payload and return an event."""
        pass
    
    def handle(self, line: LogLine, registry) -> None:
        """Handle a log line if it matches this tracer type."""
        if not self.can_handle(line):
            return
        
        event = self.parse_tracer_line(line)
        if event:
            registry.add_shark_event(event)


class TracerParserFactory:
    """Factory for creating and managing tracer parsers."""
    
    def __init__(self):
        self._parsers = {}
    
    def register_parser(self, tracer_type: str, parser: GstSharkTraceParser) -> None:
        """Register a parser for a specific tracer type."""
        self._parsers[tracer_type] = parser
    
    def get_parser(self, tracer_type: str) -> Optional[GstSharkTraceParser]:
        """Get a parser for the specified tracer type."""
        return self._parsers.get(tracer_type)
    
    def get_parser_for_line(self, line: LogLine) -> Optional[GstSharkTraceParser]:
        """Get the appropriate parser for a given log line."""
        if line.domain != "GST_TRACER":
            return None
        
        # Extract tracer type from payload (handle :0:: prefix)
        payload = line.payload.strip()
        if payload.startswith(":0:: "):
            payload = payload[5:]  # Remove ":0:: "
        
        parts = payload.split(',', 1)
        if not parts:
            return None
        
        tracer_type = parts[0].strip()
        return self.get_parser(tracer_type)


def detect_tracer_type(payload: str) -> Optional[str]:
    """Detect the tracer type from a log payload."""
    # Extract tracer type from payload (first word before comma)
    parts = payload.split(',', 1)
    if not parts:
        return None
    
    tracer_type = parts[0].strip()
    return tracer_type if tracer_type else None