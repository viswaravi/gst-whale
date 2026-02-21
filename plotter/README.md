# GST-Whale Dashboard

A modern, interactive web dashboard for visualizing GStreamer tracer data using Plotly Dash.

## Features

### 🚀 Core Visualizations
- **Processing Time Timeline**: Interactive time-series plot with rolling averages
- **Element Statistics**: Bar charts and box plots for performance analysis  
- **Distribution Analysis**: Histograms and heatmaps for pattern identification
- **Data Tables**: Detailed statistics with export capabilities

### 🎯 Interactive Features
- **Element Filtering**: Select specific elements to focus analysis
- **Time Range Selection**: Zoom into specific time periods
- **Real-time Updates**: Reactive filtering and visualization
- **Export Options**: Download data as CSV or JSON

### 🔧 Extensible Architecture
- **Plugin System**: Easy addition of new tracer types
- **Modular Components**: Reusable visualization components
- **Scalable Design**: Handles large datasets efficiently

## Quick Start

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt
```

### Running the Dashboard
```bash
# Start with default log file (uses port 8051 to avoid conflicts)
python plotter/dashboard_app.py

# Or specify a custom log file and port
python -c "
from plotter.dashboard_app import create_dashboard
dashboard = create_dashboard('path/to/your/log.log')
dashboard.run(debug=True, port=8052)
"
```

Then open http://localhost:8051 in your browser.

### Testing
```bash
# Run tests to verify installation
python plotter/test_dashboard.py
```

## Architecture

### File Structure
```
plotter/
├── data_provider.py          # Data extraction and formatting
├── dashboard_app.py          # Main Dash application
├── test_dashboard.py         # Test suite
├── components/
│   ├── __init__.py
│   └── processing_time_plots.py    # Reusable plot components
├── plugins/
│   ├── __init__.py
│   ├── base_visualizer.py          # Plugin base class
│   └── proctime_visualizer.py      # Proctime implementation
└── README.md                # This file
```

### Key Components

#### GstDataProvider
- Extracts data from `GstRegistry` for visualization
- Provides filtering and aggregation capabilities
- Converts to pandas DataFrames for easy plotting

#### GstWhaleDashboard
- Main Dash application with Bootstrap styling
- Interactive callbacks for reactive updates
- Modular layout with sidebar controls

#### Plugin System
- `BaseVisualizer`: Abstract base for tracer visualizers
- `ProctimeVisualizer`: Implementation for processing time data
- Easy extension for interlatency and other tracer types

## Data Sources

The dashboard works with GStreamer tracer logs, specifically:
- **Proctime Tracer**: Processing time measurements per element
- **Future Support**: Interlatency, schedule time, queue level, etc.

### Expected Log Format
```
0:00:00.080014532 41265 0x7182a8000c00 TRACE GST_TRACER :0:: proctime, element=(string)capsfilter0, time=(string)0:00:00.000004657;
```

## Usage Examples

### Basic Analysis
1. Open the dashboard
2. Use the sidebar to filter by element
3. Adjust time range to focus on specific periods
4. Toggle visualization options for different views

### Advanced Features
- **Rolling Average**: Smooth noisy data with configurable window
- **Heatmap**: Identify patterns in processing time over time
- **Export Data**: Download filtered data for external analysis

## Adding New Tracer Types

### Step 1: Create Event Model
```python
# In src/model/events.py
@dataclass
class InterLatencyEvent(SharkTracerEvent):
    src_element: str
    sink_element: str
    latency: float
    latency_str: str
```

### Step 2: Create Parser
```python
# In src/parser/interlatency_parser.py
class InterlatencyParser(GstSharkTraceParser):
    def __init__(self):
        super().__init__("interlatency")
    
    def parse_tracer_line(self, line: LogLine) -> Optional[InterLatencyEvent]:
        # Implementation here
        pass
```

### Step 3: Create Visualizer Plugin
```python
# In plotter/plugins/interlatency_visualizer.py
class InterlatencyVisualizer(BaseVisualizer):
    def get_layout(self) -> dbc.Card:
        # Create layout for interlatency visualization
        pass
    
    def register_callbacks(self, app: dash.Dash) -> None:
        # Register callbacks
        pass

# Register the visualizer
visualizer_registry.register('interlatency', InterlatencyVisualizer)
```

### Step 4: Update Dashboard
Add the new visualizer to the main dashboard layout and register its callbacks.

## Performance Considerations

### Large Datasets
- **Sampling**: Automatically samples large datasets for performance
- **Lazy Loading**: Data loaded on-demand for visualizations
- **Caching**: Computed statistics cached for responsive UI

### Memory Management
- **Efficient Data Structures**: Uses pandas for optimized operations
- **Garbage Collection**: Proper cleanup of large objects
- **Streaming**: Processes logs line-by-line to minimize memory

## Troubleshooting

### Common Issues

#### Dashboard Won't Start
```bash
# Check dependencies
pip install -r requirements.txt

# Verify log file exists
ls logs/shark/proctime.log
```

#### No Data Displayed
```bash
# Test data loading
python plotter/test_dashboard.py
```

#### Performance Issues
- Reduce time range to focus on specific periods
- Use element filtering to reduce data volume
- Disable rolling averages for large datasets

### Debug Mode
```bash
# Run with debug output
python plotter/dashboard_app.py
```

## Contributing

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8

# Run tests
python plotter/test_dashboard.py

# Code formatting
black plotter/
```

### Adding Features
1. Create feature branch
2. Add tests for new functionality
3. Update documentation
4. Submit pull request

## License

This project is part of the GST-Whale toolkit for GStreamer analysis.
