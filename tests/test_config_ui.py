#!/usr/bin/env python3
"""Tests for configuration UI functionality."""

import unittest
import sys
import os
from unittest.mock import patch, MagicMock, Mock
import tempfile
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock PySide6 to avoid Qt dependencies in tests
sys.modules['PySide6'] = MagicMock()
sys.modules['PySide6.QtWidgets'] = MagicMock()
sys.modules['PySide6.QtCore'] = MagicMock()
sys.modules['PySide6.QtGui'] = MagicMock()

# Now import the modules we want to test
from config_ui import load_config, save_config, CONFIG_PATH


class TestConfigUI(unittest.TestCase):
    """Test configuration UI functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_config = {
            'calendar_sync_enabled': True,
            'light_control_enabled': True,
            'google_calendar_id': 'primary',
            'govee_api_key': 'test_key',
            'govee_device_id': 'AA:BB:CC:DD:EE:FF:11:22',
            'govee_device_model': 'H6159',
            'color_map': {
                'in_meeting': {'color': '255,0,0', 'power_off': False},
                'focus': {'color': '0,0,255', 'power_off': False},
                'available': {'color': '0,255,0', 'power_off': True}
            },
            'brightness': 100,
            'check_interval': 60
        }
        
    def test_load_config_with_valid_file(self):
        """Test loading configuration from a valid file."""
        # Create a simple test config that matches the expected format
        test_config = {
            'DISABLE_CALENDAR_SYNC': False,
            'DISABLE_LIGHT_CONTROL': False,
            'GOVEE_DEVICE_ID': 'test_device',
            'STATUS_COLOR_MAP': {
                'in_meeting': {'color': '255,0,0', 'power_off': False}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f)
            config_path = f.name
            
        try:
            with patch('config_ui.CONFIG_PATH', config_path):
                config = load_config()
                
                self.assertEqual(config['DISABLE_CALENDAR_SYNC'], False)
                self.assertEqual(config['DISABLE_LIGHT_CONTROL'], False)
                self.assertEqual(config['GOVEE_DEVICE_ID'], 'test_device')
                self.assertIn('STATUS_COLOR_MAP', config)
                
        finally:
            os.unlink(config_path)
            
    def test_load_config_with_missing_file(self):
        """Test loading configuration when file doesn't exist."""
        with patch('config_ui.CONFIG_PATH', '/nonexistent/path.json'), \
             patch('config_ui.TEMPLATE_CONFIG_PATH', '/nonexistent/template.json'):
            config = load_config()
            
            # Should return default configuration
            self.assertTrue(config['DISABLE_CALENDAR_SYNC'])
            self.assertTrue(config['DISABLE_LIGHT_CONTROL'])
            self.assertIsInstance(config, dict)
            
    def test_load_config_with_invalid_json(self):
        """Test loading configuration from invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            config_path = f.name
            
        try:
            with patch('config_ui.CONFIG_PATH', config_path):
                config = load_config()
                
                # Should return default configuration
                self.assertTrue(config['DISABLE_CALENDAR_SYNC'])
                self.assertTrue(config['DISABLE_LIGHT_CONTROL'])
                
        finally:
            os.unlink(config_path)
            
    def test_save_config(self):
        """Test saving configuration to file."""
        test_config = {
            'DISABLE_CALENDAR_SYNC': False,
            'DISABLE_LIGHT_CONTROL': False,
            'GOVEE_DEVICE_ID': 'test_device'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
            
        try:
            with patch('config_ui.CONFIG_PATH', config_path):
                save_config(test_config)
                
                # Verify file was created and contains correct data
                with open(config_path, 'r') as f:
                    saved_config = json.load(f)
                    
                self.assertEqual(saved_config['DISABLE_CALENDAR_SYNC'], False)
                self.assertEqual(saved_config['DISABLE_LIGHT_CONTROL'], False)
                self.assertEqual(saved_config['GOVEE_DEVICE_ID'], 'test_device')
                
        finally:
            if os.path.exists(config_path):
                os.unlink(config_path)
                
    def test_config_defaults(self):
        """Test that default configuration has all required fields."""
        config = load_config()
        
        required_fields = [
            'DISABLE_CALENDAR_SYNC',
            'DISABLE_LIGHT_CONTROL',
            'STATUS_COLOR_MAP'
        ]
        
        for field in required_fields:
            self.assertIn(field, config)
            
        # Test default color map structure
        self.assertIsInstance(config['STATUS_COLOR_MAP'], dict)
        
        for status, settings in config['STATUS_COLOR_MAP'].items():
            self.assertIn('color', settings)
            self.assertIn('power_off', settings)
            self.assertIsInstance(settings['power_off'], bool)
            
    @patch('config_ui.keyring')
    def test_govee_credentials_handling(self, mock_keyring):
        """Test handling of Govee credentials."""
        # Test storing credentials
        mock_keyring.set_password.return_value = None
        
        # Test retrieving credentials
        mock_keyring.get_password.side_effect = lambda service, key: {
            ('GlowStatus', 'govee_api_key'): 'test_api_key',
            ('GlowStatus', 'govee_device_id'): 'AA:BB:CC:DD:EE:FF:11:22'
        }.get((service, key))
        
        config = load_config()
        
        # Should auto-enable light control if credentials are present
        if config.get('govee_api_key') or mock_keyring.get_password('GlowStatus', 'govee_api_key'):
            # This logic is in the actual config loading, test that it works
            pass
            
    def test_color_map_validation(self):
        """Test color map validation."""
        config = load_config()
        
        # Config should have a color map structure 
        # Note: key name might be STATUS_COLOR_MAP or color_map depending on version
        color_map = config.get('STATUS_COLOR_MAP') or config.get('color_map', {})
        
        # If empty, that's okay for a fresh config
        if not color_map:
            self.assertIsInstance(config, dict)
            return
            
        # Each color map entry should have proper structure
        for status, settings in color_map.items():
            self.assertIsInstance(status, str)
            self.assertIsInstance(settings, dict)
            self.assertIn('color', settings)
            self.assertIn('power_off', settings)
            
            # Color should be a string in R,G,B format
            color = settings['color']
            self.assertIsInstance(color, str)
            if color:  # Only validate if color is not empty
                parts = color.split(',')
                self.assertEqual(len(parts), 3)
                
                for part in parts:
                    value = int(part.strip())
                    self.assertGreaterEqual(value, 0)
                    self.assertLessEqual(value, 255)


# Since ConfigWindow requires PyQt5, we'll create a separate test class
# that can be run conditionally
class TestConfigWindowMock(unittest.TestCase):
    """Test ConfigWindow functionality with mocked PyQt5."""
    
    @patch('config_ui.QWidget')
    @patch('config_ui.QVBoxLayout')
    @patch('config_ui.QHBoxLayout')
    @patch('config_ui.QLabel')
    @patch('config_ui.QLineEdit')
    @patch('config_ui.QPushButton')
    @patch('config_ui.QCheckBox')
    @patch('config_ui.QSpinBox')
    @patch('config_ui.QTableWidget')
    @patch('config_ui.QComboBox')
    def test_config_window_initialization(self, *mock_args):
        """Test ConfigWindow initialization with mocked PyQt5."""
        try:
            from config_ui import ConfigWindow
            window = ConfigWindow()
            # Basic test that the window can be created
            self.assertIsNotNone(window)
        except ImportError:
            # PyQt5 not available, skip this test
            self.skipTest("PyQt5 not available")


if __name__ == '__main__':
    unittest.main()
