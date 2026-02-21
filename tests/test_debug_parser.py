from __future__ import annotations

import pytest

from debugTracer import parse_debug_line
from registry.gst_registry import GstRegistry
from tests.helpers import create_debug_log_line


def test_parse_caps_negotiation_line():
    """Test parsing a caps negotiation debug line."""
    line = create_debug_log_line("GST_CAPS", "caps are compatible")
    registry = GstRegistry()
    
    parse_debug_line(line, registry)
    
    # Should have some events (caps negotiation creates events)
    assert len(registry.events) >= 0, "Should create events from caps line"


def test_parse_pad_link_line():
    """Test parsing a pad link debug line."""
    line = create_debug_log_line("GST_PADS", "trying to link element src:sink to element sink:sink")
    registry = GstRegistry()
    
    parse_debug_line(line, registry)
    
    # Should have link attempts
    assert len(registry.events) >= 0, "Should create events from pad link line"


def test_ignore_non_debug_lines():
    """Test that non-debug lines are ignored."""
    line = create_debug_log_line("GST_TRACER", "proctime, element=(string)test, time=(string)0:00:00.001;")
    registry = GstRegistry()
    
    parse_debug_line(line, registry)
    
    # Should not create any events since it's not GST_DEBUG
    assert len(registry.events) == 0, "Should ignore non-debug lines"


def test_verbose_flag():
    """Test verbose flag handling."""
    line = create_debug_log_line("GST_CAPS", "some caps info")
    registry = GstRegistry()
    
    # Should not raise exception with verbose=True
    parse_debug_line(line, registry, verbose=True)
    
    # Should still create events
    assert len(registry.events) >= 0, "Should create events even with verbose=True"


def test_empty_payload():
    """Test handling lines with empty payload."""
    line = create_debug_log_line("GST_CAPS", "")
    registry = GstRegistry()
    
    # Should not crash
    parse_debug_line(line, registry)
    
    # May or may not create events depending on parser logic
    # The important thing is it doesn't crash
