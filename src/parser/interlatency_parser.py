"""
Interlatency Parser for GST-Shark Tracer

Parses interlatency tracer lines to extract latency information between pipeline elements.
"""

from __future__ import annotations

import re
from typing import Optional

from parser.gst_shark_trace_parser import GstSharkTraceParser
from parser.base_parser import LogLine
from model.events import InterLatencyEvent


class InterlatencyParser(GstSharkTraceParser):
    """Parser for interlatency tracer data from gst-shark."""
    
    def __init__(self):
        """Initialize interlatency parser."""
        super().__init__("interlatency")
        
        # Regex pattern for parsing interlatency log lines
        # Format: :0:: interlatency, from_pad=(string)element_pad, to_pad=(string)element_pad, time=(string)timestamp;
        self.interlatency_re = re.compile(
            r':0::\s*interlatency,\s*'
            r'from_pad=\(string\)(?P<src_pad>[^,]+),\s*'
            r'to_pad=\(string\)(?P<sink_pad>[^,]+),\s*'
            r'time=\(string\)(?P<time>[^;]+);'
        )
        
        # Pattern to extract element name from pad name
        # Remove _src, _sink, and other pad suffixes
        self.element_name_re = re.compile(r'^(?P<element>[^_]+)')
    
    def can_handle(self, line: LogLine) -> bool:
        """Check if this parser can handle the given log line."""
        if line.domain != "GST_TRACER":
            return False
        
        # Check if the payload contains the interlatency pattern with :0:: prefix
        return ":0:: interlatency," in line.payload.strip()
    
    def parse_tracer_line(self, line: LogLine) -> Optional[InterLatencyEvent]:
        """
        Parse an interlatency tracer line and return an InterLatencyEvent.
        
        Args:
            line: LogLine containing interlatency tracer data
            
        Returns:
            InterLatencyEvent or None if parsing fails
        """
        match = self.interlatency_re.search(line.payload)
        if not match:
            return None
        
        src_pad = match.group('src_pad').strip()
        sink_pad = match.group('sink_pad').strip()
        time_str = match.group('time').strip()
        
        # Extract element names from pad names
        src_element = self._extract_element_name(src_pad)
        sink_element = self._extract_element_name(sink_pad)
        
        # Parse time string to float seconds
        latency = self._parse_timestamp_seconds(time_str)
        if latency is None:
            return None
        
        # Create InterLatencyEvent
        event = InterLatencyEvent(
            ts=line.ts,
            link_key=(src_element, sink_element),
            order=0,  # Will be set by registry
            tracer_type=self.tracer_type,
            element_name=src_element,  # Use source element as primary
            latency=latency,
            latency_str=time_str,
            src_element=src_element,
            sink_element=sink_element
        )
        
        return event
    
    def _extract_element_name(self, pad_name: str) -> str:
        """
        Extract element name from pad name.
        
        Args:
            pad_name: Full pad name (e.g., "videotestsrc0_src")
            
        Returns:
            Element name (e.g., "videotestsrc0")
        """
        # Split on underscore and take everything before the last part
        parts = pad_name.split('_')
        if len(parts) >= 2:
            # Remove the last part (pad name like 'src' or 'sink')
            return '_'.join(parts[:-1])
        return pad_name  # Fallback to full pad name
    
    def _parse_timestamp_seconds(self, ts: str) -> Optional[float]:
        """
        Parse time string to float seconds.
        
        Args:
            ts: Time string in format "0:00:00.000010769"
            
        Returns:
            Time in seconds as float, or None if parsing fails
        """
        parts = ts.split(":")
        if len(parts) != 3:
            return None
        
        try:
            h = int(parts[0])
            m = int(parts[1])
            # Handle seconds part that might have microseconds
            seconds_parts = parts[2].split('.')
            if len(seconds_parts) != 2:
                return None
            
            s = int(seconds_parts[0])
            microseconds = int(seconds_parts[1].ljust(9, '0')[:9])  # Pad to 9 digits
            return h * 3600.0 + m * 60.0 + s + microseconds / 1_000_000_000
        except (ValueError, IndexError):
            return None
