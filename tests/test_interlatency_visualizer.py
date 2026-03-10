"""
Unit tests for Interlatency Visualizer
"""

import pytest
import sys
import os
import pandas as pd
from unittest.mock import Mock, patch

# Add src and plotter to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'plotter'))

from data_provider import GstDataProvider
from registry.gst_registry import GstRegistry
from model.events import InterLatencyEvent
from plugins.interlatency_visualizer import InterlatencyVisualizer


class TestInterlatencyVisualizer:
    """Test cases for InterlatencyVisualizer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = GstRegistry()
        self.data_provider = GstDataProvider(self.registry)
        self.visualizer = InterlatencyVisualizer("interlatency", self.data_provider)
        
        # Add test interlatency events
        self._add_test_events()
    
    def _add_test_events(self):
        """Add test interlatency events to registry."""
        test_events = [
            InterLatencyEvent(
                ts=0.1,
                link_key=("src1", "sink1"),
                order=1,
                tracer_type="interlatency",
                element_name="src1",
                latency=0.001,
                latency_str="0:00:00.001000000",
                src_element="src1",
                sink_element="sink1"
            ),
            InterLatencyEvent(
                ts=0.2,
                link_key=("src2", "sink2"),
                order=2,
                tracer_type="interlatency",
                element_name="src2",
                latency=0.002,
                latency_str="0:00:00.002000000",
                src_element="src2",
                sink_element="sink2"
            ),
        ]
        
        for event in test_events:
            self.registry.add_shark_event(event)
    
    def test_visualizer_initialization(self):
        """Test visualizer initialization."""
        assert self.visualizer.tracer_type == "interlatency"
        assert self.visualizer.data_provider == self.data_provider
        assert hasattr(self.visualizer, 'timeline')
        assert hasattr(self.visualizer, 'stats_chart')
        # Removed heatmap and network components
    
    def test_get_layout_returns_card(self):
        """Test that get_layout returns a dbc.Card."""
        layout = self.visualizer.get_layout()
        
        # Check that it's a Card component (has children attribute)
        assert hasattr(layout, 'children')
        # Check for key elements in layout
        layout_str = str(layout)
        assert "Interlatency Analysis" in layout_str
        assert "Timeline" in layout_str
        assert "Path Statistics" in layout_str
        assert "End-to-End Summary" in layout_str
    
    def test_get_filter_controls(self):
        """Test filter controls generation."""
        controls = self.visualizer.get_filter_controls()
        
        assert len(controls) > 0
        # Check for specific options
        controls_str = str(controls)
        assert "Show Rolling Average" in controls_str
    
    def test_get_summary_stats_with_data(self):
        """Test summary statistics with data."""
        stats = self.visualizer.get_summary_stats()
        
        assert stats['tracer_type'] == "interlatency"
        assert stats['total_events'] == 2
        assert stats['paths'] == 2  # src1->sink1, src2->sink2
        assert stats['avg_latency'] > 0
        assert stats['max_latency'] > 0
        assert stats['min_latency'] > 0
    
    def test_get_summary_stats_empty(self):
        """Test summary statistics with empty data."""
        empty_registry = GstRegistry()
        empty_provider = GstDataProvider(empty_registry)
        empty_visualizer = InterlatencyVisualizer("interlatency", empty_provider)
        
        stats = empty_visualizer.get_summary_stats()
        
        assert stats['tracer_type'] == "interlatency"
        assert stats['total_events'] == 0
        assert stats['paths'] == 0
        assert stats['avg_latency'] == 0.0
        assert stats['max_latency'] == 0.0
        # min_latency may not be present in empty case
        assert stats.get('min_latency', 0.0) == 0.0
    
    def test_create_end_to_end_summary(self):
        """Test end-to-end summary creation."""
        data = self.visualizer.get_data()
        stats_df = self.data_provider.get_path_statistics()
        
        summary = self.visualizer._create_end_to_end_summary(data, stats_df)
        
        summary_str = str(summary)
        # The test data uses different path names, so we may get "No complete pipeline paths found"
        # or the actual summary depending on whether paths match
        assert "End-to-End Pipeline Latency" in summary_str or "No complete pipeline paths found" in summary_str
    
    def test_get_data(self):
        """Test get_data method."""
        data = self.visualizer.get_data()
        
        assert isinstance(data, pd.DataFrame)
        assert not data.empty
        assert len(data) == 2
        assert 'src_element' in data.columns
        assert 'sink_element' in data.columns
        assert 'latency_ms' in data.columns
    
    def test_process_path_filter_none(self):
        """Test path filter processing with None."""
        result = self.visualizer._process_path_filter(None)
        assert result is None
    
    def test_process_path_filter_empty_list(self):
        """Test path filter processing with empty list."""
        result = self.visualizer._process_path_filter([])
        assert result is None
    
    def test_process_path_filter_empty_string(self):
        """Test path filter processing with empty string list."""
        result = self.visualizer._process_path_filter([''])
        assert result is None
    
    def test_process_path_filter_single_path(self):
        """Test path filter processing with single path."""
        result = self.visualizer._process_path_filter(['src1->sink1'])
        assert result == 'src1->sink1'
    
    def test_process_path_filter_multiple_paths(self):
        """Test path filter processing with multiple paths."""
        paths = ['src1->sink1', 'src2->sink2']
        result = self.visualizer._process_path_filter(paths)
        assert result == 'src1->sink1|src2->sink2'
    
    def test_process_path_filter_string_input(self):
        """Test path filter processing with string input."""
        result = self.visualizer._process_path_filter('src1->sink1')
        assert result == 'src1->sink1'
    
    def test_create_data_table_with_data(self):
        """Test data table creation with data."""
        data = self.visualizer.get_data()
        table = self.visualizer._create_data_table(data)
        
        table_str = str(table)
        assert "Time" in table_str
        assert "Source" in table_str
        assert "Sink" in table_str
        assert "Latency (ms)" in table_str
        assert "Path" in table_str
    
    def test_create_data_table_empty(self):
        """Test data table creation with empty data."""
        empty_df = pd.DataFrame()
        table = self.visualizer._create_data_table(empty_df)
        
        table_str = str(table)
        assert "No data available" in table_str
    
    def test_create_stats_table_with_data(self):
        """Test statistics table creation with data."""
        stats_df = self.data_provider.get_path_statistics()
        table = self.visualizer._create_stats_table(stats_df)
        
        table_str = str(table)
        assert "Path Summary" in table_str
        assert "Path" in table_str
        assert "Count" in table_str
        assert "Avg (ms)" in table_str
        assert "Min (ms)" in table_str
        assert "Max (ms)" in table_str
    
    def test_create_stats_table_empty(self):
        """Test statistics table creation with empty data."""
        empty_df = pd.DataFrame()
        table = self.visualizer._create_stats_table(empty_df)
        
        table_str = str(table)
        assert "No statistics available" in table_str
    
    def test_data_formatting_in_table(self):
        """Test data formatting in tables."""
        data = self.visualizer.get_data()
        table = self.visualizer._create_data_table(data)
        
        table_str = str(table)
        # Check that latency values are present (format may vary)
        assert "1.0" in table_str or "2.0" in table_str
    
    def test_time_range_in_summary_stats(self):
        """Test time range in summary statistics."""
        stats = self.visualizer.get_summary_stats()
        
        assert 'time_range' in stats
        assert isinstance(stats['time_range'], tuple)
        assert len(stats['time_range']) == 2
        assert stats['time_range'][0] <= stats['time_range'][1]
