"""
GST-Whale Dashboard - Plotly Dash Web Interface

A modern, interactive web dashboard for visualizing GStreamer tracer data.
Starts with processing time visualization and designed to be extensible
for other tracer types like interlatency.
"""

from __future__ import annotations

import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
from typing import List, Optional, Tuple
import os
import sys

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_provider import GstDataProvider
from components.processing_time_plots import (
    ProcessingTimeTimeline, 
    ProcessingTimeStats, 
    ProcessingTimeHeatmap
)


class GstWhaleDashboard:
    """Main dashboard application for GST-Whale visualizations."""
    
    def __init__(self, data_provider: GstDataProvider):
        """Initialize dashboard with data provider."""
        self.data_provider = data_provider
        self.timeline = ProcessingTimeTimeline()
        self.stats = ProcessingTimeStats()
        self.app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
        self._setup_layout()
        self._setup_callbacks()
    
    def _setup_layout(self):
        """Setup the dashboard layout."""
        # Get initial data
        element_list = self.data_provider.get_element_list()
        time_range = self.data_provider.get_time_range()
        event_summary = self.data_provider.get_event_summary()
        
        # Get initial data for element controls
        initial_timeline_df = self.data_provider.get_timeline_data()
        element_controls = self.timeline.create_element_controls(initial_timeline_df)
        
        # Sidebar for controls
        sidebar = dbc.Card([
            dbc.CardBody([
                html.H4("GST-Whale Dashboard", className="card-title"),
                html.Hr(),
                
                # Element filter
                html.H6("Element Filter", className="text-muted"),
                dcc.Dropdown(
                    id='element-dropdown',
                    options=[{'label': 'All Elements', 'value': ''}] + 
                           [{'label': elem, 'value': elem} for elem in element_list],
                    value='',
                    multi=True,
                    placeholder="Select elements..."
                ),
                html.Hr(),
                
                # Element visibility controls
                *element_controls,
                html.Hr(),
                
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
                
                # Element visibility controls
                html.Div(id='element-visibility-controls'),
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
                    html.P(f"ProcTime Events: {event_summary['proctime_events']}")
                ])
            ])
        ], className="mb-4")
        
        # Main content area
        main_content = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1("Processing Time Analysis", className="text-center mb-4"),
                    html.Hr()
                ])
            ]),
            
            # Timeline plot
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Processing Time Timeline", className="card-title"),
                            dcc.Graph(id='timeline-graph', style={'height': '500px'})
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),
            
            # Statistics and distribution
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Element Statistics", className="card-title"),
                            dcc.Graph(id='stats-graph', style={'height': '400px'})
                        ])
                    ])
                ], width=6),
                
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Time Distribution", className="card-title"),
                            dcc.Graph(id='distribution-graph', style={'height': '400px'})
                        ])
                    ])
                ], width=6)
            ], className="mb-4"),
            
            # Data table
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Detailed Statistics", className="card-title"),
                            html.Div(id='stats-table')
                        ])
                    ])
                ])
            ])
        ], fluid=True)
        
        # Main layout
        self.app.layout = dbc.Container([
            dbc.Row([
                dbc.Col([
                    sidebar
                ], width=3),
                dbc.Col([
                    main_content
                ], width=9)
            ])
        ], fluid=True, className="p-3")
    
    def _setup_callbacks(self):
        """Setup interactive callbacks."""
        
        @self.app.callback(
            [Output('timeline-graph', 'figure'),
             Output('stats-graph', 'figure'),
             Output('distribution-graph', 'figure'),
             Output('stats-table', 'children')],
            [Input('element-dropdown', 'value'),
             Input('time-range-slider', 'value'),
             Input('viz-options', 'value'),
             Input('element-visibility-checklist', 'value')]
        )
        def update_visualizations(selected_elements, time_range, viz_options, visible_elements):
            """Update all visualizations based on filters."""
            
            # Process element filter
            element_filter = None
            if selected_elements and isinstance(selected_elements, list):
                if len(selected_elements) > 0 and selected_elements != ['']:
                    element_filter = selected_elements[0] if len(selected_elements) == 1 else '|'.join(selected_elements)
            elif selected_elements:
                element_filter = selected_elements
            
            # Get data
            timeline_df = self.data_provider.get_timeline_data(
                element_filter=element_filter,
                start_time=time_range[0],
                end_time=time_range[1]
            )
            
            stats_df = self.data_provider.get_element_statistics(element_filter)
            
            # Create figures using new components
            show_rolling = 'rolling' in viz_options
            timeline_fig = self.timeline.create_figure(
                timeline_df, 
                show_rolling_avg=show_rolling,
                visible_elements=visible_elements
            )
            stats_fig = self.stats.create_bar_chart(stats_df)
            dist_fig = self._create_distribution_figure(timeline_df)
            stats_table = self._create_stats_table(stats_df)
            
            return timeline_fig, stats_fig, dist_fig, stats_table
    
    def _create_stats_figure(self, df: pd.DataFrame) -> go.Figure:
        """Create statistics bar chart."""
        if df.empty:
            return go.Figure().add_annotation(text="No data available", 
                                           xref="paper", yref="paper",
                                           x=0.5, y=0.5, showarrow=False)
        
        fig = go.Figure()
        
        # Add average processing time bars
        fig.add_trace(go.Bar(
            x=df['element_name'],
            y=df['avg_time_ms'],
            name='Average Time',
            marker_color='lightblue',
            hovertemplate='<b>%{x}</b><br>' +
                         'Avg Time: %{y:.3f}ms<extra></extra>'
        ))
        
        # Add error bars for min/max
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
            showlegend=True
        )
        
        return fig
    
    def _create_distribution_figure(self, df: pd.DataFrame) -> go.Figure:
        """Create distribution histogram."""
        if df.empty:
            return go.Figure().add_annotation(text="No data available", 
                                           xref="paper", yref="paper",
                                           x=0.5, y=0.5, showarrow=False)
        
        fig = go.Figure()
        
        # Create histogram for each element
        for element in df['element_name'].unique():
            element_df = df[df['element_name'] == element]
            fig.add_trace(go.Histogram(
                x=element_df['processing_time_ms'],
                name=element,
                opacity=0.7,
                nbinsx=30,
                hovertemplate='<b>%{fullData.name}</b><br>' +
                             'Range: %{x:.3f}ms<br>' +
                             'Count: %{y}<extra></extra>'
            ))
        
        fig.update_layout(
            title="Processing Time Distribution",
            xaxis_title="Processing Time (ms)",
            yaxis_title="Count",
            barmode='overlay',
            showlegend=True
        )
        
        return fig
    
    def _create_stats_table(self, df: pd.DataFrame) -> html.Div:
        """Create detailed statistics table."""
        if df.empty:
            return html.P("No data available")
        
        # Format data for display
        display_df = df.copy()
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
    
    def run(self, debug: bool = False, port: int = 8050):
        """Run the dashboard application."""
        self.app.run(debug=debug, port=port, host='0.0.0.0')


def create_dashboard(log_file: str, **kwargs) -> GstWhaleDashboard:
    """
    Create dashboard instance from log file.
    
    Args:
        log_file: Path to the log file
        **kwargs: Additional arguments for data provider
        
    Returns:
        GstWhaleDashboard instance
    """
    data_provider = GstDataProvider.create_from_log_file(
        log_file, 
        enable_debug=False,  # Focus on tracer data for now
        enable_tracer=True,
        verbose=False
    )
    
    return GstWhaleDashboard(data_provider)


if __name__ == "__main__":
    # Example usage
    log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'shark', 'proctime.log')
    
    if os.path.exists(log_file):
        dashboard = create_dashboard(log_file)
        print(f"Starting GST-Whale Dashboard...")
        print(f"Open http://localhost:8051 in your browser")
        dashboard.run(debug=True, port=8051)
    else:
        print(f"Log file not found: {log_file}")
        print("Please update the log file path or ensure the file exists.")
