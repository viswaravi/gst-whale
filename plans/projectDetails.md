# GST-Whale

## 📁 Current File Structure

```
gst-whale/
├── src/                          # Main implementation
│   ├── gstTracer.py           # Unified CLI entry point
│   ├── debugTracer.py         # Debug parsing function
│   ├── sharkTracer.py          # Tracer parsing function
│   ├── parser/                  # Parser implementations
│   │   ├── base_parser.py
│   │   ├── proctime_parser.py
│   │   ├── gst_shark_trace_parser.py
│   │   ├── caps_parser.py
│   │   └── element_pads_parser.py
│   ├── model/                   # Data models
│   │   ├── element.py
│   │   ├── pad.py
│   │   └── events.py
│   ├── registry/                # Data storage
│   │   └── gst_registry.py
│   └── utils/                   # Utilities
│       └── log_reader.py
├── tests/                        # Comprehensive test suite
│   ├── test_*.py               # Unit tests
│   ├── fixtures/                # Test data
│   └── helpers.py              # Test utilities
├── logs/                         # Sample data
│   └── shark/
│       └── proctime.log       # Real test file (77K+ events)
├── ReadMe.md                    # Basic usage guide
└── pytest.ini                   # Test configuration
```

## 🎯 Core Implementation Status

### Architecture Overview

```
Simple Line-by-Line Parsing
├── debugTracer.py      # parse_debug_line(line, registry)
├── sharkTracer.py      # parse_tracer_line(line, registry)  
└── gstTracer.py        # Main CLI with routing logic
```

### ✅ Simple Line-by-Line Parsing
- **`parse_debug_line(line, registry)`**: Handles one GST_DEBUG line at a time
- **`parse_tracer_line(line, registry)`**: Handles one GST_TRACER line at a time
- **Main routing logic**: Domain-based with flexible enable/disable flags

### ✅ Unified CLI (gstTracer.py)
- **Flexible flags**: `--enable-debug/--disable-debug`, `--enable-tracer/--disable-tracer`
- **Focused modes**: `--debug-only`, `--tracer-only` for isolated testing
- **Comprehensive output**: `--stats`, `--events`, `--summary` options

### ✅ Shark Tracer Support
- **ProctimeParser**: Full regex-based parsing with error handling
- **Processing statistics**: Min/max/avg calculations per element
- **Millisecond display**: All timing shown in ms for readability
- **Extensible design**: Easy to add new tracer types via factory

### ✅ Enhanced Data Models
- **GstElement with pads/links**: Contains internal pad management for graph visualization
- **SharkTracerEvent hierarchy**: Base class for all tracer events
- **ProcTimeEvent**: Specific implementation for processing time data
- **GstRegistry enhancements**: Supports both debug and shark events with statistics

### ✅ Comprehensive Testing
- **Unit tests**: All major components tested with high coverage
- **CLI tests**: End-to-end functionality validation
- **Test fixtures**: Sample log files for testing
- **Manual validation**: Real-world log file verification

## 🚀 Real-World Validation Results

### Successfully Processed
- **77,073 proctime events** from actual proctime.log file
- **4 elements** tracked: capsfilter0, capsfilter1, videoconvert0, videoscale0
- **Processing statistics**: Min/max/avg calculations verified
- **Millisecond precision**: All timing displayed with 3 decimal places

### Performance Characteristics
- **Memory efficient**: Line-by-line processing, minimal memory footprint
- **Fast parsing**: Regex-based pattern matching
- **Large file support**: Tested with 77K+ log entries

## 🛠️ CLI Usage Examples

### Basic Analysis
```bash
# Parse both debug and tracer data
python src/gstTracer.py logs/pipeline.log --summary

# Only tracer data with statistics
python src/gstTracer.py logs/tracer.log --tracer-only --stats

# Filter by element name
python src/gstTracer.py pipeline.log --element videoscale0 --stats
```

### Advanced Filtering
```bash
# Disable debug parsing, only tracer
python src/gstTracer.py mixed.log --disable-debug --tracer-only

# Specific tracer type
python src/gstTracer.py tracer.log --tracer-type proctime --stats

# Multiple filters
python src/gstTracer.py mixed.log --element capsfilter --tracer-type proctime --stats
```

## 🔧 Extensibility Points

### Adding New Tracer Types
The architecture supports easy addition of new tracer types:

1. **Create event model** in `model/events.py`
2. **Implement parser class** extending `GstSharkTraceParser`
3. **Register in factory** within `sharkTracer.py`
4. **Update CLI** to add new `--tracer-type` options

### Example: Adding Interlatency Support
```python
# In model/events.py
@dataclass
class InterLatencyEvent(SharkTracerEvent):
    src_element: str
    sink_element: str
    latency: float
    latency_str: str

# In parser/interlatency_parser.py
class InterlatencyParser(GstSharkTraceParser):
    def __init__(self):
        super().__init__("interlatency")
    
    def parse_tracer_line(self, line: LogLine) -> Optional[InterLatencyEvent]:
        # Implementation here
        pass
```