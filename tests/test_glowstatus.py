#!/usr/bin/env python3
"""Tests for main GlowStatus application logic."""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock PySide6 to avoid Qt/OpenGL dependencies in headless environment
sys.modules['PySide6'] = MagicMock()
sys.modules['PySide6.QtWidgets'] = MagicMock()
sys.modules['PySide6.QtCore'] = MagicMock()
sys.modules['PySide6.QtGui'] = MagicMock()
sys.modules['PySide6.QtSystemTrayIcon'] = MagicMock()

# Since glowstatus.py might not have all functions exposed, we'll test what we can


class TestGlowStatusLogic(unittest.TestCase):
    """Test main GlowStatus application logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_config = {
            'DISABLE_CALENDAR_SYNC': False,
            'DISABLE_LIGHT_CONTROL': False,
            'SELECTED_CALENDAR_ID': 'primary',
            'GOVEE_API_KEY': 'test_key',
            'GOVEE_DEVICE_ID': 'AA:BB:CC:DD:EE:FF:11:22',
            'GOVEE_DEVICE_MODEL': 'H6159',
            'STATUS_COLOR_MAP': {
                'in_meeting': {'color': '255,0,0', 'power_off': False},
                'focus': {'color': '0,0,255', 'power_off': False},
                'available': {'color': '0,255,0', 'power_off': True}
            },
            'REFRESH_INTERVAL': 60
        }
        
    def test_import_glowstatus(self):
        """Test that glowstatus module can be imported."""
        try:
            import glowstatus
            self.assertTrue(True)  # Import successful
        except ImportError as e:
            self.fail(f"Could not import glowstatus: {e}")
            
    @patch('config_ui.load_config')
    def test_config_integration(self, mock_load_config):
        """Test integration with config loading."""
        mock_load_config.return_value = self.sample_config
        
        # Test that config can be loaded
        from settings_ui import load_config
        config = load_config()
        
        self.assertEqual(config['DISABLE_CALENDAR_SYNC'], False)
        self.assertEqual(config['DISABLE_LIGHT_CONTROL'], False)
        self.assertIn('STATUS_COLOR_MAP', config)


if __name__ == '__main__':
    unittest.main()
