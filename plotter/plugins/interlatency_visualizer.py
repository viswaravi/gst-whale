"""
Interlatency Visualizer Plugin

Visualization plugin for interlatency tracer data.
"""

from __future__ import annotations

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
from typing import Dict, List, Any, Optional

from .base_visualizer import BaseVisualizer, visualizer_registry
from components.interlatency_plots import (
    InterlatencyTimeline, 
    PathStatisticsBarChart
)


class InterlatencyVisualizer(BaseVisualizer):
    """Visualizer for interlatency tracer data."""
    
    def __init__(self, tracer_type: str, data_provider):
        """Initialize interlatency visualizer."""
        super().__init__(tracer_type, data_provider)
        
        # Initialize plot components
        self.timeline = InterlatencyTimeline()
        self.stats_chart = PathStatisticsBarChart()
    
    def get_layout(self) -> dbc.Card:
        """Get the main layout for interlatency visualization."""
        return dbc.Card([
            dbc.CardBody([
                html.H4("Interlatency Analysis", className="card-title"),
                
                # Visualization tabs
                dbc.Tabs([
                    dbc.Tab(label="Timeline", tab_id="timeline"),
                    dbc.Tab(label="Path Statistics", tab_id="stats"),
                    dbc.Tab(label="End-to-End Summary", tab_id="summary")
                ], id="interlatency-tabs", active_tab="timeline"),
                
                # Tab content
                html.Div(id="interlatency-tab-content", className="mt-3"),
                
                # Export controls
                html.Hr(),
                html.Div([
                    html.H6("Export Data", className="text-muted"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Select(
                                id="interlatency-export-format",
                                options=[
                                    {"label": "CSV", "value": "csv"},
                                    {"label": "JSON", "value": "json"}
                                ],
                                value="csv",
                                size="sm"
                            )
                        ], width=4),
                        dbc.Col([
                            dbc.Button(
                                "Export",
                                id="interlatency-export-btn",
                                color="primary",
                                size="sm"
                            )
                        ], width=2),
                        dbc.Col([
                            html.Div(id="interlatency-export-status")
                        ], width=6)
                    ])
                ])
            ])
        ], className="mb-4")
    
    def register_callbacks(self, app: dash.Dash) -> None:
        """Register callbacks for interlatency visualizer."""
        
        @app.callback(
            Output("interlatency-tab-content", "children"),
            Input("interlatency-tabs", "active_tab"),
            State("path-dropdown", "value"),
            State("time-range-slider", "value"),
            State("viz-options", "value")
        )
        def update_tab_content(active_tab, selected_paths, time_range, viz_options):
            """Update tab content based on selected tab."""
            
            # Process path filter
            path_filter = self._process_path_filter(selected_paths)
            
            # Get data
            interlatency_df = self.data_provider.get_interlatency_data(
                path_filter=path_filter,
                start_time=time_range[0],
                end_time=time_range[1]
            )
            
            stats_df = self.data_provider.get_path_statistics(path_filter)
            
            if active_tab == "timeline":
                show_rolling = 'rolling' in viz_options
                timeline_fig = self.timeline.create_figure(interlatency_df, show_rolling)
                return dcc.Graph(figure=timeline_fig, style={'height': '500px'})
            
            elif active_tab == "stats":
                stats_fig = self.stats_chart.create_figure(stats_df)
                
                # Also create a data table for detailed statistics
                table = self._create_stats_table(stats_df)
                
                return dbc.Row([
                    dbc.Col([
                        dcc.Graph(figure=stats_fig, style={'height': '400px'})
                    ], width=8),
                    dbc.Col([
                        table
                    ], width=4)
                ])
            
            elif active_tab == "summary":
                return self._create_end_to_end_summary(interlatency_df, stats_df)
            
            return html.P("Select a tab to view data")
        
        @app.callback(
            Output("interlatency-export-status", "children"),
            Input("interlatency-export-btn", "n_clicks"),
            State("interlatency-export-format", "value"),
            State("path-dropdown", "value"),
            State("time-range-slider", "value"),
            prevent_initial_call=True
        )
        def export_data(n_clicks, export_format, selected_paths, time_range):
            """Export data in selected format."""
            if n_clicks is None:
                return ""
            
            try:
                path_filter = self._process_path_filter(selected_paths)
                
                # Get filtered data
                interlatency_df = self.data_provider.get_interlatency_data(
                    path_filter=path_filter,
                    start_time=time_range[0],
                    end_time=time_range[1]
                )
                
                if export_format == "csv":
                    csv_data = interlatency_df.to_csv(index=False)
                    return dbc.Alert("Data exported successfully!", color="success")
                elif export_format == "json":
                    json_data = interlatency_df.to_json(orient='records', indent=2)
                    return dbc.Alert("Data exported successfully!", color="success")
                
            except Exception as e:
                return dbc.Alert(f"Export failed: {str(e)}", color="danger")
    
    def get_filter_controls(self) -> List[Any]:
        """Get filter controls specific to interlatency visualizer."""
        return [
            html.H6("Interlatency Options", className="text-muted"),
            dbc.Checklist(
                id="interlatency-options",
                options=[
                    {"label": "Show Rolling Average", "value": "rolling"},
                    {"label": "Show Network Graph", "value": "network"},
                    {"label": "Percentile View", "value": "percentile"}
                ],
                value=[],
                inline=True
            )
        ]
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for interlatency data."""
        stats_df = self.data_provider.get_path_statistics()
        interlatency_df = self.data_provider.get_interlatency_data()
        paths = self.data_provider.get_pipeline_paths()
        
        if stats_df.empty:
            return {
                'tracer_type': self.tracer_type,
                'total_events': 0,
                'paths': 0,
                'time_range': (0.0, 0.0),
                'avg_latency': 0.0,
                'max_latency': 0.0
            }
        
        return {
            'tracer_type': self.tracer_type,
            'total_events': len(interlatency_df),
            'paths': len(paths),
            'time_range': (interlatency_df['timestamp'].min(), interlatency_df['timestamp'].max()),
            'avg_latency': stats_df['avg_latency_ms'].mean(),
            'max_latency': stats_df['max_latency_ms'].max(),
            'min_latency': stats_df['min_latency_ms'].min()
        }
    
    def get_data(self) -> pd.DataFrame:
        """Get raw interlatency data."""
        return self.data_provider.get_interlatency_data()
    
    def _process_path_filter(self, selected_paths) -> Optional[str]:
        """Process path filter from dropdown selection."""
        if not selected_paths:
            return None
        
        if isinstance(selected_paths, list):
            if len(selected_paths) == 0 or selected_paths == ['']:
                return None
            elif len(selected_paths) == 1:
                return selected_paths[0]
            else:
                return '|'.join(selected_paths)
        
        return selected_paths
    
    def _create_data_table(self, df: pd.DataFrame) -> html.Div:
        """Create data table for interlatency data."""
        if df.empty:
            return html.P("No data available")
        
        # Format for display
        display_df = df.copy()
        display_df['latency_ms'] = display_df['latency_ms'].round(3)
        display_df['timestamp'] = display_df['timestamp'].round(3)
        
        # Select and rename columns for display
        display_df = display_df[['timestamp', 'src_element', 'sink_element', 'latency_ms', 'path_id']]
        display_df.columns = ['Time', 'Source', 'Sink', 'Latency (ms)', 'Path']
        
        return dbc.Table.from_dataframe(
            display_df.head(100),  # Limit to first 100 rows for performance
            striped=True,
            bordered=True,
            hover=True,
            size="sm",
            className="mt-3"
        )
    
    def _create_stats_table(self, stats_df: pd.DataFrame) -> html.Div:
        """Create summary statistics table."""
        if stats_df.empty:
            return html.P("No statistics available")
        
        # Format for display
        display_df = stats_df.copy()
        display_df['avg_latency_ms'] = display_df['avg_latency_ms'].round(3)
        display_df['min_latency_ms'] = display_df['min_latency_ms'].round(3)
        display_df['max_latency_ms'] = display_df['max_latency_ms'].round(3)
        display_df['total_latency_ms'] = display_df['total_latency_ms'].round(3)
        
        # Select and rename columns
        display_df = display_df[['path_id', 'count', 'avg_latency_ms', 'min_latency_ms', 'max_latency_ms']]
        display_df.columns = ['Path', 'Count', 'Avg (ms)', 'Min (ms)', 'Max (ms)']
        
        return html.Div([
            html.H6("Path Summary", className="text-muted"),
            dbc.Table.from_dataframe(
                display_df,
                striped=True,
                bordered=True,
                hover=True,
                size="sm",
                className="mt-2"
            )
        ])
    
    def _create_end_to_end_summary(self, interlatency_df: pd.DataFrame, stats_df: pd.DataFrame) -> html.Div:
        """Create end-to-end latency summary for complete pipeline paths."""
        if stats_df.empty:
            return html.P("No data available for end-to-end analysis")
        
        # Define the 3 pipeline paths based on analysis
        pipeline_definitions = {
            "Input → Sink": ["videotestsrc0->capsfilter0", "videotestsrc0->appsink"],
            "Src → glimagesink": ["appsrc->gluploadelement0", "appsrc->glcolorconvertelement0", "appsrc->glcolorbalance0", "appsrc->sink"],
            "Src → Sink": ["appsrc->gluploadelement0", "appsrc->glcolorconvertelement0", "appsrc->glcolorbalance0", "appsrc->sink"]
        }
        
        # Calculate end-to-end latencies
        summary_data = []
        for pipeline_name, path_segments in pipeline_definitions.items():
            total_latency = 0.0
            hop_count = 0
            hop_details = []
            
            for segment in path_segments:
                segment_stats = stats_df[stats_df['path_id'] == segment]
                if not segment_stats.empty:
                    avg_latency = segment_stats.iloc[0]['avg_latency_ms']
                    total_latency += avg_latency
                    hop_count += 1
                    hop_details.append(f"{segment}: {avg_latency:.3f}ms")
            
            if hop_count > 0:
                summary_data.append({
                    'Pipeline': pipeline_name,
                    'Total Latency (ms)': round(total_latency, 3),
                    'Hop Count': hop_count,
                    'Details': ' + '.join(hop_details)
                })
        
        if not summary_data:
            return html.P("No complete pipeline paths found")
        
        summary_df = pd.DataFrame(summary_data)
        
        return html.Div([
            html.H6("End-to-End Pipeline Latency", className="text-muted"),
            html.P("Total accumulated latency for complete pipeline paths:", className="text-muted small"),
            dbc.Table.from_dataframe(
                summary_df,
                striped=True,
                bordered=True,
                hover=True,
                size="sm",
                className="mt-2"
            ),
            html.Hr(),
            html.H6("Pipeline Path Details", className="text-muted mt-4"),
            html.Div([
                html.P([
                    html.Strong(f"{row['Pipeline']}: "), 
                    f"{row['Details']}"
                ], className="small mb-2")
                for _, row in summary_df.iterrows()
            ])
        ])


# Register the visualizer
visualizer_registry.register('interlatency', InterlatencyVisualizer)
