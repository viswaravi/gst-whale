from __future__ import annotations

import subprocess
import tempfile
import pytest
from pathlib import Path

# Test data samples
DEBUG_SAMPLE_LOG = """0:00:00.001234567 12345 0xabcdef DEBUG GST_PADS trying to link element src:sink to element sink:sink
0:00:00.002345678 12345 0xabcdef DEBUG GST_CAPS caps are compatible
0:00:00.003456789 12345 0xabcdef DEBUG GST_PADS link successful src:sink -> sink:sink"""

TRACER_SAMPLE_LOG = """0:00:00.001234567 12345 0xabcdef TRACE GST_TRACER :0:: proctime, element=(string)test1, time=(string)0:00:00.001;
0:00:00.002345678 12345 0xabcdef TRACE GST_TRACER :0:: proctime, element=(string)test2, time=(string)0:00:00.002;
0:00:00.003456789 12345 0xabcdef TRACE GST_TRACER :0:: proctime, element=(string)test1, time=(string)0:00:00.003;"""

MIXED_SAMPLE_LOG = DEBUG_SAMPLE_LOG + "\n" + TRACER_SAMPLE_LOG


def test_debug_only_parsing():
    """Test CLI with debug-only flag."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        f.write(DEBUG_SAMPLE_LOG)
        f.flush()
        
        result = subprocess.run([
            "python", "gstTracer.py", f.name, "--debug-only", "--summary"
        ], capture_output=True, text=True, cwd="/home/viswa/Nidavelir/MyCode/Gstreamer/gst-whale/src")
        
        assert result.returncode == 0, "Should exit successfully"
        assert "Debug events:" in result.stdout, "Should show debug events count"
        assert "Shark tracer events: 0" in result.stdout, "Should show no tracer events"


def test_tracer_only_parsing():
    """Test CLI with tracer-only flag."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        f.write(TRACER_SAMPLE_LOG)
        f.flush()
        
        result = subprocess.run([
            "python", "gstTracer.py", f.name, "--tracer-only", "--summary"
        ], capture_output=True, text=True, cwd="/home/viswa/Nidavelir/MyCode/Gstreamer/gst-whale/src")
        
        assert result.returncode == 0, "Should exit successfully"
        assert "Debug events: 0" in result.stdout, "Should show no debug events"
        assert "Shark tracer events: 3" in result.stdout, "Should show tracer events count"


def test_mixed_parsing():
    """Test CLI with both debug and tracer parsing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        f.write(MIXED_SAMPLE_LOG)
        f.flush()
        
        result = subprocess.run([
            "python", "gstTracer.py", f.name, "--summary"
        ], capture_output=True, text=True, cwd="/home/viswa/Nidavelir/MyCode/Gstreamer/gst-whale/src")
        
        assert result.returncode == 0, "Should exit successfully"
        assert "Debug events:" in result.stdout, "Should show debug events count"
        assert "Shark tracer events:" in result.stdout, "Should show tracer events count"


def test_disable_debug_parsing():
    """Test CLI with debug parsing disabled."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        f.write(MIXED_SAMPLE_LOG)
        f.flush()
        
        result = subprocess.run([
            "python", "gstTracer.py", f.name, "--disable-debug", "--summary"
        ], capture_output=True, text=True, cwd="/home/viswa/Nidavelir/MyCode/Gstreamer/gst-whale/src")
        
        assert result.returncode == 0, "Should exit successfully"
        assert "Debug events: 0" in result.stdout, "Should show no debug events"
        assert "Shark tracer events:" in result.stdout, "Should show tracer events count"


def test_disable_tracer_parsing():
    """Test CLI with tracer parsing disabled."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        f.write(MIXED_SAMPLE_LOG)
        f.flush()
        
        result = subprocess.run([
            "python", "gstTracer.py", f.name, "--disable-tracer", "--summary"
        ], capture_output=True, text=True, cwd="/home/viswa/Nidavelir/MyCode/Gstreamer/gst-whale/src")
        
        assert result.returncode == 0, "Should exit successfully"
        assert "Debug events:" in result.stdout, "Should show debug events count"
        assert "Shark tracer events: 0" in result.stdout, "Should show no tracer events"


def test_stats_output():
    """Test statistics output."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        f.write(TRACER_SAMPLE_LOG)
        f.flush()
        
        result = subprocess.run([
            "python", "gstTracer.py", f.name, "--tracer-only", "--stats"
        ], capture_output=True, text=True, cwd="/home/viswa/Nidavelir/MyCode/Gstreamer/gst-whale/src")
        
        assert result.returncode == 0, "Should exit successfully"
        assert "PROCESSING TIME STATISTICS" in result.stdout, "Should show stats header"
        assert "test1" in result.stdout, "Should show test1 element"
        assert "test2" in result.stdout, "Should show test2 element"


def test_element_filter():
    """Test element filtering."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        f.write(MIXED_SAMPLE_LOG)
        f.flush()
        
        result = subprocess.run([
            "python", "gstTracer.py", f.name, "--tracer-only", "--stats", "--element", "test1"
        ], capture_output=True, text=True, cwd="/home/viswa/Nidavelir/MyCode/Gstreamer/gst-whale/src")
        
        assert result.returncode == 0, "Should exit successfully"
        assert "test1" in result.stdout, "Should show test1 element"
        assert "test2" not in result.stdout, "Should not show test2 element"


def test_conflicting_flags():
    """Test error handling for conflicting flags."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        f.write(MIXED_SAMPLE_LOG)
        f.flush()
        
        result = subprocess.run([
            "python", "gstTracer.py", f.name, "--debug-only", "--tracer-only"
        ], capture_output=True, text=True, cwd="/home/viswa/Nidavelir/MyCode/Gstreamer/gst-whale/src")
        
        assert result.returncode == 1, "Should exit with error"
        assert "Error:" in result.stdout, "Should show error message"


def test_nonexistent_file():
    """Test error handling for nonexistent file."""
    result = subprocess.run([
        "python", "gstTracer.py", "/nonexistent/file.log"
    ], capture_output=True, text=True, cwd="/home/viswa/Nidavelir/MyCode/Gstreamer/gst-whale/src")
    assert result.returncode != 0, "Should exit with error"
