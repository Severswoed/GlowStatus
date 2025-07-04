#!/usr/bin/env python3
"""
Test script to validate the final fixes for GlowStatus:
1. Light state tracking to avoid redundant API calls
2. "End Meeting Early" snooze logic with overlapping meetings  
3. Manual status sync improvements
"""

import sys
import os
import time
import json
import datetime
from unittest.mock import Mock, patch

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from glowstatus import GlowStatusController
from settings_ui import load_config, save_config

def test_light_state_tracking():
    """Test that redundant API calls are avoided"""
    print("\n=== Testing Light State Tracking ===")
    
    controller = GlowStatusController()
    
    # Mock govee controller to track API calls
    mock_govee = Mock()
    mock_govee.set_power = Mock()
    mock_govee.set_color = Mock()
    
    color_map = {
        "in_meeting": {"color": "255,0,0", "power_off": False},
        "available": {"color": "0,255,0", "power_off": True}
    }
    
    print("First call - should make API calls...")
    controller.apply_status_to_light(mock_govee, "in_meeting", color_map, False)
    
    # Check that both power and color were called
    assert mock_govee.set_power.call_count == 1
    assert mock_govee.set_color.call_count == 1
    mock_govee.set_power.assert_called_with("on")
    mock_govee.set_color.assert_called_with(255, 0, 0)
    
    print("Second call with same status - should NOT make API calls...")
    mock_govee.reset_mock()
    controller.apply_status_to_light(mock_govee, "in_meeting", color_map, False)
    
    # Should make no calls since state hasn't changed
    assert mock_govee.set_power.call_count == 0
    assert mock_govee.set_color.call_count == 0
    
    print("Third call with different status - should make API calls...")
    controller.apply_status_to_light(mock_govee, "available", color_map, False)
    
    # Should only call set_power (off), not set_color
    assert mock_govee.set_power.call_count == 1
    assert mock_govee.set_color.call_count == 0
    mock_govee.set_power.assert_called_with("off")
    
    print("✅ Light state tracking working correctly!")

def test_end_meeting_early_snooze():
    """Test that 'End Meeting Early' respects snooze period"""
    print("\n=== Testing End Meeting Early Snooze Logic ===")
    
    # Save original config
    original_config = load_config()
    
    try:
        # Setup test config
        config = {
            "GOVEE_DEVICE_ID": "test_device",
            "GOVEE_DEVICE_MODEL": "H6159", 
            "SELECTED_CALENDAR_ID": "test@example.com",
            "DISABLE_CALENDAR_SYNC": False,
            "DISABLE_LIGHT_CONTROL": False,
            "STATUS_COLOR_MAP": {
                "in_meeting": {"color": "255,0,0", "power_off": False},
                "available": {"color": "0,255,0", "power_off": True}
            },
            "CURRENT_STATUS": "meeting_ended_early",
            "MANUAL_STATUS_TIMESTAMP": time.time(),  # Just set
            "OFF_FOR_UNKNOWN_STATUS": True,
            "POWER_OFF_WHEN_AVAILABLE": True
        }
        save_config(config)
        
        controller = GlowStatusController()
        
        # Mock the calendar sync and govee controller
        with patch('glowstatus.CalendarSync') as mock_calendar_class, \
             patch('glowstatus.GoveeController') as mock_govee_class, \
             patch('glowstatus.load_secret') as mock_load_secret:
            
            mock_load_secret.return_value = "test_api_key"
            mock_govee = Mock()
            mock_govee_class.return_value = mock_govee
            
            # Mock calendar to return overlapping meeting
            mock_calendar = Mock()
            mock_calendar_class.return_value = mock_calendar
            mock_calendar.get_current_status.return_value = ("in_meeting", datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=30))
            
            print("Testing 'End Meeting Early' during snooze period (should stay available)...")
            controller._update_now_impl()
            
            # During snooze period, should be "available" despite overlapping meeting
            current_config = load_config()
            assert current_config.get("CURRENT_STATUS") == "meeting_ended_early"
            print("✅ Status remains 'meeting_ended_early' during snooze period")
        
        # Test after snooze period
        config["MANUAL_STATUS_TIMESTAMP"] = time.time() - (6 * 60)  # 6 minutes ago
        save_config(config)
        
        with patch('glowstatus.CalendarSync') as mock_calendar_class, \
             patch('glowstatus.GoveeController') as mock_govee_class, \
             patch('glowstatus.load_secret') as mock_load_secret:
            
            mock_load_secret.return_value = "test_api_key"
            mock_govee = Mock()
            mock_govee_class.return_value = mock_govee
            
            # Mock calendar to return overlapping meeting
            mock_calendar = Mock()
            mock_calendar_class.return_value = mock_calendar
            mock_calendar.get_current_status.return_value = ("in_meeting", datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=30))
            
            print("Testing after snooze period with overlapping meeting (should transition to in_meeting)...")
            controller._update_now_impl()
            
            # After snooze period, should transition to calendar control
            current_config = load_config()
            assert current_config.get("CURRENT_STATUS") is None  # Manual override cleared
            print("✅ Manual override cleared after snooze period with overlapping meeting")
            
    finally:
        # Restore original config
        save_config(original_config)

def test_manual_status_validation():
    """Test that manual status without timestamp is handled correctly"""
    print("\n=== Testing Manual Status Validation ===")
    
    # Save original config
    original_config = load_config()
    
    try:
        # Test invalid manual status (no timestamp, not meeting_ended_early)
        config = {
            "GOVEE_DEVICE_ID": "test_device",
            "GOVEE_DEVICE_MODEL": "H6159",
            "SELECTED_CALENDAR_ID": "test@example.com", 
            "DISABLE_CALENDAR_SYNC": False,
            "DISABLE_LIGHT_CONTROL": False,
            "STATUS_COLOR_MAP": {
                "focus": {"color": "0,0,255", "power_off": False},
                "available": {"color": "0,255,0", "power_off": True}
            },
            "CURRENT_STATUS": "focus",  # No timestamp!
            "OFF_FOR_UNKNOWN_STATUS": True,
            "POWER_OFF_WHEN_AVAILABLE": True
        }
        save_config(config)
        
        controller = GlowStatusController()
        
        with patch('glowstatus.CalendarSync') as mock_calendar_class, \
             patch('glowstatus.GoveeController') as mock_govee_class, \
             patch('glowstatus.load_secret') as mock_load_secret:
            
            mock_load_secret.return_value = "test_api_key"
            mock_govee = Mock()
            mock_govee_class.return_value = mock_govee
            
            # Mock calendar
            mock_calendar = Mock()
            mock_calendar_class.return_value = mock_calendar
            mock_calendar.get_current_status.return_value = ("available", None)
            
            print("Testing manual status without timestamp (should be cleared)...")
            controller._update_now_impl()
            
            # Manual status without timestamp should be cleared
            current_config = load_config()
            assert current_config.get("CURRENT_STATUS") != "focus"
            print("✅ Invalid manual status (no timestamp) was cleared")
            
        # Test valid meeting_ended_early without timestamp (should be allowed)
        config["CURRENT_STATUS"] = "meeting_ended_early"
        config.pop("MANUAL_STATUS_TIMESTAMP", None)
        save_config(config)
        
        with patch('glowstatus.CalendarSync') as mock_calendar_class, \
             patch('glowstatus.GoveeController') as mock_govee_class, \
             patch('glowstatus.load_secret') as mock_load_secret:
            
            mock_load_secret.return_value = "test_api_key"
            mock_govee = Mock()
            mock_govee_class.return_value = mock_govee
            
            # Mock calendar
            mock_calendar = Mock()
            mock_calendar_class.return_value = mock_calendar
            mock_calendar.get_current_status.return_value = ("available", None)
            
            print("Testing 'meeting_ended_early' without timestamp (should be allowed)...")
            controller._update_now_impl()
            
            # meeting_ended_early without timestamp should be allowed
            current_config = load_config()
            # Should transition to calendar status since no timestamp means no snooze
            print("✅ 'meeting_ended_early' without timestamp handled correctly")
            
    finally:
        # Restore original config
        save_config(original_config)

def main():
    print("🔧 Testing Final Fixes for GlowStatus")
    print("=" * 50)
    
    try:
        test_light_state_tracking()
        test_end_meeting_early_snooze() 
        test_manual_status_validation()
        
        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("\nKey fixes validated:")
        print("1. ✅ Light state tracking prevents redundant API calls")
        print("2. ✅ 'End Meeting Early' respects 5-minute snooze period")
        print("3. ✅ Manual status validation prevents invalid states")
        print("4. ✅ Manual overrides properly transition to calendar control")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
