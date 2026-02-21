#!/usr/bin/env python3
"""
Test script for GST-Whale Dashboard
Tests data loading and basic functionality.
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_provider import GstDataProvider
from dashboard_app import create_dashboard


def test_data_loading():
    """Test loading data from proctime.log."""
    log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'shark', 'proctime.log')
    
    print(f"Testing data loading from: {log_file}")
    
    if not os.path.exists(log_file):
        print(f"ERROR: Log file not found: {log_file}")
        return False
    
    try:
        # Create data provider
        data_provider = GstDataProvider.create_from_log_file(
            log_file, 
            enable_debug=False,
            enable_tracer=True,
            verbose=False
        )
        
        # Test data extraction
        print("✅ Data provider created successfully")
        
        # Get basic statistics
        summary = data_provider.get_event_summary()
        print(f"✅ Event summary: {summary}")
        
        # Get processing times data
        proc_df = data_provider.get_processing_times_data()
        print(f"✅ Processing times DataFrame shape: {proc_df.shape}")
        
        if not proc_df.empty:
            print(f"✅ Elements found: {proc_df['element_name'].unique()}")
            print(f"✅ Time range: {proc_df['timestamp'].min():.3f} - {proc_df['timestamp'].max():.3f}")
            print(f"✅ Processing time range: {proc_df['processing_time_ms'].min():.3f}ms - {proc_df['processing_time_ms'].max():.3f}ms")
        
        # Get element statistics
        stats_df = data_provider.get_element_statistics()
        print(f"✅ Element statistics shape: {stats_df.shape}")
        
        if not stats_df.empty:
            print("✅ Element statistics:")
            for _, row in stats_df.iterrows():
                print(f"   {row['element_name']}: {row['count']} samples, avg {row['avg_time_ms']:.3f}ms")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_dashboard_creation():
    """Test dashboard creation."""
    log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'shark', 'proctime.log')
    
    if not os.path.exists(log_file):
        print(f"ERROR: Log file not found: {log_file}")
        return False
    
    try:
        dashboard = create_dashboard(log_file)
        print("✅ Dashboard created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating dashboard: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🐋 Testing GST-Whale Dashboard")
    print("=" * 50)
    
    # Test data loading
    print("\n1. Testing data loading...")
    data_ok = test_data_loading()
    
    # Test dashboard creation
    print("\n2. Testing dashboard creation...")
    dashboard_ok = test_dashboard_creation()
    
    print("\n" + "=" * 50)
    if data_ok and dashboard_ok:
        print("✅ All tests passed! Dashboard is ready to use.")
        print("\nTo start the dashboard:")
        print("  python plotter/dashboard_app.py")
        print("Then open http://localhost:8050 in your browser")
    else:
        print("❌ Some tests failed. Please check the errors above.")
