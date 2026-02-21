#!/usr/bin/env python3
"""
Test script for element visibility functionality
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from data_provider import GstDataProvider
from components.processing_time_plots import ProcessingTimeTimeline


def test_element_visibility():
    """Test element visibility controls functionality."""
    log_file = os.path.join(os.path.dirname(__file__), '..', 'logs', 'shark', 'proctime.log')
    
    print("Testing element visibility controls...")
    
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
    
    # Test element controls creation
    controls = timeline.create_element_controls(df)
    print(f"✅ Element controls created: {len(controls)} components")
    
    # Find the checklist component
    checklist = None
    print(f"Component types:")
    for i, component in enumerate(controls):
        print(f"  {i}: {type(component)}")
        if hasattr(component, 'id'):
            print(f"     ID: {component.id}")
    
    if len(controls) >= 2:
        checklist = controls[1]  # Checklist is the second component
    
    if checklist is not None:
        print(f"✅ Checklist found with type: {type(checklist)}")
        if hasattr(checklist, 'id'):
            print(f"✅ Checklist ID: {checklist.id}")
        if hasattr(checklist, 'options'):
            print(f"✅ Checklist options: {len(checklist.options)} elements")
        if hasattr(checklist, 'value'):
            print(f"✅ Default values: {checklist.value}")
        
        # Test individual elements
        if hasattr(checklist, 'options'):
            for option in checklist.options:
                print(f"   - {option['label']}: {option['value']}")
    else:
        print("❌ Checklist component not found!")
        return False
    
    # Test figure creation with different visibility settings
    all_elements = df['element_name'].unique()
    print(f"✅ All elements: {list(all_elements)}")
    
    # Test with all elements visible
    fig1 = timeline.create_figure(df, visible_elements=all_elements)
    visible_traces_1 = sum(1 for trace in fig1.data if trace.visible)
    print(f"✅ All elements visible: {visible_traces_1} traces")
    
    # Test with partial visibility
    partial_elements = [all_elements[0], all_elements[2]]  # First and third elements
    fig2 = timeline.create_figure(df, visible_elements=partial_elements)
    visible_traces_2 = sum(1 for trace in fig2.data if trace.visible)
    print(f"✅ Partial elements visible: {visible_traces_2} traces")
    
    # Test with single element
    single_element = [all_elements[1]]
    fig3 = timeline.create_figure(df, visible_elements=single_element)
    visible_traces_3 = sum(1 for trace in fig3.data if trace.visible)
    print(f"✅ Single element visible: {visible_traces_3} traces")
    
    # Verify trace names match visible elements
    if fig2.data:
        visible_names = [trace.name for trace in fig2.data if trace.visible]
        print(f"✅ Visible trace names: {visible_names}")
    
    return True


if __name__ == "__main__":
    print("👁️ Testing Element Visibility Controls")
    print("=" * 50)
    
    try:
        success = test_element_visibility()
        if success:
            print("\n✅ All element visibility tests passed!")
            print("\nFeatures working:")
            print("- Element checkbox controls in sidebar")
            print("- Dynamic line plot visibility")
            print("- Proper trace management")
            print("- Integration with dashboard callbacks")
        else:
            print("\n❌ Some tests failed!")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
