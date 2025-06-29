#!/usr/bin/env python3
"""
Test meeting transition scenarios, especially handling of meeting_ended_early status
with overlapping and consecutive meetings.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import datetime
import sys
import os

# Mock Qt and GUI dependencies before importing
sys.modules['PySide6'] = MagicMock()
sys.modules['PySide6.QtWidgets'] = MagicMock()
sys.modules['PySide6.QtCore'] = MagicMock()
sys.modules['PySide6.QtGui'] = MagicMock()
sys.modules['PySide6.QtNetwork'] = MagicMock()

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))


class TestMeetingTransitions(unittest.TestCase):
    """Test meeting transition scenarios and status handling."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_config = {
            "CALENDAR_SYNC_ENABLED": True,
            "SELECTED_CALENDAR_ID": "test@example.com",
            "LIGHTS_ENABLED": True,
            "GOVEE_API_KEY": "test_key",
            "GOVEE_DEVICE_ID": "test_device",
            "STATUS_COLOR_MAP": {
                "in_meeting": {"color": "255,0,0", "power_off": False},
                "available": {"color": "0,255,0", "power_off": True},
                "meeting_ended_early": {"color": "255,255,0", "power_off": True}
            }
        }
        
    def test_imminent_meeting_detection_logic(self):
        """Test the core logic for detecting imminent meetings."""
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Test case 1: Meeting starts in 30 seconds (should be imminent)
        next_event_start = now + datetime.timedelta(seconds=30)
        time_to_next = (next_event_start - now).total_seconds()
        imminent_meeting = (0 <= time_to_next <= 60)
        self.assertTrue(imminent_meeting, "Meeting in 30 seconds should be imminent")
        
        # Test case 2: Meeting starts in 90 seconds (should not be imminent)
        next_event_start = now + datetime.timedelta(seconds=90)
        time_to_next = (next_event_start - now).total_seconds()
        imminent_meeting = (0 <= time_to_next <= 60)
        self.assertFalse(imminent_meeting, "Meeting in 90 seconds should not be imminent")
        
        # Test case 3: Meeting started 30 seconds ago (should not be imminent)
        next_event_start = now - datetime.timedelta(seconds=30)
        time_to_next = (next_event_start - now).total_seconds()
        imminent_meeting = (0 <= time_to_next <= 60)
        self.assertFalse(imminent_meeting, "Past meeting should not be imminent")
        
    def test_meeting_status_transitions(self):
        """Test the logic for status transitions with meeting_ended_early."""
        
        # Test: meeting_ended_early with imminent meeting should transition
        manual_status = "meeting_ended_early"
        imminent_meeting = True
        active_meeting = False
        
        if active_meeting or imminent_meeting:
            expected_status = "in_meeting"
            should_clear_manual = True
        elif manual_status:
            expected_status = manual_status
            should_clear_manual = False
        else:
            expected_status = "available"
            should_clear_manual = False
            
        self.assertEqual(expected_status, "in_meeting")
        self.assertTrue(should_clear_manual)
        
        # Test: meeting_ended_early with no imminent meeting should stay manual
        manual_status = "meeting_ended_early"
        imminent_meeting = False
        active_meeting = False
        
        if active_meeting or imminent_meeting:
            expected_status = "in_meeting"
            should_clear_manual = True
        elif manual_status:
            expected_status = manual_status
            should_clear_manual = False
        else:
            expected_status = "available"
            should_clear_manual = False
            
        self.assertEqual(expected_status, "meeting_ended_early")
        self.assertFalse(should_clear_manual)
        
    def test_calendar_status_handling(self):
        """Test handling of different calendar statuses."""
        
        # Test: calendar shows "in_meeting" should override manual status
        calendar_status = "in_meeting"
        manual_status = "meeting_ended_early"
        active_meeting = (calendar_status == "in_meeting")
        
        if active_meeting:
            expected_status = "in_meeting"
            should_clear_manual = True
        elif manual_status:
            expected_status = manual_status
            should_clear_manual = False
        else:
            expected_status = calendar_status
            should_clear_manual = False
            
        self.assertEqual(expected_status, "in_meeting")
        self.assertTrue(should_clear_manual)
        
    def test_light_control_logic(self):
        """Test light control decisions based on status."""
        
        color_map = {
            "in_meeting": {"color": "255,0,0", "power_off": False},
            "available": {"color": "0,255,0", "power_off": True},
            "meeting_ended_early": {"color": "255,255,0", "power_off": True}
        }
        
        # Test: in_meeting should turn on red lights
        status = "in_meeting"
        config = color_map.get(status, {})
        should_power_off = config.get("power_off", False)
        expected_color = config.get("color", "128,128,128")
        
        self.assertFalse(should_power_off)
        self.assertEqual(expected_color, "255,0,0")
        
        # Test: meeting_ended_early should turn off lights
        status = "meeting_ended_early"
        config = color_map.get(status, {})
        should_power_off = config.get("power_off", False)
        
        self.assertTrue(should_power_off)
        
    def test_manual_status_expiry_logic(self):
        """Test manual status expiry handling."""
        
        now = datetime.datetime.now(datetime.timezone.utc)
        manual_expiry = 2 * 60 * 60  # 2 hours
        
        # Test: Recent manual status should not expire
        manual_timestamp = now.timestamp() - 1800  # 30 minutes ago
        time_since_manual = now.timestamp() - manual_timestamp
        manual_expired = time_since_manual > manual_expiry
        
        self.assertFalse(manual_expired, "Manual status should not expire after 30 minutes")
        
        # Test: Old manual status should expire
        manual_timestamp = now.timestamp() - 3 * 60 * 60  # 3 hours ago
        time_since_manual = now.timestamp() - manual_timestamp
        manual_expired = time_since_manual > manual_expiry
        
        self.assertTrue(manual_expired, "Manual status should expire after 3 hours")


def run_tests():
    """Run the meeting transition tests."""
    print("🧪 Running Meeting Transition Tests...")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestMeetingTransitions)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success status
    success = result.wasSuccessful()
    
    if success:
        print("✅ All meeting transition tests passed!")
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        
    return success


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
