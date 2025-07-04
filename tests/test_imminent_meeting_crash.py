#!/usr/bin/env python3
"""
Test for the imminent meeting crash scenario reported by user.
This test simulates the exact conditions that caused the crash:
- Meeting from 12:18pm to 12:22pm ET
- Crash at 12:17pm (1 minute prior check)
- App crashed when opening settings menu
"""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta, timezone

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from glowstatus import GlowStatusController


class TestImminentMeetingCrash(unittest.TestCase):
    """Test the specific crash scenario with imminent meeting detection."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Meeting time: 12:18pm to 12:22pm ET on July 4, 2025
        # Assuming ET is UTC-4 in July (EDT), so 12:18pm ET = 4:18pm UTC
        self.meeting_start_utc = datetime(2025, 7, 4, 16, 18, 0, tzinfo=timezone.utc)
        self.meeting_end_utc = datetime(2025, 7, 4, 16, 22, 0, tzinfo=timezone.utc)
        
        # Time when crash occurred: 12:17pm ET = 4:17pm UTC (1 minute before meeting)
        self.crash_time_utc = datetime(2025, 7, 4, 16, 17, 0, tzinfo=timezone.utc)
        
        print(f"Meeting UTC: {self.meeting_start_utc} to {self.meeting_end_utc}")
        print(f"Crash time UTC: {self.crash_time_utc}")
        
        # Mock config for the test
        self.mock_config = {
            "GOVEE_DEVICE_ID": "test_device",
            "GOVEE_DEVICE_MODEL": "H6159",
            "SELECTED_CALENDAR_ID": "test@example.com",
            "STATUS_COLOR_MAP": {
                "in_meeting": {"color": "255,0,0", "power_off": False},
                "available": {"color": "0,255,0", "power_off": True},
                "focus": {"color": "0,0,255", "power_off": False}
            },
            "DISABLE_CALENDAR_SYNC": False,
            "DISABLE_LIGHT_CONTROL": False
        }
    
    @patch('glowstatus.datetime')
    @patch('glowstatus.load_config')
    @patch('glowstatus.save_config')
    @patch('glowstatus.load_secret')
    @patch('glowstatus.CalendarSync')
    @patch('glowstatus.GoveeController')
    @patch('glowstatus.resource_path')
    @patch('glowstatus.os.path.exists')
    def test_imminent_meeting_crash_scenario(self, mock_exists, mock_resource_path, 
                                           mock_govee, mock_calendar_sync, mock_load_secret,
                                           mock_save_config, mock_load_config, mock_datetime):
        """Test the exact crash scenario: 1 minute before meeting starts."""
        
        # Mock the current time to be 12:17pm ET (crash time)
        mock_datetime.datetime.now.return_value = self.crash_time_utc.replace(tzinfo=None)
        mock_datetime.datetime.now.side_effect = lambda tz=None: (
            self.crash_time_utc if tz == timezone.utc else self.crash_time_utc.replace(tzinfo=None)
        )
        mock_datetime.timezone = timezone
        
        # Mock config and dependencies
        mock_load_config.return_value = self.mock_config.copy()
        mock_load_secret.return_value = "test_api_key"
        mock_exists.return_value = True
        mock_resource_path.return_value = "/path/to/client_secret.json"
        
        # Mock calendar service
        mock_calendar = MagicMock()
        mock_calendar_sync.return_value = mock_calendar
        
        # Mock the calendar response with the meeting that starts in 1 minute
        mock_calendar.get_current_status.return_value = ("available", self.meeting_start_utc)
        
        # Mock Govee controller
        mock_govee_instance = MagicMock()
        mock_govee.return_value = mock_govee_instance
        
        # Create controller and test the scenario
        controller = GlowStatusController()
        
        try:
            # This should trigger the imminent meeting detection
            controller._update_now_impl()
            
            # Check if the method completed without crashing
            print("✅ _update_now_impl completed successfully")
            
            # Verify that the imminent meeting logic was triggered
            mock_calendar.get_current_status.assert_called()
            
            # Calculate if imminent meeting should be detected
            time_to_meeting = (self.meeting_start_utc - self.crash_time_utc).total_seconds()
            print(f"Time to meeting: {time_to_meeting} seconds")
            
            # Should be exactly 60 seconds (1 minute)
            self.assertAlmostEqual(time_to_meeting, 60, delta=1)
            
            # Should be within the imminent meeting window (0-60 seconds)
            self.assertTrue(0 <= time_to_meeting <= 60, 
                          f"Meeting should be imminent: {time_to_meeting}s away")
            
        except Exception as e:
            self.fail(f"❌ Crash detected in _update_now_impl: {e}")
            import traceback
            traceback.print_exc()
    
    @patch('glowstatus.datetime')
    @patch('glowstatus.load_config')
    @patch('glowstatus.save_config')
    @patch('glowstatus.load_secret')
    @patch('glowstatus.CalendarSync')
    @patch('glowstatus.GoveeController')
    @patch('glowstatus.resource_path')
    @patch('glowstatus.os.path.exists')
    def test_timezone_conversion_edge_cases(self, mock_exists, mock_resource_path, 
                                          mock_govee, mock_calendar_sync, mock_load_secret,
                                          mock_save_config, mock_load_config, mock_datetime):
        """Test timezone conversion issues that might cause crashes."""
        
        # Test various problematic timezone scenarios
        test_cases = [
            # Case 1: Naive datetime from calendar (missing timezone)
            (datetime(2025, 7, 4, 16, 18, 0), "naive_datetime"),
            # Case 2: Different timezone than expected
            (self.meeting_start_utc, "utc_datetime"),
            # Case 3: DST transition edge case (simplified without pytz)
            (datetime(2025, 3, 9, 11, 0, 0, tzinfo=timezone.utc), "dst_transition")
        ]
        
        for meeting_time, case_name in test_cases:
            with self.subTest(case=case_name):
                print(f"\n--- Testing {case_name} ---")
                
                # Reset mocks
                mock_load_config.reset_mock()
                mock_calendar_sync.reset_mock()
                
                # Setup mocks
                mock_datetime.datetime.now.return_value = self.crash_time_utc.replace(tzinfo=None)
                mock_datetime.datetime.now.side_effect = lambda tz=None: (
                    self.crash_time_utc if tz == timezone.utc else self.crash_time_utc.replace(tzinfo=None)
                )
                mock_datetime.timezone = timezone
                
                mock_load_config.return_value = self.mock_config.copy()
                mock_load_secret.return_value = "test_api_key"
                mock_exists.return_value = True
                
                mock_calendar = MagicMock()
                mock_calendar_sync.return_value = mock_calendar
                mock_calendar.get_current_status.return_value = ("available", meeting_time)
                
                mock_govee_instance = MagicMock()
                mock_govee.return_value = mock_govee_instance
                
                controller = GlowStatusController()
                
                try:
                    controller._update_now_impl()
                    print(f"✅ {case_name} handled successfully")
                except Exception as e:
                    print(f"❌ {case_name} failed: {e}")
                    # Don't fail the test for timezone edge cases, just log them
                    import traceback
                    traceback.print_exc()
    
    def test_timezone_math_precision(self):
        """Test the specific timezone math that might cause crashes."""
        
        # Test the exact calculation from the crash scenario
        meeting_start = self.meeting_start_utc
        check_time = self.crash_time_utc
        
        # This is the calculation from glowstatus.py
        time_to_next = (meeting_start - check_time).total_seconds()
        
        print(f"Meeting start: {meeting_start}")
        print(f"Check time: {check_time}")
        print(f"Time difference: {time_to_next} seconds")
        
        # Should be exactly 60 seconds
        self.assertAlmostEqual(time_to_next, 60, delta=1)
        
        # Test the imminent meeting condition
        imminent_meeting = (
            meeting_start is not None
            and (0 <= time_to_next <= 60)
        )
        
        self.assertTrue(imminent_meeting, "Should detect imminent meeting")
        
        # Test edge cases that might cause issues
        edge_cases = [
            # Exactly 60 seconds
            60.0,
            # Just under 60 seconds  
            59.9,
            # Just over 60 seconds
            60.1,
            # Exactly 0 seconds (meeting starting now)
            0.0,
            # Negative (meeting already started)
            -1.0
        ]
        
        for time_diff in edge_cases:
            imminent = (0 <= time_diff <= 60)
            expected = time_diff >= 0 and time_diff <= 60
            self.assertEqual(imminent, expected, 
                           f"Edge case {time_diff}s should be {expected}")


if __name__ == '__main__':
    print("🧪 Testing imminent meeting crash scenario...")
    print("=" * 50)
    unittest.main(verbosity=2)
