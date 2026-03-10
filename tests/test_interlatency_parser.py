"""
Unit tests for Interlatency Parser
"""

import pytest
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from parser.interlatency_parser import InterlatencyParser
from parser.base_parser import GstLogLineParser
from model.events import InterLatencyEvent


class TestInterlatencyParser:
    """Test cases for InterlatencyParser."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = InterlatencyParser()
        self.line_parser = GstLogLineParser()
    
    def test_can_handle_valid_interlatency_line(self):
        """Test parser can handle valid interlatency lines."""
        line_str = "0:00:00.109414140 16882 0x7c45040010c0 TRACE GST_TRACER :0:: interlatency, from_pad=(string)videotestsrc0_src, to_pad=(string)capsfilter0_src, time=(string)0:00:00.000010769;"
        log_line = self.line_parser.parse(line_str)
        
        assert self.parser.can_handle(log_line)
    
    def test_cannot_handle_non_tracer_line(self):
        """Test parser rejects non-GST_TRACER lines."""
        line_str = "0:00:00.109414140 16882 0x7c45040010c0 TRACE GST_DEBUG some debug message"
        log_line = self.line_parser.parse(line_str)
        
        assert not self.parser.can_handle(log_line)
    
    def test_cannot_handle_other_tracer_types(self):
        """Test parser rejects other tracer types."""
        line_str = "0:00:00.109414140 16882 0x7c45040010c0 TRACE GST_TRACER :0:: proctime, element=(string)test, time=(string)0:00:00.000001;"
        log_line = self.line_parser.parse(line_str)
        
        assert not self.parser.can_handle(log_line)
    
    def test_parse_valid_interlatency_line(self):
        """Test parsing of valid interlatency line."""
        line_str = "0:00:00.109414140 16882 0x7c45040010c0 TRACE GST_TRACER :0:: interlatency, from_pad=(string)videotestsrc0_src, to_pad=(string)capsfilter0_src, time=(string)0:00:00.000010769;"
        log_line = self.line_parser.parse(line_str)
        
        event = self.parser.parse_tracer_line(log_line)
        
        assert event is not None
        assert isinstance(event, InterLatencyEvent)
        assert event.src_element == "videotestsrc0"
        assert event.sink_element == "capsfilter0"
        assert event.latency == 0.000010769
        assert event.latency_str == "0:00:00.000010769"
        assert event.tracer_type == "interlatency"
    
    def test_parse_multiple_different_paths(self):
        """Test parsing of different pipeline paths."""
        test_cases = [
            ("appsrc_src", "sink_sink", "0:00:00.002201642", "appsrc", "sink"),
            ("videotestsrc0_src", "appsink_sink", "0:00:00.003225955", "videotestsrc0", "appsink"),
            ("gluploadelement0_src", "glcolorconvertelement0_src", "0:00:00.015502258", "gluploadelement0", "glcolorconvertelement0"),
        ]
        
        for src_pad, sink_pad, time_str, expected_src, expected_sink in test_cases:
            line_str = f"0:00:00.109414140 16882 0x7c45040010c0 TRACE GST_TRACER :0:: interlatency, from_pad=(string){src_pad}, to_pad=(string){sink_pad}, time=(string){time_str};"
            log_line = self.line_parser.parse(line_str)
            
            event = self.parser.parse_tracer_line(log_line)
            
            assert event is not None
            assert event.src_element == expected_src
            assert event.sink_element == expected_sink
    
    def test_extract_element_name_from_pad(self):
        """Test element name extraction from pad names."""
        test_cases = [
            ("videotestsrc0_src", "videotestsrc0"),
            ("appsink_sink", "appsink"),
            ("glcolorconvertelement0_src", "glcolorconvertelement0"),
            ("simpleelement", "simpleelement"),  # No suffix
        ]
        
        for pad_name, expected_element in test_cases:
            result = self.parser._extract_element_name(pad_name)
            assert result == expected_element
    
    def test_parse_time_string_valid_formats(self):
        """Test time string parsing for valid formats."""
        test_cases = [
            ("0:00:00.000010769", 0.000010769),
            ("0:00:01.123456789", 1.123456789),
            ("0:01:30.500000000", 90.5),
            ("1:00:00.000000000", 3600.0),
        ]
        
        for time_str, expected_seconds in test_cases:
            result = self.parser._parse_timestamp_seconds(time_str)
            assert result == expected_seconds
    
    def test_parse_time_string_invalid_formats(self):
        """Test time string parsing for invalid formats."""
        invalid_cases = [
            "invalid",
            "0:00:00",  # Missing microseconds
            "0:00",  # Missing seconds
            "0:00:00.000010769.123",  # Extra decimal
            "",  # Empty string
        ]
        
        for time_str in invalid_cases:
            result = self.parser._parse_timestamp_seconds(time_str)
            assert result is None
    
    def test_parse_malformed_line(self):
        """Test parsing of malformed interlatency lines."""
        malformed_lines = [
            "0:00:00.109414140 16882 0x7c45040010c0 TRACE GST_TRACER :0:: interlatency, from_pad=(string)videotestsrc0_src",  # Missing to_pad
            "0:00:00.109414140 16882 0x7c45040010c0 TRACE GST_TRACER :0:: interlatency, to_pad=(string)capsfilter0_src, time=(string)0:00:00.000010769;",  # Missing from_pad
            "0:00:00.109414140 16882 0x7c45040010c0 TRACE GST_TRACER :0:: interlatency, from_pad=(string)videotestsrc0_src, to_pad=(string)capsfilter0_src",  # Missing time
            "0:00:00.109414140 16882 0x7c45040010c0 TRACE GST_TRACER :0:: interlatency, from_pad=(string)videotestsrc0_src, to_pad=(string)capsfilter0_src, time=(string)invalid_time;",  # Invalid time
        ]
        
        for line_str in malformed_lines:
            log_line = self.line_parser.parse(line_str)
            event = self.parser.parse_tracer_line(log_line)
            assert event is None
    
    def test_edge_case_element_names(self):
        """Test parsing with unusual element names."""
        test_cases = [
            ("element-with-dashes_src", "element-with-dashes"),
            ("element123_src", "element123"),
            ("element_with_underscores_src", "element_with_underscores"),
            ("CamelCaseElement_src", "CamelCaseElement"),
        ]
        
        for pad_name, expected_element in test_cases:
            result = self.parser._extract_element_name(pad_name)
            assert result == expected_element
    
    def test_order_field_set_to_zero(self):
        """Test that order field is set to 0 for registry to set later."""
        line_str = "0:00:00.109414140 16882 0x7c45040010c0 TRACE GST_TRACER :0:: interlatency, from_pad=(string)videotestsrc0_src, to_pad=(string)capsfilter0_src, time=(string)0:00:00.000010769;"
        log_line = self.line_parser.parse(line_str)
        
        event = self.parser.parse_tracer_line(log_line)
        
        assert event is not None
        assert event.order == 0
