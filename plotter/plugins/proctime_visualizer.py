"""
Proctime Visualizer Plugin

Visualization plugin for processing time tracer data.
"""

from __future__ import annotations

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
from typing import Dict, List, Any, Optional

from .base_visualizer import BaseVisualizer, visualizer_registry
from components.processing_time_plots import (
    ProcessingTimeTimeline, 
    ProcessingTimeStats, 
    ProcessingTimeHeatmap
)


class ProctimeVisualizer(BaseVisualizer):
    """Visualizer for processing time tracer data."""
    
    def __init__(self, tracer_type: str, data_provider):
        """Initialize proctime visualizer."""
        super().__init__(tracer_type, data_provider)
        
        # Initialize plot components
        self.timeline = ProcessingTimeTimeline()
        self.stats = ProcessingTimeStats()
        self.heatmap = ProcessingTimeHeatmap()
    
    def get_layout(self) -> dbc.Card:
        """Get the main layout for proctime visualization."""
        return dbc.Card([
            dbc.CardBody([
                html.H4("Processing Time Analysis", className="card-title"),
                
                # Visualization tabs
                dbc.Tabs([
                    dbc.Tab(label="Timeline", tab_id="timeline"),
                    dbc.Tab(label="Statistics", tab_id="stats"),
                    dbc.Tab(label="Heatmap", tab_id="heatmap"),
                    dbc.Tab(label="Data Table", tab_id="table")
                ], id="proctime-tabs", active_tab="timeline"),
                
                # Tab content
                html.Div(id="proctime-tab-content", className="mt-3"),
                
                # Export controls
                html.Hr(),
                html.Div([
                    html.H6("Export Data", className="text-muted"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Select(
                                id="proctime-export-format",
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
                                id="proctime-export-btn",
                                color="primary",
                                size="sm"
                            )
                        ], width=2),
                        dbc.Col([
                            html.Div(id="proctime-export-status")
                        ], width=6)
                    ])
                ])
            ])
        ], className="mb-4")
    
    def register_callbacks(self, app: dash.Dash) -> None:
        """Register callbacks for proctime visualizer."""
        
        @app.callback(
            Output("proctime-tab-content", "children"),
            Input("proctime-tabs", "active_tab"),
            State("element-dropdown", "value"),
            State("time-range-slider", "value"),
            State("viz-options", "value")
        )
        def update_tab_content(active_tab, selected_elements, time_range, viz_options):
            """Update tab content based on selected tab."""
            
            # Process element filter
            element_filter = self._process_element_filter(selected_elements)
            
            # Get data
            timeline_df = self.data_provider.get_timeline_data(
                element_filter=element_filter,
                start_time=time_range[0],
                end_time=time_range[1]
            )
            
            stats_df = self.data_provider.get_element_statistics(element_filter)
            
            if active_tab == "timeline":
                show_rolling = 'rolling' in viz_options
                timeline_fig = self.timeline.create_figure(timeline_df, show_rolling)
                return dcc.Graph(figure=timeline_fig, style={'height': '500px'})
            
            elif active_tab == "stats":
                stats_fig = self.stats.create_bar_chart(stats_df)
                box_fig = self.stats.create_box_plot(timeline_df)
                
                return dbc.Row([
                    dbc.Col([
                        dcc.Graph(figure=stats_fig, style={'height': '400px'})
                    ], width=6),
                    dbc.Col([
                        dcc.Graph(figure=box_fig, style={'height': '400px'})
                    ], width=6)
                ])
            
            elif active_tab == "heatmap":
                heatmap_fig = self.heatmap.create_heatmap(timeline_df)
                return dcc.Graph(figure=heatmap_fig, style={'height': '400px'})
            
            elif active_tab == "table":
                return self._create_data_table(stats_df)
            
            return html.P("Select a tab to view data")
        
        @app.callback(
            Output("proctime-export-status", "children"),
            Input("proctime-export-btn", "n_clicks"),
            State("proctime-export-format", "value"),
            State("element-dropdown", "value"),
            State("time-range-slider", "value"),
            prevent_initial_call=True
        )
        def export_data(n_clicks, export_format, selected_elements, time_range):
            """Export data in selected format."""
            if n_clicks is None:
                return ""
            
            try:
                element_filter = self._process_element_filter(selected_elements)
                
                # Get filtered data
                timeline_df = self.data_provider.get_timeline_data(
                    element_filter=element_filter,
                    start_time=time_range[0],
                    end_time=time_range[1]
                )
                
                if export_format == "csv":
                    csv_data = timeline_df.to_csv(index=False)
                    return dbc.Alert("Data exported successfully!", color="success")
                elif export_format == "json":
                    json_data = timeline_df.to_json(orient='records', indent=2)
                    return dbc.Alert("Data exported successfully!", color="success")
                
            except Exception as e:
                return dbc.Alert(f"Export failed: {str(e)}", color="danger")
    
    def get_filter_controls(self) -> List[Any]:
        """Get filter controls specific to proctime visualizer."""
        return [
            html.H6("Proctime Options", className="text-muted"),
            dbc.Checklist(
                id="proctime-options",
                options=[
                    {"label": "Show Outliers", "value": "outliers"},
                    {"label": "Log Scale", "value": "log"},
                    {"label": "Percentile View", "value": "percentile"}
                ],
                value=[],
                inline=True
            )
        ]
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for proctime data."""
        stats_df = self.data_provider.get_element_statistics()
        timeline_df = self.data_provider.get_timeline_data()
        
        if stats_df.empty:
            return {
                'tracer_type': self.tracer_type,
                'total_events': 0,
                'elements': 0,
                'time_range': (0.0, 0.0),
                'avg_processing_time': 0.0,
                'max_processing_time': 0.0
            }
        
        return {
            'tracer_type': self.tracer_type,
            'total_events': len(timeline_df),
            'elements': len(stats_df),
            'time_range': (timeline_df['timestamp'].min(), timeline_df['timestamp'].max()),
            'avg_processing_time': stats_df['avg_time_ms'].mean(),
            'max_processing_time': stats_df['max_time_ms'].max(),
            'min_processing_time': stats_df['min_time_ms'].min()
        }
    
    def get_data(self) -> pd.DataFrame:
        """Get raw proctime data."""
        return self.data_provider.get_timeline_data()
    
    def _process_element_filter(self, selected_elements) -> Optional[str]:
        """Process element filter from dropdown selection."""
        if not selected_elements:
            return None
        
        if isinstance(selected_elements, list):
            if len(selected_elements) == 0 or selected_elements == ['']:
                return None
            elif len(selected_elements) == 1:
                return selected_elements[0]
            else:
                return '|'.join(selected_elements)
        
        return selected_elements
    
    def _create_data_table(self, stats_df: pd.DataFrame) -> html.Div:
        """Create data table for statistics."""
        if stats_df.empty:
            return html.P("No data available")
        
        # Format for display
        display_df = stats_df.copy()
        display_df['avg_time_ms'] = display_df['avg_time_ms'].round(3)
        display_df['min_time_ms'] = display_df['min_time_ms'].round(3)
        display_df['max_time_ms'] = display_df['max_time_ms'].round(3)
        display_df['std_time_ms'] = display_df['std_time_ms'].round(3)
        
        display_df.columns = ['Element', 'Count', 'Total (ms)', 'Avg (ms)', 'Min (ms)', 'Max (ms)', 'Std (ms)']
        
        return dbc.Table.from_dataframe(
            display_df,
            striped=True,
            bordered=True,
            hover=True,
            size="sm",
            className="mt-3"
        )


# Register the visualizer
visualizer_registry.register('proctime', ProctimeVisualizer)
