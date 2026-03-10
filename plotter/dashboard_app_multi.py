"""
GST-Whale Multi-Tracer Dashboard - Plotly Dash Web Interface

A modern, interactive web dashboard for visualizing multiple GStreamer tracer types.
Supports both processing time and interlatency tracers through the plugin system.
"""

from __future__ import annotations

import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
from typing import List, Optional, Tuple
import os
import sys

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_provider import GstDataProvider
from plugins.base_visualizer import visualizer_registry

# Import visualizers to register them
import plugins.proctime_visualizer
import plugins.interlatency_visualizer


class GstWhaleMultiDashboard:
    """Multi-tracer dashboard application for GST-Whale visualizations."""
    
    def __init__(self, data_provider: GstDataProvider):
        """Initialize dashboard with data provider."""
        self.data_provider = data_provider
        
        # Create visualizer instances
        self.visualizers = {}
        for tracer_type in visualizer_registry.get_available_types():
            self.visualizers[tracer_type] = visualizer_registry.create_visualizer(
                tracer_type, data_provider
            )
        
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self._setup_layout()
        self._setup_callbacks()
    
    def _setup_layout(self):
        """Setup the dashboard layout."""
        # Get initial data
        time_range = self.data_provider.get_time_range()
        event_summary = self.data_provider.get_event_summary()
        
        # Get available elements and paths
        elements = self.data_provider.get_element_list()
        paths = self.data_provider.get_pipeline_paths()
        
        # Sidebar for controls
        sidebar = dbc.Card([
            dbc.CardBody([
                html.H4("GST-Whale Dashboard", className="card-title"),
                html.Hr(),
                
                # Tracer type selector
                html.H6("Tracer Type", className="text-muted"),
                dcc.Dropdown(
                    id='tracer-type-dropdown',
                    options=[
                        {'label': 'Processing Time', 'value': 'proctime'},
                        {'label': 'Interlatency', 'value': 'interlatency'}
                    ],
                    value='proctime' if event_summary['proctime_events'] > 0 else 'interlatency',
                    clearable=False
                ),
                html.Hr(),
                
                # Element filter (for proctime)
                html.Div(id='element-filter-section', children=[
                    html.H6("Element Filter", className="text-muted"),
                    dcc.Dropdown(
                        id='element-dropdown',
                        options=[{'label': elem, 'value': elem} for elem in elements],
                        value=[],
                        multi=True,
                        placeholder="Select elements..."
                    )
                ]),
                
                # Path filter (for interlatency)
                html.Div(id='path-filter-section', children=[
                    html.H6("Path Filter", className="text-muted"),
                    dcc.Dropdown(
                        id='path-dropdown',
                        options=[{'label': path, 'value': path} for path in paths],
                        value=[],
                        multi=True,
                        placeholder="Select pipeline paths..."
                    ),
                    html.Hr()
                ], style={'display': 'none'}),
                
                # Time range filter
                html.H6("Time Range", className="text-muted"),
                dcc.RangeSlider(
                    id='time-range-slider',
                    min=time_range[0],
                    max=time_range[1],
                    value=[time_range[0], time_range[1]],
                    marks={int(time_range[0]): 'Start', int(time_range[1]): 'End'},
                    tooltip={"placement": "bottom", "always_visible": True}
                ),
                html.Hr(),
                
                # Tracer-specific options
                html.Div(id='tracer-options-section'),
                html.Hr(),
                
                # Visualization options
                html.H6("Visualization Options", className="text-muted"),
                dbc.Checklist(
                    id='viz-options',
                    options=[
                        {'label': 'Show Rolling Average', 'value': 'rolling'},
                        {'label': 'Show Statistics', 'value': 'stats'},
                        {'label': 'Show Distribution', 'value': 'dist'}
                    ],
                    value=['rolling', 'stats'],
                    inline=True
                ),
                html.Hr(),
                
                # Summary info
                html.H6("Data Summary", className="text-muted"),
                html.Div(id='summary-info', children=[
                    html.P(f"Total Events: {event_summary['total_events']}"),
                    html.P(f"Elements: {event_summary['elements']}"),
                    html.P(f"ProcTime Events: {event_summary['proctime_events']}"),
                    html.P(f"Interlatency Events: {event_summary.get('interlatency_events', 0)}")
                ])
            ])
        ], className="mb-4")
        
        # Main content area
        main_content = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("GST-Whale Multi-Tracer Analysis", className="text-center mb-4"),
                    html.Hr()
                ])
            ]),
            
            # Dynamic content area (will be populated by callbacks)
            html.Div(id='main-content-area')
        ], fluid=True)
        
        # App layout
        self.app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([sidebar], width=3),
                dbc.Col([main_content], width=9)
            ])
        ], fluid=True, className="p-4")
    
    def _setup_callbacks(self):
        """Setup dashboard callbacks."""
        
        @self.app.callback(
            [Output('element-filter-section', 'style'),
             Output('path-filter-section', 'style'),
             Output('tracer-options-section', 'children')],
            [Input('tracer-type-dropdown', 'value')]
        )
        def update_filter_controls(tracer_type):
            """Update filter controls based on selected tracer type."""
            
            element_style = {'display': 'block'} if tracer_type == 'proctime' else {'display': 'none'}
            path_style = {'display': 'block'} if tracer_type == 'interlatency' else {'display': 'none'}
            
            # Get tracer-specific options
            if tracer_type in self.visualizers:
                options = self.visualizers[tracer_type].get_filter_controls()
            else:
                options = []
            
            return element_style, path_style, options
        
        @self.app.callback(
            Output('main-content-area', 'children'),
            [Input('tracer-type-dropdown', 'value')],
            [State('element-dropdown', 'value'),
             State('path-dropdown', 'value'),
             State('time-range-slider', 'value'),
             State('viz-options', 'value')]
        )
        def update_main_content(tracer_type, selected_elements, selected_paths, time_range, viz_options):
            """Update main content area based on selected tracer type."""
            
            if tracer_type not in self.visualizers:
                return html.Div("Visualizer not found", className="text-center")
            
            visualizer = self.visualizers[tracer_type]
            return visualizer.get_layout()
        
        # Register callbacks for each visualizer
        for tracer_type, visualizer in self.visualizers.items():
            visualizer.register_callbacks(self.app)
    
    def run(self, debug=False, port=8051):
        """Run the dashboard."""
        self.app.run(debug=debug, port=port)


def create_dashboard(log_file: str) -> GstWhaleMultiDashboard:
    """
    Create a dashboard instance from a log file.
    
    Args:
        log_file: Path to the GStreamer log file
        
    Returns:
        GstWhaleMultiDashboard instance
    """
    data_provider = GstDataProvider.create_from_log_file(
        log_file, 
        enable_debug=False,  # Focus on tracer data for now
        enable_tracer=True,
        verbose=False
    )
    
    return GstWhaleMultiDashboard(data_provider)


if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='GST-Whale Multi-Tracer Dashboard for GStreamer log analysis')
    parser.add_argument(
        '--log-file', 
        '-l',
        type=str,
        help='Path to the GStreamer log file (default: ../logs/shark/proctime.log)'
    )
    parser.add_argument(
        '--port', 
        '-p',
        type=int,
        default=8051,
        help='Port to run the dashboard on (default: 8051)'
    )
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Enable debug mode'
    )
    
    args = parser.parse_args()
    
    # Determine log file path
    if args.log_file:
        log_file = args.log_file
        # Convert relative path to absolute if needed
        if not os.path.isabs(log_file):
            log_file = os.path.abspath(log_file)
    else:
        # Default log file path
        log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'shark', 'proctime.log')
    
    print(f"GST-Whale Multi-Tracer Dashboard")
    print(f"Log file: {log_file}")
    print(f"Port: {args.port}")
    print(f"Debug mode: {args.debug}")
    print("-" * 50)
    
    if os.path.exists(log_file):
        try:
            dashboard = create_dashboard(log_file)
            print(f"Starting GST-Whale Multi-Tracer Dashboard...")
            print(f"Open http://localhost:{args.port} in your browser")
            dashboard.run(debug=args.debug, port=args.port)
        except Exception as e:
            print(f"Error creating dashboard: {e}")
            print("Please check the log file format and dependencies.")
    else:
        print(f"❌ Log file not found: {log_file}")
        print("Please provide a valid log file path using --log-file or ensure the default file exists.")
        print("\nExample usage:")
        print("  python dashboard_app_multi.py --log-file /path/to/your/proctime.log")
        print("  python dashboard_app_multi.py -l ./logs/interLatency.log --port 8050")
        print("  python dashboard_app_multi.py --debug")
