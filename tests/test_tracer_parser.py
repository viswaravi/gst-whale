from __future__ import annotations

import pytest

from sharkTracer import parse_tracer_line
from registry.gst_registry import GstRegistry
from tests.helpers import create_tracer_log_line


def test_parse_proctime_line():
    """Test parsing a proctime tracer line."""
    line = create_tracer_log_line("proctime, element=(string)test, time=(string)0:00:00.001;")
    registry = GstRegistry()
    
    parse_tracer_line(line, registry)
    
    assert len(registry.shark_events) == 1, "Should create one shark event"
    assert registry.shark_events[0].element_name == "test", "Should extract correct element name"
    assert registry.shark_events[0].processing_time == 0.001, "Should extract correct time"


def test_parse_unknown_tracer_line():
    """Test handling unknown tracer type."""
    line = create_tracer_log_line("unknown, data=123;")
    registry = GstRegistry()
    
    # Should not crash, but should not create events
    parse_tracer_line(line, registry)
    assert len(registry.shark_events) == 0, "Should not create events for unknown tracer"


def test_ignore_non_tracer_lines():
    """Test that non-tracer lines are ignored."""
    line = create_tracer_log_line("proctime, element=(string)test, time=(string)0:00:00.001;")
    line.domain = "GST_DEBUG"  # Change domain to non-tracer
    
    registry = GstRegistry()
    parse_tracer_line(line, registry)
    
    # Should not create any events since it's not GST_TRACER
    assert len(registry.shark_events) == 0, "Should ignore non-tracer lines"


def test_verbose_warning():
    """Test verbose warning for unknown tracer."""
    line = create_tracer_log_line("unknown, data=123;")
    registry = GstRegistry()
    
    # Should not raise exception with verbose=True
    parse_tracer_line(line, registry, verbose=True)
    
    # Should not create events
    assert len(registry.shark_events) == 0, "Should not create events for unknown tracer"


def test_element_creation():
    """Test that elements are created in registry."""
    line = create_tracer_log_line("proctime, element=(string)newelement, time=(string)0:00:00.001;")
    registry = GstRegistry()
    
    parse_tracer_line(line, registry)
    
    # Element should be created
    assert "newelement" in registry.elements, "Should create element in registry"
    element = registry.elements["newelement"]
    assert element.name == "newelement", "Should have correct element name"


def test_multiple_proctime_events():
    """Test parsing multiple proctime events."""
    registry = GstRegistry()
    
    # Parse multiple lines for same element
    lines = [
        create_tracer_log_line("proctime, element=(string)test, time=(string)0:00:00.001;"),
        create_tracer_log_line("proctime, element=(string)test, time=(string)0:00:00.002;"),
        create_tracer_log_line("proctime, element=(string)test, time=(string)0:00:00.003;"),
    ]
    
    for line in lines:
        parse_tracer_line(line, registry)
    
    assert len(registry.shark_events) == 3, "Should create three events"
    assert len(registry.element_processing_times["test"]) == 3, "Should have three processing times"
    
    # Check statistics
    stats = registry.get_element_processing_stats("test")
    assert stats is not None, "Should have stats for element"
    assert stats['count'] == 3, "Should have count of 3"
    assert stats['avg'] == 0.002, "Should have correct average"
    assert stats['min'] == 0.001, "Should have correct min"
    assert stats['max'] == 0.003, "Should have correct max"
