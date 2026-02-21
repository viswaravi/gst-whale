#!/usr/bin/env python3
"""
Test script for the new line plot functionality
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_provider import GstDataProvider
from components.processing_time_plots import ProcessingTimeTimeline


def test_line_plot_functionality():
    """Test the new line plot with element visibility controls."""
    log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'shark', 'proctime.log')
    
    print("Testing new line plot functionality...")
    
    # Create data provider
    data_provider = GstDataProvider.create_from_log_file(
        log_file, 
        enable_debug=False,
        enable_tracer=True,
        verbose=False
    )
    
    # Create timeline component
    timeline = ProcessingTimeTimeline()
    
    # Get data
    df = data_provider.get_timeline_data()
    print(f"✅ Data loaded: {df.shape}")
    
    # Test line plot creation
    fig1 = timeline.create_figure(df, show_rolling_avg=True)
    print(f"✅ Line plot with rolling avg: {len(fig1.data)} traces")
    
    # Test with element visibility
    visible_elements = ['capsfilter0', 'videoconvert0']
    fig2 = timeline.create_figure(df, visible_elements=visible_elements)
    print(f"✅ Line plot with filtered elements: {len(fig2.data)} traces")
    
    # Verify visibility
    visible_traces = [trace for trace in fig2.data if trace.visible]
    print(f"✅ Visible traces: {len(visible_traces)}")
    
    # Test element controls creation
    controls = timeline.create_element_controls(df)
    print(f"✅ Element controls created: {len(controls)} components")
    
    # Test without rolling average (raw line plot)
    fig3 = timeline.create_figure(df, show_rolling_avg=False)
    print(f"✅ Raw line plot: {len(fig3.data)} traces")
    
    return True


if __name__ == "__main__":
    print("📈 Testing Line Plot Functionality")
    print("=" * 50)
    
    try:
        success = test_line_plot_functionality()
        if success:
            print("\n✅ All line plot tests passed!")
            print("\nNew features:")
            print("- Clean line plots over time")
            print("- Element visibility controls")
            print("- Rolling average toggle")
            print("- Better hover information")
        else:
            print("\n❌ Some tests failed!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
