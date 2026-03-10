"""
Interlatency Visualization Components

Reusable plot components for interlatency tracer data visualization.
"""

from __future__ import annotations

import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
from typing import List, Optional


class InterlatencyTimeline:
    """Timeline plot for interlatency data over time."""
    
    def create_figure(self, df: pd.DataFrame, show_rolling: bool = False) -> go.Figure:
        """
        Create timeline plot of interlatency data.
        
        Args:
            df: DataFrame with interlatency data
            show_rolling: Whether to show rolling average
            
        Returns:
            Plotly figure
        """
        if df.empty:
            return go.Figure().add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        fig = go.Figure()
        
        # Group by path for different colors
        for path_id, path_data in df.groupby('path_id'):
            # Add raw data points
            fig.add_trace(go.Scatter(
                x=path_data['timestamp'],
                y=path_data['latency_ms'],
                mode='markers',
                name=f'{path_id} (raw)',
                marker=dict(size=4, opacity=0.7),
                hovertemplate='<b>%{fullData.name}</b><br>' +
                            'Time: %{x:.3f}s<br>' +
                            'Latency: %{y:.3f}ms<br>' +
                            '<extra></extra>'
            ))
            
            # Add rolling average if requested
            if show_rolling and len(path_data) > 1:
                rolling_avg = path_data['latency_ms'].rolling(window=10, min_periods=1).mean()
                fig.add_trace(go.Scatter(
                    x=path_data['timestamp'],
                    y=rolling_avg,
                    mode='lines',
                    name=f'{path_id} (avg)',
                    line=dict(width=2),
                    hovertemplate='<b>%{fullData.name}</b><br>' +
                                'Time: %{x:.3f}s<br>' +
                                'Avg Latency: %{y:.3f}ms<br>' +
                                '<extra></extra>'
                ))
        
        fig.update_layout(
            title="Interlatency Timeline",
            xaxis_title="Time (seconds)",
            yaxis_title="Latency (ms)",
            hovermode='closest',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            annotations=[
                dict(
                    text="Raw = individual measurements | Avg = rolling average (10 samples)",
                    showarrow=False,
                    xref="paper", yref="paper",
                    x=0.5, y=-0.08,
                    xanchor='center', yanchor='top',
                    font=dict(size=10, color='gray')
                )
            ]
        )
        
        return fig


class PathStatisticsBarChart:
    """Bar chart for path statistics comparison."""
    
    def create_figure(self, stats_df: pd.DataFrame) -> go.Figure:
        """
        Create bar chart of path statistics.
        
        Args:
            stats_df: DataFrame with path statistics
            
        Returns:
            Plotly figure
        """
        if stats_df.empty:
            return go.Figure().add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        fig = go.Figure()
        
        # Add average latency bars
        fig.add_trace(go.Bar(
            x=stats_df['path_id'],
            y=stats_df['avg_latency_ms'],
            name='Average Latency',
            marker_color='lightblue',
            hovertemplate='<b>%{x}</b><br>' +
                        'Avg Latency: %{y:.3f}ms<br>' +
                        '<extra></extra>'
        ))
        
        # Add min/max as error bars
        fig.add_trace(go.Scatter(
            x=stats_df['path_id'],
            y=stats_df['min_latency_ms'],
            mode='markers',
            name='Min Latency',
            marker=dict(color='green', size=8, symbol='triangle-down'),
            hovertemplate='<b>%{x}</b><br>' +
                        'Min Latency: %{y:.3f}ms<br>' +
                        '<extra></extra>'
        ))
        
        fig.add_trace(go.Scatter(
            x=stats_df['path_id'],
            y=stats_df['max_latency_ms'],
            mode='markers',
            name='Max Latency',
            marker=dict(color='red', size=8, symbol='triangle-up'),
            hovertemplate='<b>%{x}</b><br>' +
                        'Max Latency: %{y:.3f}ms<br>' +
                        '<extra></extra>'
        ))
        
        fig.update_layout(
            title="Pipeline Path Statistics",
            xaxis_title="Pipeline Path (Source → Sink)",
            yaxis_title="Latency (ms)",
            hovermode='closest',
            xaxis_tickangle=-45
        )
        
        return fig
