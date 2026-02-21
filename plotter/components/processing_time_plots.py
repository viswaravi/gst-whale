"""
Processing Time Visualization Components

Specialized components for visualizing processing time data
from GStreamer tracer logs.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
from typing import List, Optional, Dict, Any
import dash
from dash import html
import random


class ProcessingTimeTimeline:
    """Interactive timeline component for processing time data."""
    
    def __init__(self, element_colors: Optional[Dict[str, str]] = None):
        """Initialize with optional color scheme."""
        # If custom colors provided, use them; otherwise use random colors
        if element_colors:
            self.element_colors = element_colors
            self.use_random_colors = False
        else:
            self.element_colors = {}
            self.use_random_colors = True
            # Use a diverse color palette for random selection
            self.color_palette = [
                '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
                '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
                '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
                '#f7cec6', '#dbdb8d', '#9edae5', '#addd8e', '#ff9f9c'
            ]
    
    def create_figure(self, df: pd.DataFrame, 
                     show_rolling_avg: bool = True,
                     window_size: int = 50,
                     visible_elements: Optional[List[str]] = None) -> go.Figure:
        """
        Create timeline visualization figure as line plot over time.
        
        Args:
            df: DataFrame with processing time data
            show_rolling_avg: Whether to show rolling average
            window_size: Rolling window size
            visible_elements: List of elements to show (None = show all)
            
        Returns:
            Plotly figure
        """
        if df.empty:
            return go.Figure().add_annotation(
                text="No data available", 
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
        
        fig = go.Figure()
        
        # Get all unique elements and filter if needed
        all_elements = sorted(df['element_name'].unique())
        if visible_elements is None:
            visible_elements = all_elements
        
        # Generate random colors for elements if needed
        if self.use_random_colors:
            random.shuffle(self.color_palette)
            for i, element in enumerate(all_elements):
                if element not in self.element_colors:
                    self.element_colors[element] = self.color_palette[i % len(self.color_palette)]
        
        # Group by element and create line plots
        for i, element in enumerate(all_elements):
            element_df = df[df['element_name'] == element].copy()
            
            # Sort by timestamp
            element_df = element_df.sort_values('timestamp')
            
            # Determine visibility
            is_visible = element in visible_elements
            
            # Get color for this element
            element_color = self.element_colors.get(element, self.color_palette[i % len(self.color_palette)])
            
            # Add rolling average line (primary visualization)
            if show_rolling_avg and len(element_df) >= window_size:
                element_df['rolling_avg'] = element_df['processing_time_ms'].rolling(
                    window=window_size, center=True
                ).mean()
                
                fig.add_trace(go.Scatter(
                    x=element_df['timestamp'],
                    y=element_df['rolling_avg'],
                    mode='lines',
                    name=f'{element}',
                    line=dict(
                        width=2,
                        color=element_color
                    ),
                    visible=is_visible,
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                 'Time: %{x:.3f}s<br>' +
                                 'Rolling Avg: %{y:.3f}ms<extra></extra>'
                ))
            else:
                # If no rolling average, show raw data as line
                fig.add_trace(go.Scatter(
                    x=element_df['timestamp'],
                    y=element_df['processing_time_ms'],
                    mode='lines',
                    name=f'{element}',
                    line=dict(
                        width=1,
                        color=element_color
                    ),
                    visible=is_visible,
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                 'Time: %{x:.3f}s<br>' +
                                 'Processing Time: %{y:.3f}ms<extra></extra>'
                ))
        
        fig.update_layout(
            title="Processing Time Timeline",
            xaxis_title="Timestamp (seconds)",
            yaxis_title="Processing Time (ms)",
            hovermode='x unified',
            legend=dict(
                x=0, y=1, 
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='gray',
                borderwidth=1
            ),
            showlegend=True,
            height=500
        )
        
        # Add range slider for time navigation
        fig.update_layout(
            xaxis=dict(
                rangeslider=dict(visible=True, thickness=0.05),
                type="linear"
            )
        )
        
        return fig
    
    def create_element_controls(self, df: pd.DataFrame) -> List[Any]:
        """
        Create element visibility controls.
        
        Args:
            df: DataFrame with processing time data
            
        Returns:
            List of Dash components for element controls
        """
        if df.empty:
            return []
        
        elements = sorted(df['element_name'].unique())
        
        return [
            html.H6("Element Visibility", className="text-muted"),
            dbc.Checklist(
                id="element-visibility-checklist",
                options=[
                    {"label": elem, "value": elem}
                    for elem in elements
                ],
                value=elements,  # All visible by default
                inline=True
            )
        ]


class ProcessingTimeStats:
    """Statistics visualization component for processing time data."""
    
    def create_bar_chart(self, df: pd.DataFrame) -> go.Figure:
        """Create bar chart showing average processing times."""
        if df.empty:
            return go.Figure().add_annotation(
                text="No data available", 
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
        
        fig = go.Figure()
        
        # Add average processing time bars
        fig.add_trace(go.Bar(
            x=df['element_name'],
            y=df['avg_time_ms'],
            name='Average Time',
            marker_color='lightblue',
            hovertemplate='<b>%{x}</b><br>' +
                         'Avg Time: %{y:.3f}ms<br>' +
                         'Count: %{customdata}<extra></extra>',
            customdata=df['count']
        ))
        
        # Add error bars for min/max range
        fig.add_trace(go.Bar(
            x=df['element_name'],
            y=df['max_time_ms'] - df['min_time_ms'],
            base=df['min_time_ms'],
            name='Min-Max Range',
            marker_color='lightcoral',
            opacity=0.6,
            hovertemplate='<b>%{x}</b><br>' +
                         'Range: %{base:.3f}ms - %{y:.3f}ms<extra></extra>'
        ))
        
        fig.update_layout(
            title="Processing Time Statistics by Element",
            xaxis_title="Element",
            yaxis_title="Processing Time (ms)",
            barmode='overlay',
            showlegend=True,
            height=400
        )
        
        return fig
    
    def create_box_plot(self, df: pd.DataFrame) -> go.Figure:
        """Create box plot for processing time distribution."""
        if df.empty:
            return go.Figure().add_annotation(
                text="No data available", 
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
        
        # Create box plot data
        box_data = []
        element_names = []
        
        for element in df['element_name'].unique():
            element_df = df[df['element_name'] == element]
            box_data.append(element_df['processing_time_ms'])
            element_names.append(element)
        
        fig = go.Figure()
        
        fig.add_trace(go.Box(
            x=element_names,
            y=box_data,
            name='Processing Time Distribution',
            boxpoints='outliers',
            jitter=0.3,
            pointpos=-1.8,
            hovertemplate='<b>%{x}</b><br>' +
                         'Median: %{median:.3f}ms<br>' +
                         'Q1: %{q1:.3f}ms<br>' +
                         'Q3: %{q3:.3f}ms<extra></extra>'
        ))
        
        fig.update_layout(
            title="Processing Time Distribution",
            xaxis_title="Element",
            yaxis_title="Processing Time (ms)",
            height=400
        )
        
        return fig


class ProcessingTimeHeatmap:
    """Heatmap component for processing time patterns."""
    
    def create_heatmap(self, df: pd.DataFrame, 
                      time_bins: int = 50,
                      element_order: Optional[List[str]] = None) -> go.Figure:
        """
        Create heatmap showing processing time intensity over time.
        
        Args:
            df: DataFrame with processing time data
            time_bins: Number of time bins for heatmap
            element_order: Order of elements (optional)
            
        Returns:
            Plotly figure
        """
        if df.empty:
            return go.Figure().add_annotation(
                text="No data available", 
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
        
        # Create time bins
        time_min, time_max = df['timestamp'].min(), df['timestamp'].max()
        time_edges = pd.cut(df['timestamp'], bins=time_bins, retbins=True)[1]
        time_centers = (time_edges[:-1] + time_edges[1:]) / 2
        
        # Create element order
        if element_order is None:
            element_order = sorted(df['element_name'].unique())
        
        # Create heatmap matrix
        heatmap_data = []
        for element in element_order:
            element_df = df[df['element_name'] == element]
            
            # Bin the data
            element_hist, _ = pd.cut(element_df['timestamp'], 
                                   bins=time_edges, 
                                   include_lowest=True, 
                                   retbins=True)
            element_binned = element_df.groupby(element_hist)['processing_time_ms'].mean()
            
            # Fill missing bins with 0
            element_series = pd.Series(0, index=pd.IntervalIndex.from_arrays(time_edges[:-1], time_edges[1:]))
            element_series.loc[element_binned.index] = element_binned.values
            
            heatmap_data.append(element_series.values)
        
        fig = go.Figure()
        
        fig.add_trace(go.Heatmap(
            x=time_centers,
            y=element_order,
            z=heatmap_data,
            colorscale='Viridis',
            hovertemplate='Time: %{x:.3f}s<br>' +
                         'Element: %{y}<br>' +
                         'Avg Time: %{z:.3f}ms<extra></extra>',
            colorbar=dict(title="Avg Processing Time (ms)")
        ))
        
        fig.update_layout(
            title="Processing Time Heatmap",
            xaxis_title="Timestamp (seconds)",
            yaxis_title="Element",
            height=400
        )
        
        return fig
