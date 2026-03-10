"""
Unit tests for Interlatency Data Provider functionality
"""

import pytest
import sys
import os
import pandas as pd

# Add src and plotter to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'plotter'))

from data_provider import GstDataProvider
from registry.gst_registry import GstRegistry
from model.events import InterLatencyEvent


class TestInterlatencyDataProvider:
    """Test cases for interlatency data provider functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.registry = GstRegistry()
        self.data_provider = GstDataProvider(self.registry)
        
        # Add test interlatency events
        self._add_test_events()
    
    def _add_test_events(self):
        """Add test interlatency events to registry."""
        test_events = [
            InterLatencyEvent(
                ts=0.1,
                link_key=("videotestsrc0", "capsfilter0"),
                order=1,
                tracer_type="interlatency",
                element_name="videotestsrc0",
                latency=0.000010769,
                latency_str="0:00:00.000010769",
                src_element="videotestsrc0",
                sink_element="capsfilter0"
            ),
            InterLatencyEvent(
                ts=0.2,
                link_key=("videotestsrc0", "appsink"),
                order=2,
                tracer_type="interlatency",
                element_name="videotestsrc0",
                latency=0.003225955,
                latency_str="0:00:00.003225955",
                src_element="videotestsrc0",
                sink_element="appsink"
            ),
            InterLatencyEvent(
                ts=0.3,
                link_key=("appsrc", "sink"),
                order=3,
                tracer_type="interlatency",
                element_name="appsrc",
                latency=0.002201642,
                latency_str="0:00:00.002201642",
                src_element="appsrc",
                sink_element="sink"
            ),
        ]
        
        for event in test_events:
            self.registry.add_shark_event(event)
    
    def test_get_interlatency_data_basic(self):
        """Test basic interlatency data extraction."""
        df = self.data_provider.get_interlatency_data()
        
        assert not df.empty
        assert len(df) == 3
        assert 'timestamp' in df.columns
        assert 'src_element' in df.columns
        assert 'sink_element' in df.columns
        assert 'latency_ms' in df.columns
        assert 'path_id' in df.columns
        
        # Check latency conversion to ms
        assert df.iloc[0]['latency_ms'] == 0.000010769 * 1000
    
    def test_get_interlatency_data_with_element_filter(self):
        """Test interlatency data with element filter."""
        df = self.data_provider.get_interlatency_data(element_filter="videotestsrc0")
        
        assert len(df) == 2  # Two events with videotestsrc0
        assert all(df['src_element'] == "videotestsrc0")
    
    def test_get_interlatency_data_with_source_filter(self):
        """Test interlatency data with source filter."""
        df = self.data_provider.get_interlatency_data(source_filter="appsrc")
        
        assert len(df) == 1  # One event from appsrc
        assert df.iloc[0]['src_element'] == "appsrc"
    
    def test_get_interlatency_data_with_sink_filter(self):
        """Test interlatency data with sink filter."""
        df = self.data_provider.get_interlatency_data(sink_filter="sink")
        
        assert len(df) == 2  # Two events with "sink" in sink element name
        assert all("sink" in str(elem) for elem in df['sink_element'])
    
    def test_get_interlatency_data_with_path_filter(self):
        """Test interlatency data with path filter."""
        df = self.data_provider.get_interlatency_data(path_filter="videotestsrc0->capsfilter0")
        
        assert len(df) == 1  # One matching path
        assert df.iloc[0]['path_id'] == "videotestsrc0->capsfilter0"
    
    def test_get_interlatency_data_with_time_filter(self):
        """Test interlatency data with time range filter."""
        df = self.data_provider.get_interlatency_data(start_time=0.15, end_time=0.25)
        
        assert len(df) == 1  # Only event at ts=0.2
        assert df.iloc[0]['timestamp'] == 0.2
    
    def test_get_pipeline_paths(self):
        """Test pipeline path extraction."""
        paths = self.data_provider.get_pipeline_paths()
        
        assert len(paths) == 3
        assert "videotestsrc0->capsfilter0" in paths
        assert "videotestsrc0->appsink" in paths
        assert "appsrc->sink" in paths
        assert paths == sorted(paths)  # Should be sorted
    
    def test_get_path_statistics(self):
        """Test path statistics computation."""
        stats_df = self.data_provider.get_path_statistics()
        
        assert not stats_df.empty
        assert len(stats_df) == 3
        
        # Check required columns
        required_columns = ['path_id', 'count', 'avg_latency_ms', 'min_latency_ms', 'max_latency_ms', 'std_latency_ms']
        for col in required_columns:
            assert col in stats_df.columns
        
        # Check specific path statistics
        videotestsrc0_capsfilter0_stats = stats_df[stats_df['path_id'] == 'videotestsrc0->capsfilter0']
        assert len(videotestsrc0_capsfilter0_stats) == 1
        assert videotestsrc0_capsfilter0_stats.iloc[0]['count'] == 1
        assert abs(videotestsrc0_capsfilter0_stats.iloc[0]['avg_latency_ms'] - 0.010769) < 0.001  # Allow for float precision
    
    def test_get_path_statistics_with_filter(self):
        """Test path statistics with filter."""
        stats_df = self.data_provider.get_path_statistics(path_filter="videotestsrc0")
        
        assert len(stats_df) == 2  # Two paths with videotestsrc0
        assert all(stats_df['path_id'].str.contains("videotestsrc0"))
    
    def test_get_event_summary_includes_interlatency(self):
        """Test event summary includes interlatency events."""
        summary = self.data_provider.get_event_summary()
        
        assert 'interlatency_events' in summary
        assert summary['interlatency_events'] == 3
        assert summary['total_events'] == 3
        assert summary['shark_events'] == 3
    
    def test_empty_registry_handling(self):
        """Test handling of empty registry."""
        empty_registry = GstRegistry()
        empty_provider = GstDataProvider(empty_registry)
        
        df = empty_provider.get_interlatency_data()
        assert df.empty
        
        paths = empty_provider.get_pipeline_paths()
        assert len(paths) == 0
        
        stats_df = empty_provider.get_path_statistics()
        assert stats_df.empty
    
    def test_path_id_format(self):
        """Test path ID format consistency."""
        df = self.data_provider.get_interlatency_data()
        
        for _, row in df.iterrows():
            expected_path_id = f"{row['src_element']}->{row['sink_element']}"
            assert row['path_id'] == expected_path_id
    
    def test_latency_conversion_to_milliseconds(self):
        """Test latency conversion to milliseconds."""
        df = self.data_provider.get_interlatency_data()
        
        for _, row in df.iterrows():
            expected_ms = row['latency_s'] * 1000
            assert abs(row['latency_ms'] - expected_ms) < 0.001  # Small tolerance for floating point
    
    def test_timestamp_sorting(self):
        """Test that data is sorted by timestamp."""
        df = self.data_provider.get_interlatency_data()
        
        timestamps = df['timestamp'].tolist()
        assert timestamps == sorted(timestamps)
    
    def test_multiple_events_same_path(self):
        """Test handling of multiple events on same path."""
        # Add another event on existing path
        additional_event = InterLatencyEvent(
            ts=0.4,
            link_key=("videotestsrc0", "capsfilter0"),
            order=4,
            tracer_type="interlatency",
            element_name="videotestsrc0",
            latency=0.000020000,
            latency_str="0:00:00.000020000",
            src_element="videotestsrc0",
            sink_element="capsfilter0"
        )
        self.registry.add_shark_event(additional_event)
        
        df = self.data_provider.get_interlatency_data()
        videotestsrc0_capsfilter0_events = df[df['path_id'] == 'videotestsrc0->capsfilter0']
        
        assert len(videotestsrc0_capsfilter0_events) == 2
        
        stats_df = self.data_provider.get_path_statistics()
        path_stats = stats_df[stats_df['path_id'] == 'videotestsrc0->capsfilter0']
        assert path_stats.iloc[0]['count'] == 2
