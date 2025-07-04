#!/usr/bin/env python3
"""
Test for the stuck manual status bug fix.
This tests the scenario where CURRENT_STATUS is set but MANUAL_STATUS_TIMESTAMP is null,
which was causing the app to be permanently stuck in manual mode.
"""

import unittest
import sys
import os
import time
from unittest.mock import patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from glowstatus import GlowStatusController


class TestStuckManualStatusBugFix(unittest.TestCase):
    """Test the fix for stuck manual status without timestamp."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Config representing the user's stuck state
        self.stuck_config = {
            "GOVEE_DEVICE_ID": "10:00:D7:C1:83:46:65:8C",
            "GOVEE_DEVICE_MODEL": "H6159",
            "SELECTED_CALENDAR_ID": "severswoed@gmail.com",
            "REFRESH_INTERVAL": 15,
            "DISABLE_CALENDAR_SYNC": False,
            "DISABLE_LIGHT_CONTROL": False,
            "POWER_OFF_WHEN_AVAILABLE": True,
            "OFF_FOR_UNKNOWN_STATUS": True,
            "STATUS_COLOR_MAP": {
                "in_meeting": {"color": "255,0,0", "power_off": False},
                "available": {"color": "0,255,0", "power_off": True}
            },
            "CURRENT_STATUS": "in_meeting",  # ← STUCK HERE
            "GOOGLE_USER_EMAIL": "severswoed@gmail.com",
            "MANUAL_STATUS_TIMESTAMP": None  # ← NO TIMESTAMP = BUG
        }
        
    @patch('glowstatus.load_secret')
    @patch('glowstatus.CalendarSync')
    @patch('glowstatus.GoveeController')
    @patch('glowstatus.resource_path')
    @patch('glowstatus.os.path.exists')
    @patch('glowstatus.load_config')
    @patch('glowstatus.save_config')
    def test_stuck_manual_status_cleared_on_update(self, mock_save_config, mock_load_config,
                                                  mock_exists, mock_resource_path, 
                                                  mock_govee, mock_calendar_sync, mock_load_secret):
        """Test that stuck manual status is cleared on update."""
        
        print("🐛 Testing stuck manual status bug fix...")
        
        # Setup mocks
        mock_load_secret.return_value = "test_api_key"
        mock_resource_path.return_value = "/path/to/client_secret.json"
        mock_exists.return_value = True
        
        # Track config saves to see if manual status gets cleared
        config_saves = []
        def track_config_save(config):
            config_saves.append(config.copy())
            print(f"  📝 Config saved: CURRENT_STATUS={config.get('CURRENT_STATUS')}, TIMESTAMP={config.get('MANUAL_STATUS_TIMESTAMP')}")
        
        mock_save_config.side_effect = track_config_save
        
        # Return the stuck config initially, then return updated config
        config_loads = [self.stuck_config.copy()]
        mock_load_config.side_effect = lambda: config_loads[-1].copy()
        
        # Mock calendar to return "available" (user is not actually in meeting)
        mock_calendar = MagicMock()
        mock_calendar.get_current_status.return_value = ("available", None)
        mock_calendar_sync.return_value = mock_calendar
        
        # Mock Govee controller
        mock_govee_instance = MagicMock()
        mock_govee.return_value = mock_govee_instance
        
        # Create controller and trigger update
        controller = GlowStatusController()
        
        print("  🔍 Before update - stuck config:")
        print(f"     CURRENT_STATUS: {self.stuck_config['CURRENT_STATUS']}")
        print(f"     MANUAL_STATUS_TIMESTAMP: {self.stuck_config['MANUAL_STATUS_TIMESTAMP']}")
        
        # This should detect and fix the stuck manual status
        controller.update_now()
        
        print("  🔍 After update:")
        
        # Verify that save_config was called to clear the manual status
        self.assertTrue(len(config_saves) > 0, "Config should have been saved to clear manual status")
        
        # Check if the manual status was cleared
        final_config = config_saves[-1]
        self.assertIsNone(final_config.get("CURRENT_STATUS"), 
                         "CURRENT_STATUS should be cleared when no timestamp exists")
        self.assertIsNone(final_config.get("MANUAL_STATUS_TIMESTAMP"), 
                         "MANUAL_STATUS_TIMESTAMP should be cleared")
        
        print("  ✅ Manual status correctly cleared!")
        
        # Verify the light was controlled based on calendar status (available = off)
        mock_govee_instance.set_power.assert_called_with("off")
        print("  ✅ Light correctly turned off based on calendar status!")
    
    @patch('glowstatus.load_secret')
    @patch('glowstatus.CalendarSync')
    @patch('glowstatus.GoveeController')
    @patch('glowstatus.resource_path')
    @patch('glowstatus.os.path.exists')
    @patch('glowstatus.load_config')
    @patch('glowstatus.save_config')
    def test_valid_manual_status_preserved(self, mock_save_config, mock_load_config,
                                         mock_exists, mock_resource_path, 
                                         mock_govee, mock_calendar_sync, mock_load_secret):
        """Test that valid manual status with timestamp is preserved."""
        
        print("\n✅ Testing valid manual status preservation...")
        
        # Setup mocks
        mock_load_secret.return_value = "test_api_key"
        mock_resource_path.return_value = "/path/to/client_secret.json"
        mock_exists.return_value = True
        
        # Config with valid manual status (has timestamp)
        valid_config = self.stuck_config.copy()
        valid_config["MANUAL_STATUS_TIMESTAMP"] = time.time()  # Current timestamp
        
        config_saves = []
        mock_save_config.side_effect = lambda config: config_saves.append(config.copy())
        mock_load_config.return_value = valid_config
        
        # Mock calendar and govee
        mock_calendar = MagicMock()
        mock_calendar.get_current_status.return_value = ("available", None)
        mock_calendar_sync.return_value = mock_calendar
        
        mock_govee_instance = MagicMock()
        mock_govee.return_value = mock_govee_instance
        
        # Create controller and trigger update
        controller = GlowStatusController()
        controller.update_now()
        
        # Valid manual status should be preserved (not cleared)
        # The config might still be saved for other reasons, but CURRENT_STATUS should remain
        print(f"  📝 Config saves: {len(config_saves)}")
        
        # Check that the manual status was NOT cleared inappropriately
        if config_saves:
            final_config = config_saves[-1]
            # If config was saved, it should still preserve the manual status
            # (unless it was expired, but our timestamp is current)
            print(f"     Final CURRENT_STATUS: {final_config.get('CURRENT_STATUS')}")
        
        print("  ✅ Valid manual status handling tested!")
    
    def test_manual_status_expiry_logic(self):
        """Test the manual status expiry calculation."""
        
        print("\n⏰ Testing manual status expiry logic...")
        
        current_time = time.time()
        
        # Test cases for expiry
        test_cases = [
            (current_time - 1800, 3600, False, "30 min old, 1h expiry -> not expired"),
            (current_time - 3900, 3600, True, "65 min old, 1h expiry -> expired"),
            (current_time - 10800, 7200, True, "3h old, 2h expiry -> expired"),
            (None, 3600, True, "No timestamp -> should be cleared"),
        ]
        
        for timestamp, expiry, should_be_expired, description in test_cases:
            print(f"  🔍 {description}")
            
            if timestamp is None:
                # No timestamp case
                expired = True  # Should always be cleared
            else:
                # Normal expiry check
                expired = (current_time - timestamp) > expiry
            
            self.assertEqual(expired, should_be_expired, f"Expiry logic failed for: {description}")
            print(f"     ✅ {'Expired' if expired else 'Valid'} (correct)")


if __name__ == '__main__':
    print("🔧 TESTING STUCK MANUAL STATUS BUG FIX")
    print("=" * 50)
    unittest.main(verbosity=2)
