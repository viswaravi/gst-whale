from __future__ import annotations

import pytest

from parser.proctime_parser import ProctimeParser
from tests.helpers import create_tracer_log_line


def test_proctime_regex():
    """Test proctime parser regex matching."""
    parser = ProctimeParser()
    
    # Valid line
    valid_line = create_tracer_log_line("proctime, element=(string)test, time=(string)0:00:00.001;")
    assert parser.can_handle(valid_line), "Should handle valid proctime line"
    
    event = parser.parse_tracer_line(valid_line)
    assert event is not None, "Should parse valid proctime line"
    assert event.element_name == "test", f"Expected element 'test', got '{event.element_name}'"
    assert event.processing_time == 0.001, f"Expected time 0.001, got {event.processing_time}"
    
    # Invalid line
    invalid_line = create_tracer_log_line("othertracer, data=123;")
    assert not parser.can_handle(invalid_line), "Should not handle other tracer line"


def test_time_parsing():
    """Test various time format parsing."""
    parser = ProctimeParser()
    
    test_cases = [
        ("0:00:00.001", 0.001),
        ("0:01:30.500", 90.5),
        ("1:00:00.000", 3600.0),
        ("0:00:00.000123456", 0.000123456),
    ]
    
    for time_str, expected in test_cases:
        payload = f"proctime, element=(string)test, time=(string){time_str};"
        line = create_tracer_log_line(payload)
        event = parser.parse_tracer_line(line)
        assert event is not None, f"Should parse time '{time_str}'"
        assert abs(event.processing_time - expected) < 1e-9, f"Expected {expected}, got {event.processing_time}"


def test_element_name_parsing():
    """Test element name parsing."""
    parser = ProctimeParser()
    
    test_cases = [
        "capsfilter0",
        "videoconvert0", 
        "videoscale0",
        "test_element_123",
        "src",
        "sink",
    ]
    
    for element_name in test_cases:
        payload = f"proctime, element=(string){element_name}, time=(string)0:00:00.001;"
        line = create_tracer_log_line(payload)
        event = parser.parse_tracer_line(line)
        assert event is not None, f"Should parse element '{element_name}'"
        assert event.element_name == element_name, f"Expected '{element_name}', got '{event.element_name}'"


def test_malformed_lines():
    """Test handling of malformed proctime lines."""
    parser = ProctimeParser()
    
    # Missing element
    malformed_line1 = create_tracer_log_line("proctime, time=(string)0:00:00.001;")
    event1 = parser.parse_tracer_line(malformed_line1)
    assert event1 is None, "Should fail parsing line without element"
    
    # Missing time
    malformed_line2 = create_tracer_log_line("proctime, element=(string)test;")
    event2 = parser.parse_tracer_line(malformed_line2)
    assert event2 is None, "Should fail parsing line without time"
    
    # Malformed time
    malformed_line3 = create_tracer_log_line("proctime, element=(string)test, time=(string)not_a_time;")
    event3 = parser.parse_tracer_line(malformed_line3)
    assert event3 is None, "Should fail parsing line with malformed time"


def test_real_log_format():
    """Test parsing with actual log format including ANSI codes."""
    parser = ProctimeParser()
    
    # Simulate real log line format
    raw_line = "0:00:00.080014532 41265 0x7182a8000c00 TRACE GST_TRACER :0:: proctime, element=(string)capsfilter0, time=(string)0:00:00.000004657;"
    
    from parser.base_parser import GstLogLineParser
    line_parser = GstLogLineParser()
    parsed = line_parser.parse(raw_line)
    
    assert parsed is not None, "Should parse real log line"
    assert parsed.domain == "GST_TRACER", "Should have GST_TRACER domain"
    assert parser.can_handle(parsed), "Should handle real proctime line"
    
    event = parser.parse_tracer_line(parsed)
    assert event is not None, "Should parse event from real line"
    assert event.element_name == "capsfilter0", "Should extract correct element name"
    assert abs(event.processing_time - 0.000004657) < 1e-9, "Should extract correct time"
