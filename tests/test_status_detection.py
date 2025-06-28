#!/usr/bin/env python3
"""
Test script to verify that custom status keywords from settings are properly detected.
This tests the fix for the bug where custom statuses added in the UI weren't working.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import normalize_status

def test_custom_status_detection():
    """Test that custom status keywords are properly detected when color_map is provided."""
    
    # Example color map like what would come from settings
    custom_color_map = {
        "in_meeting": {"color": "255,0,0", "power_off": False},
        "focus": {"color": "0,0,255", "power_off": False},
        "available": {"color": "0,255,0", "power_off": True},
        "lunch": {"color": "0,255,0", "power_off": True},
        "break": {"color": "255,255,0", "power_off": True},
        "deep_work": {"color": "128,0,128", "power_off": False},
    }
    
    test_cases = [
        # (event_summary, expected_status_with_custom_map, expected_status_without_map)
        ("Team lunch break", "lunch", "in_meeting"),
        ("Break time", "break", "in_meeting"), 
        ("Deep_work session", "deep_work", "in_meeting"),
        ("Focus time", "focus", "focus"),  # Should work in both cases
        ("Morning standup", "in_meeting", "in_meeting"),  # Default fallback
        ("Coffee break", "break", "in_meeting"),
    ]
    
    print("Testing custom status detection...")
    print("=" * 50)
    
    for summary, expected_custom, expected_default in test_cases:
        # Test with custom color map
        result_custom = normalize_status(summary, custom_color_map)
        
        # Test without custom color map (should use defaults)
        result_default = normalize_status(summary, None)
        
        print(f"Event: '{summary}'")
        print(f"  With custom map: {result_custom} (expected: {expected_custom})")
        print(f"  With defaults:   {result_default} (expected: {expected_default})")
        
        # Check results
        if result_custom == expected_custom:
            print("  ✅ Custom detection PASSED")
        else:
            print("  ❌ Custom detection FAILED")
            
        if result_default == expected_default:
            print("  ✅ Default detection PASSED")
        else:
            print("  ❌ Default detection FAILED")
        print()

if __name__ == "__main__":
    test_custom_status_detection()
    print("Test complete! If you see ✅ for all tests, the fix is working correctly.")
    print("You can now add custom status keywords in the Settings UI and they should be detected.")
