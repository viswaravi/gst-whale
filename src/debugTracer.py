from __future__ import annotations

from parser.base_parser import LogLine
from parser.caps_parser import CapsParser
from parser.element_pads_parser import ElementPadsParser
from registry.gst_registry import GstRegistry


def parse_debug_line(line: LogLine, registry: GstRegistry, verbose: bool = False) -> None:
    """Parse a single GST_DEBUG line and update registry."""
    if line.domain != "GST_DEBUG":
        return
    
    # Initialize debug parsers
    parsers = [ElementPadsParser(), CapsParser(verbose=verbose)]
    
    for parser in parsers:
        parser.handle(line, registry)
