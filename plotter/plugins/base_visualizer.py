"""
Base Visualizer Plugin

Abstract base class for tracer visualization plugins.
Provides a common interface for different tracer types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd

from data_provider import GstDataProvider


class BaseVisualizer(ABC):
    """Abstract base class for tracer visualizers."""
    
    def __init__(self, tracer_type: str, data_provider: GstDataProvider):
        """
        Initialize visualizer.
        
        Args:
            tracer_type: Type of tracer (e.g., 'proctime', 'interlatency')
            data_provider: Data provider instance
        """
        self.tracer_type = tracer_type
        self.data_provider = data_provider
    
    @abstractmethod
    def get_layout(self) -> dbc.Card:
        """
        Get the main layout component for this visualizer.
        
        Returns:
            Dash Bootstrap Card component
        """
        pass
    
    @abstractmethod
    def register_callbacks(self, app: dash.Dash) -> None:
        """
        Register Dash callbacks for this visualizer.
        
        Args:
            app: Dash application instance
        """
        pass
    
    @abstractmethod
    def get_filter_controls(self) -> List[Any]:
        """
        Get filter controls specific to this visualizer.
        
        Returns:
            List of Dash components
        """
        pass
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics for this tracer type.
        
        Returns:
            Dictionary with summary statistics
        """
        return {
            'tracer_type': self.tracer_type,
            'total_events': 0,
            'elements': 0,
            'time_range': (0.0, 0.0)
        }
    
    def export_data(self, format: str = 'csv') -> str:
        """
        Export data in specified format.
        
        Args:
            format: Export format ('csv', 'json', 'excel')
            
        Returns:
            String representation of exported data
        """
        if format == 'csv':
            return self._export_csv()
        elif format == 'json':
            return self._export_json()
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def _export_csv(self) -> str:
        """Export data as CSV."""
        df = self.get_data()
        return df.to_csv(index=False)
    
    def _export_json(self) -> str:
        """Export data as JSON."""
        df = self.get_data()
        return df.to_json(orient='records', indent=2)
    
    @abstractmethod
    def get_data(self) -> pd.DataFrame:
        """
        Get the raw data for this visualizer.
        
        Returns:
            DataFrame with tracer-specific data
        """
        pass


class VisualizerRegistry:
    """Registry for managing visualizer plugins."""
    
    def __init__(self):
        """Initialize registry."""
        self._visualizers: Dict[str, type] = {}
    
    def register(self, tracer_type: str, visualizer_class: type) -> None:
        """
        Register a visualizer class.
        
        Args:
            tracer_type: Type of tracer
            visualizer_class: Visualizer class
        """
        if not issubclass(visualizer_class, BaseVisualizer):
            raise ValueError("Visualizer class must inherit from BaseVisualizer")
        
        self._visualizers[tracer_type] = visualizer_class
    
    def create_visualizer(self, tracer_type: str, data_provider: GstDataProvider) -> BaseVisualizer:
        """
        Create visualizer instance.
        
        Args:
            tracer_type: Type of tracer
            data_provider: Data provider instance
            
        Returns:
            Visualizer instance
        """
        if tracer_type not in self._visualizers:
            raise ValueError(f"No visualizer registered for tracer type: {tracer_type}")
        
        visualizer_class = self._visualizers[tracer_type]
        return visualizer_class(tracer_type, data_provider)
    
    def get_available_types(self) -> List[str]:
        """
        Get list of available tracer types.
        
        Returns:
            List of tracer type names
        """
        return list(self._visualizers.keys())


# Global registry instance
visualizer_registry = VisualizerRegistry()
