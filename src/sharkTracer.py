from __future__ import annotations

from parser.base_parser import LogLine
from parser.proctime_parser import ProctimeParser
from parser.interlatency_parser import InterlatencyParser
from parser.gst_shark_trace_parser import TracerParserFactory
from registry.gst_registry import GstRegistry


def parse_tracer_line(line: LogLine, registry: GstRegistry, verbose: bool = False) -> None:
    """Parse a single GST_TRACER line and update registry."""
    if line.domain != "GST_TRACER":
        return
    
    # Initialize tracer parser factory
    factory = TracerParserFactory()
    factory.register_parser("proctime", ProctimeParser())
    factory.register_parser("interlatency", InterlatencyParser())
    
    tracer_parser = factory.get_parser_for_line(line)
    if tracer_parser:
        tracer_parser.handle(line, registry)
    elif verbose:
        print(f"Warning: No parser found for tracer line: {line.payload[:50]}...")
