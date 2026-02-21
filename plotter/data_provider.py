"""
Data Provider Module for GST-Whale Dashboard

This module extracts data from GstRegistry and formats it for visualization
in Plotly Dash components. Provides a clean interface between the parsing
logic and the visualization layer.
"""

from __future__ import annotations

import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

# Import existing gst-whale modules
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from registry.gst_registry import GstRegistry
from model.events import ProcTimeEvent, SharkTracerEvent


class GstDataProvider:
    """Data provider for GST-Whale dashboard visualizations."""
    
    def __init__(self, registry: GstRegistry):
        """Initialize with a populated GstRegistry."""
        self.registry = registry
    
    def get_processing_times_data(self, 
                                element_filter: Optional[str] = None,
                                start_time: Optional[float] = None,
                                end_time: Optional[float] = None) -> pd.DataFrame:
        """
        Extract processing time data as a pandas DataFrame.
        
        Args:
            element_filter: Filter by element name (partial match)
            start_time: Start timestamp filter
            end_time: End timestamp filter
            
        Returns:
            DataFrame with columns: timestamp, element_name, processing_time_ms
        """
        proc_time_events = [ev for ev in self.registry.shark_events 
                          if isinstance(ev, ProcTimeEvent)]
        
        # Apply filters
        if element_filter:
            proc_time_events = [ev for ev in proc_time_events 
                               if element_filter in ev.element_name]
        
        if start_time is not None:
            proc_time_events = [ev for ev in proc_time_events 
                               if ev.ts >= start_time]
        
        if end_time is not None:
            proc_time_events = [ev for ev in proc_time_events 
                             if ev.ts <= end_time]
        
        # Convert to DataFrame
        data = []
        for event in proc_time_events:
            data.append({
                'timestamp': event.ts,
                'element_name': event.element_name,
                'processing_time_ms': event.processing_time * 1000,  # Convert to ms
                'processing_time_s': event.processing_time,
                'order': event.order
            })
        
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values('timestamp')
        
        return df
    
    def get_element_statistics(self, element_filter: Optional[str] = None) -> pd.DataFrame:
        """
        Get summary statistics for each element.
        
        Args:
            element_filter: Filter by element name (partial match)
            
        Returns:
            DataFrame with statistics per element
        """
        stats = self.registry.get_all_processing_stats()
        
        # Apply element filter
        if element_filter:
            stats = {k: v for k, v in stats.items() 
                    if element_filter in k}
        
        data = []
        for element_name, element_stats in stats.items():
            data.append({
                'element_name': element_name,
                'count': element_stats['count'],
                'total_time_ms': element_stats['total'] * 1000,
                'avg_time_ms': element_stats['avg'] * 1000,
                'min_time_ms': element_stats['min'] * 1000,
                'max_time_ms': element_stats['max'] * 1000,
                'std_time_ms': self._calculate_std(element_name)
            })
        
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.sort_values('avg_time_ms', ascending=False)
        
        return df
    
    def get_timeline_data(self, 
                         element_filter: Optional[str] = None,
                         start_time: Optional[float] = None,
                         end_time: Optional[float] = None,
                         window_size: Optional[int] = None) -> pd.DataFrame:
        """
        Get timeline data with optional rolling window aggregation.
        
        Args:
            element_filter: Filter by element name
            start_time: Start timestamp filter
            end_time: End timestamp filter
            window_size: Rolling window size for smoothing
            
        Returns:
            DataFrame with timeline data
        """
        df = self.get_processing_times_data(element_filter, start_time, end_time)
        
        if df.empty:
            return df
        
        if window_size and window_size > 1:
            df['rolling_avg_ms'] = (df.groupby('element_name')['processing_time_ms']
                                   .rolling(window=window_size)
                                   .mean()
                                   .reset_index(0, drop=True))
            df['rolling_std_ms'] = (df.groupby('element_name')['processing_time_ms']
                                   .rolling(window=window_size)
                                   .std()
                                   .reset_index(0, drop=True))
        
        return df
    
    def get_element_list(self) -> List[str]:
        """Get list of all element names in the registry."""
        return sorted(self.registry.elements.keys())
    
    def get_time_range(self) -> Tuple[float, float]:
        """Get the time range of all events."""
        if not self.registry.events:
            return (0.0, 0.0)
        
        timestamps = [ev.ts for ev in self.registry.events]
        return (min(timestamps), max(timestamps))
    
    def get_event_summary(self) -> Dict[str, int]:
        """Get summary counts of different event types."""
        summary = {
            'total_events': len(self.registry.events),
            'shark_events': len(self.registry.shark_events),
            'proctime_events': len([ev for ev in self.registry.shark_events 
                                  if isinstance(ev, ProcTimeEvent)]),
            'elements': len(self.registry.elements),
            'pads': len(self.registry.pads),
            'links': len(self.registry.links)
        }
        return summary
    
    def _calculate_std(self, element_name: str) -> float:
        """Calculate standard deviation for an element's processing times."""
        times = self.registry.element_processing_times.get(element_name, [])
        if len(times) < 2:
            return 0.0
        
        mean = sum(times) / len(times)
        variance = sum((t - mean) ** 2 for t in times) / len(times)
        return variance ** 0.5 * 1000  # Convert to ms
    
    @staticmethod
    def create_from_log_file(log_file: str, 
                           enable_debug: bool = False,
                           enable_tracer: bool = True,
                           verbose: bool = False) -> GstDataProvider:
        """
        Create a GstDataProvider by parsing a log file.
        
        Args:
            log_file: Path to the log file
            enable_debug: Enable debug parsing
            enable_tracer: Enable tracer parsing
            verbose: Verbose output
            
        Returns:
            GstDataProvider with populated registry
        """
        from parser.base_parser import GstLogLineParser
        from utils.log_reader import LogReader
        
        # Create shared objects
        line_parser = GstLogLineParser()
        registry = GstRegistry()
        reader = LogReader(log_file)
        
        # Process file line by line
        for raw_line in reader.lines():
            log_line = line_parser.parse(raw_line)
            if log_line is None:
                continue
            
            # Route based on domain and enabled flags
            if log_line.domain == "GST_DEBUG" and enable_debug:
                from debugTracer import parse_debug_line
                parse_debug_line(log_line, registry, verbose)
            elif log_line.domain == "GST_TRACER" and enable_tracer:
                from sharkTracer import parse_tracer_line
                parse_tracer_line(log_line, registry, verbose)
        
        registry.finalize()
        
        return GstDataProvider(registry)
