import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import (
    clamp_rgb,
    normalize_status,
    is_valid_govee_api_key,
    is_valid_govee_device_id,
    is_valid_govee_device_model,
    is_valid_google_calendar_id,
)

class TestUtils(unittest.TestCase):
    def test_clamp_rgb(self):
        self.assertEqual(clamp_rgb(300, -10, 128), (255, 0, 128))
        self.assertEqual(clamp_rgb(0, 0, 0), (0, 0, 0))
        self.assertEqual(clamp_rgb(255, 255, 255), (255, 255, 255))

    def test_normalize_status(self):
        self.assertEqual(normalize_status("Focus Time"), "focus")
        self.assertEqual(normalize_status("Deep Focus"), "focus")
        self.assertEqual(normalize_status("Team Meeting"), "in_meeting")
        self.assertEqual(normalize_status("Call with client"), "in_meeting")
        self.assertEqual(normalize_status("1:1 Meeting"), "in_meeting")
        self.assertEqual(normalize_status("Available"), "available")
        self.assertEqual(normalize_status("Random Event"), "in_meeting")  # Default fallback

    def test_is_valid_govee_api_key(self):
        self.assertTrue(is_valid_govee_api_key("a" * 32))
        self.assertFalse(is_valid_govee_api_key(""))
        self.assertFalse(is_valid_govee_api_key("short"))

    def test_is_valid_govee_device_id(self):
        self.assertTrue(is_valid_govee_device_id("AB:CD:EF:12:34:56:78:90"))
        self.assertFalse(is_valid_govee_device_id("ABC1234567"))
        self.assertFalse(is_valid_govee_device_id(""))

    def test_is_valid_govee_device_model(self):
        self.assertTrue(is_valid_govee_device_model("H6159"))
        self.assertTrue(is_valid_govee_device_model("H6001"))
        self.assertFalse(is_valid_govee_device_model("6159"))  # Should start with letter
        self.assertFalse(is_valid_govee_device_model(""))
        self.assertFalse(is_valid_govee_device_model("H61@#"))  # Invalid characters

    def test_is_valid_google_calendar_id(self):
        self.assertTrue(is_valid_google_calendar_id("primary"))
        self.assertTrue(is_valid_google_calendar_id("user@example.com"))
        self.assertTrue(is_valid_google_calendar_id("abc123@group.calendar.google.com"))
        self.assertFalse(is_valid_google_calendar_id("not-an-email"))
        self.assertFalse(is_valid_google_calendar_id(""))

if __name__ == "__main__":
    unittest.main()