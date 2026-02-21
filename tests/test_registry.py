from __future__ import annotations

import pytest

from registry.gst_registry import GstRegistry
from model.element import GstElement
from model.pad import GstPad
from tests.helpers import create_proctime_event


def test_element_creation():
    """Test element creation and retrieval."""
    registry = GstRegistry()
    
    # Create new element
    element = registry.get_or_create_element("test_element")
    assert element is not None, "Should create element"
    assert element.name == "test_element", "Should have correct name"
    assert "test_element" in registry.elements, "Should be in registry"
    
    # Get existing element
    existing = registry.get_or_create_element("test_element")
    assert existing is element, "Should return existing element"
    assert len(registry.elements) == 1, "Should not create duplicate"


def test_pad_creation():
    """Test pad creation and element association."""
    registry = GstRegistry()
    
    # Create pad
    pad = registry.get_or_create_pad("test_element", "src")
    assert pad is not None, "Should create pad"
    assert pad.element_name == "test_element", "Should have correct element"
    assert pad.pad_name == "src", "Should have correct pad name"
    assert pad.key == "test_element:src", "Should have correct key"
    
    # Element should be created too
    assert "test_element" in registry.elements, "Should create element"
    element = registry.elements["test_element"]
    assert element.get_pad("src") is pad, "Pad should be in element"


def test_processing_stats_calculation():
    """Test processing time statistics calculation."""
    registry = GstRegistry()
    
    # Add some proctime events
    events = [
        create_proctime_event("elem1", 0.001),
        create_proctime_event("elem1", 0.002), 
        create_proctime_event("elem2", 0.005),
        create_proctime_event("elem1", 0.003),
    ]
    
    for event in events:
        registry.add_shark_event(event)
    
    # Test stats for elem1
    stats = registry.get_element_processing_stats("elem1")
    assert stats is not None, "Should have stats for elem1"
    assert stats['count'] == 3, "Should have count of 3"
    assert stats['total'] == 0.006, "Should have total of 0.006"
    assert stats['avg'] == 0.002, "Should have average of 0.002"
    assert stats['min'] == 0.001, "Should have min of 0.001"
    assert stats['max'] == 0.003, "Should have max of 0.003"
    
    # Test stats for elem2
    stats2 = registry.get_element_processing_stats("elem2")
    assert stats2 is not None, "Should have stats for elem2"
    assert stats2['count'] == 1, "Should have count of 1"
    assert stats2['avg'] == 0.005, "Should have average of 0.005"


def test_element_pad_management():
    """Test element and pad relationship management."""
    registry = GstRegistry()
    
    # Create element and add pads
    element = registry.get_or_create_element("test_element")
    src_pad = GstPad("test_element", "src")
    sink_pad = GstPad("test_element", "sink")
    
    element.add_pad(src_pad)
    element.add_pad(sink_pad)
    
    # Test pad retrieval
    assert element.get_pad("src") is src_pad, "Should retrieve src pad"
    assert element.get_pad("sink") is sink_pad, "Should retrieve sink pad"
    assert len(element.pads) == 2, "Should have 2 pads"
    
    # Test pad linking
    element.link_pad("src", "other_element:src")
    assert element.pad_links["src"] == "other_element:src", "Should link src pad"
    
    # Test convenience methods
    src_pads = element.get_src_pads()
    sink_pads = element.get_sink_pads()
    assert len(src_pads) == 1, "Should have 1 src pad"
    assert len(sink_pads) == 1, "Should have 1 sink pad"
    assert src_pads["src"] is src_pad, "Src pad should be correct"


def test_all_processing_stats():
    """Test getting all processing statistics."""
    registry = GstRegistry()
    
    # Add events for multiple elements
    events = [
        create_proctime_event("elem1", 0.001),
        create_proctime_event("elem2", 0.002),
        create_proctime_event("elem1", 0.003),
    ]
    
    for event in events:
        registry.add_shark_event(event)
    
    all_stats = registry.get_all_processing_stats()
    assert len(all_stats) == 2, "Should have stats for 2 elements"
    assert "elem1" in all_stats, "Should have stats for elem1"
    assert "elem2" in all_stats, "Should have stats for elem2"
    
    # Check elem1 stats
    elem1_stats = all_stats["elem1"]
    assert elem1_stats['count'] == 2, "elem1 should have 2 events"
    assert elem1_stats['avg'] == 0.002, "elem1 should have correct average"


def test_no_processing_stats():
    """Test getting stats for element with no data."""
    registry = GstRegistry()
    
    stats = registry.get_element_processing_stats("nonexistent")
    assert stats is None, "Should return None for nonexistent element"
    
    all_stats = registry.get_all_processing_stats()
    assert len(all_stats) == 0, "Should return empty dict for no data"
