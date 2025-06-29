#!/usr/bin/env python3
"""Tests for calendar sync functionality."""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta, timezone

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from calendar_sync import ensure_aware


class TestCalendarSync(unittest.TestCase):
    """Test CalendarSync functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calendar_id = "test@example.com"
        
    def test_ensure_aware(self):
        """Test timezone awareness functionality."""
        # Test naive datetime
        naive_dt = datetime(2025, 1, 10, 14, 30)
        aware_dt = ensure_aware(naive_dt)
        self.assertIsNotNone(aware_dt.tzinfo)
        
        # Test already aware datetime
        already_aware = datetime(2025, 1, 10, 14, 30, tzinfo=timezone.utc)
        result = ensure_aware(already_aware)
        self.assertEqual(result, already_aware)
        
    @patch('calendar_sync.os.path.exists')
    @patch('calendar_sync.build')
    @patch('calendar_sync.InstalledAppFlow')
    def test_calendar_sync_initialization(self, mock_flow, mock_build, mock_exists):
        """Test CalendarSync initialization."""
        mock_exists.return_value = False  # No token file exists
        
        from calendar_sync import CalendarSync
        sync = CalendarSync(self.calendar_id)
        self.assertEqual(sync.calendar_id, self.calendar_id)
        
    @patch('calendar_sync.os.path.exists')
    @patch('calendar_sync.build')
    @patch('calendar_sync.InstalledAppFlow')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('calendar_sync.pickle.load')
    def test_get_service_with_token(self, mock_pickle, mock_open_func, mock_flow, mock_build, mock_exists):
        """Test getting service with existing token."""
        mock_exists.return_value = True
        mock_creds = MagicMock()
        mock_creds.valid = True
        mock_pickle.return_value = mock_creds
        
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        
        from calendar_sync import CalendarSync
        sync = CalendarSync(self.calendar_id)
        service = sync._get_service()
        
        # Should be called at least once during initialization and _get_service
        self.assertTrue(mock_build.called)
        self.assertIsNotNone(service)
        
    @patch('calendar_sync.os.path.exists')
    @patch('calendar_sync.build')
    @patch('calendar_sync.InstalledAppFlow')
    def test_get_current_status_no_events(self, mock_flow, mock_build, mock_exists):
        """Test getting current status when no events are happening."""
        mock_exists.return_value = False
        mock_service = MagicMock()
        mock_service.events().list().execute.return_value = {'items': []}
        
        from calendar_sync import CalendarSync
        sync = CalendarSync(self.calendar_id)
        sync.service = mock_service
        
        status = sync.get_current_status()
        self.assertEqual(status, "available")
        
    @patch('calendar_sync.os.path.exists')
    @patch('calendar_sync.build')
    @patch('calendar_sync.InstalledAppFlow')
    def test_get_current_status_with_meeting(self, mock_flow, mock_build, mock_exists):
        """Test getting current status during a meeting."""
        mock_exists.return_value = False
        now = datetime.now(timezone.utc)
        
        # Create a mock event that's currently happening
        mock_event = {
            'summary': 'Team Meeting',
            'start': {'dateTime': (now - timedelta(minutes=15)).isoformat()},
            'end': {'dateTime': (now + timedelta(minutes=15)).isoformat()}
        }
        
        mock_service = MagicMock()
        mock_service.events().list().execute.return_value = {'items': [mock_event]}
        
        from calendar_sync import CalendarSync
        sync = CalendarSync(self.calendar_id)
        sync.service = mock_service
        
        status = sync.get_current_status()
        self.assertEqual(status, "in_meeting")
        
    @patch('calendar_sync.os.path.exists')
    @patch('calendar_sync.build')
    @patch('calendar_sync.InstalledAppFlow')
    def test_get_current_status_with_custom_color_map(self, mock_flow, mock_build, mock_exists):
        """Test getting current status with custom color mapping."""
        mock_exists.return_value = False
        now = datetime.now(timezone.utc)
        
        # Create a mock event with a custom status keyword
        mock_event = {
            'summary': 'Deep work session',
            'start': {'dateTime': (now - timedelta(minutes=15)).isoformat()},
            'end': {'dateTime': (now + timedelta(minutes=15)).isoformat()}
        }
        
        mock_service = MagicMock()
        mock_service.events().list().execute.return_value = {'items': [mock_event]}
        
        custom_color_map = {
            'deep work': {'color': '128,0,128', 'power_off': False},
            'in_meeting': {'color': '255,0,0', 'power_off': False}
        }
        
        from calendar_sync import CalendarSync
        sync = CalendarSync(self.calendar_id)
        sync.service = mock_service
        
        status = sync.get_current_status(color_map=custom_color_map)
        self.assertEqual(status, "deep work")
        
    @patch('calendar_sync.os.path.exists')
    @patch('calendar_sync.build')
    @patch('calendar_sync.InstalledAppFlow')
    def test_get_all_calendars(self, mock_flow, mock_build, mock_exists):
        """Test getting all calendars."""
        mock_exists.return_value = False
        mock_calendars = {
            'items': [
                {'id': 'primary', 'summary': 'Primary Calendar'},
                {'id': 'work@example.com', 'summary': 'Work Calendar'}
            ]
        }
        
        mock_service = MagicMock()
        mock_service.calendarList().list().execute.return_value = mock_calendars
        
        from calendar_sync import CalendarSync
        sync = CalendarSync(self.calendar_id)
        sync.service = mock_service
        
        calendars = sync.get_all_calendars()
        self.assertEqual(len(calendars), 2)
        self.assertEqual(calendars[0]['id'], 'primary')
        self.assertEqual(calendars[1]['id'], 'work@example.com')


if __name__ == '__main__':
    unittest.main()
