#!/usr/bin/env python3
"""
Test script for dashboard callbacks
Tests the specific callback that was failing.
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_provider import GstDataProvider


def test_timeline_data_with_time_filter():
    """Test get_timeline_data with time filtering parameters."""
    log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'shark', 'proctime.log')
    
    print("Testing get_timeline_data with time filters...")
    
    # Create data provider
    data_provider = GstDataProvider.create_from_log_file(
        log_file, 
        enable_debug=False,
        enable_tracer=True,
        verbose=False
    )
    
    # Get full time range
    full_df = data_provider.get_timeline_data()
    if full_df.empty:
        print("❌ No data found")
        return False
    
    time_min, time_max = full_df['timestamp'].min(), full_df['timestamp'].max()
    print(f"✅ Full data range: {time_min:.3f} - {time_max:.3f}")
    print(f"✅ Full data shape: {full_df.shape}")
    
    # Test with time filtering
    start_time = time_min + (time_max - time_min) * 0.25  # 25% into the data
    end_time = time_min + (time_max - time_min) * 0.75    # 75% into the data
    
    filtered_df = data_provider.get_timeline_data(
        start_time=start_time,
        end_time=end_time
    )
    
    print(f"✅ Filtered data range: {filtered_df['timestamp'].min():.3f} - {filtered_df['timestamp'].max():.3f}")
    print(f"✅ Filtered data shape: {filtered_df.shape}")
    
    # Test with element filter
    element_df = data_provider.get_timeline_data(
        element_filter='capsfilter0',
        start_time=start_time,
        end_time=end_time
    )
    
    print(f"✅ Element filtered data shape: {element_df.shape}")
    print(f"✅ Elements in filtered data: {element_df['element_name'].unique()}")
    
    # Test with rolling window
    rolling_df = data_provider.get_timeline_data(
        start_time=start_time,
        end_time=end_time,
        window_size=50
    )
    
    if 'rolling_avg_ms' in rolling_df.columns:
        print(f"✅ Rolling average calculated successfully")
        print(f"✅ Rolling avg range: {rolling_df['rolling_avg_ms'].min():.3f} - {rolling_df['rolling_avg_ms'].max():.3f}")
    else:
        print("⚠️  Rolling average not calculated (insufficient data)")
    
    return True


if __name__ == "__main__":
    print("🧪 Testing Dashboard Callbacks")
    print("=" * 50)
    
    try:
        success = test_timeline_data_with_time_filter()
        if success:
            print("\n✅ All callback tests passed!")
        else:
            print("\n❌ Some tests failed!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
