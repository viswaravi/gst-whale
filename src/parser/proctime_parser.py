from __future__ import annotations

import re
from typing import Optional

from model.events import ProcTimeEvent
from parser.base_parser import LogLine
from parser.gst_shark_trace_parser import GstSharkTraceParser


# Regex to parse proctime tracer lines:
# :0:: proctime, element=(string)capsfilter0, time=(string)0:00:00.000004657;
PROCTIME_RE = re.compile(
    r':0::\s*proctime,\s*'
    r'element=\(string\)(?P<element>[^,]+),\s*'
    r'time=\(string\)(?P<time>[^;]+);'
)


class ProctimeParser(GstSharkTraceParser):
    """Parser for proctime tracer lines."""
    
    def __init__(self):
        super().__init__("proctime")
    
    def can_handle(self, line: LogLine) -> bool:
        """Check if this parser can handle the given log line."""
        if line.domain != "GST_TRACER":
            return False
        
        # Check if the payload contains the proctime pattern with :0:: prefix
        return ":0:: proctime," in line.payload.strip()
    
    def parse_tracer_line(self, line: LogLine) -> Optional[ProcTimeEvent]:
        """Parse a proctime tracer line and return a ProcTimeEvent."""
        match = PROCTIME_RE.search(line.payload)
        if not match:
            return None
        
        element_name = match.group("element").strip()
        time_str = match.group("time").strip()
        
        # Convert time string to seconds
        processing_time = self._parse_timestamp_seconds(time_str)
        if processing_time is None:
            return None
        
        return ProcTimeEvent(
            ts=line.ts,
            link_key=("", ""),  # Will be set by __post_init__
            order=0,  # Will be set by registry
            tracer_type=self.tracer_type,
            element_name=element_name,
            processing_time=processing_time,
            processing_time_str=time_str
        )
    
    def _parse_timestamp_seconds(self, ts: str) -> Optional[float]:
        """Parse timestamp string in format H:M:S.microseconds to seconds."""
        parts = ts.split(":")
        if len(parts) != 3:
            return None
        
        try:
            h = int(parts[0])
            m = int(parts[1])
            s = float(parts[2])
            return h * 3600.0 + m * 60.0 + s
        except (ValueError, IndexError):
            return None
