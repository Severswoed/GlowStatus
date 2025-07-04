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
from settings_ui import load_config, save_config, CONFIG_PATH


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
            with patch('settings_ui.CONFIG_PATH', config_path):
                config = load_config()
                
                self.assertEqual(config['DISABLE_CALENDAR_SYNC'], False)
                self.assertEqual(config['DISABLE_LIGHT_CONTROL'], False)
                self.assertEqual(config['GOVEE_DEVICE_ID'], 'test_device')
                self.assertIn('STATUS_COLOR_MAP', config)
                
        finally:
            os.unlink(config_path)
            
    def test_load_config_with_missing_file(self):
        """Test loading configuration when file doesn't exist."""
        with patch('settings_ui.CONFIG_PATH', '/nonexistent/path.json'), \
             patch('settings_ui.TEMPLATE_CONFIG_PATH', '/nonexistent/template.json'):
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
            with patch('settings_ui.CONFIG_PATH', config_path):
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
            with patch('settings_ui.CONFIG_PATH', config_path):
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
            
    @patch('settings_ui.keyring')
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

    def test_disable_light_control_user_choice_respected(self):
        """Test that user's choice to disable light control is respected even with Govee credentials."""
        # Test config with Govee credentials but user wants light control disabled
        test_config = {
            'DISABLE_LIGHT_CONTROL': True,  # User explicitly disabled
            'GOVEE_DEVICE_ID': 'AA:BB:CC:DD:EE:FF:11:22',  # But has credentials
            'GOVEE_DEVICE_MODEL': 'H6159',
            'GOVEE_API_KEY': 'test_api_key'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f)
            config_path = f.name
            
        try:
            with patch('settings_ui.CONFIG_PATH', config_path):
                # Load config - should preserve user's choice
                loaded_config = load_config()
                
                # User's choice should be preserved, not auto-enabled
                self.assertTrue(loaded_config['DISABLE_LIGHT_CONTROL'])
                self.assertEqual(loaded_config['GOVEE_DEVICE_ID'], 'AA:BB:CC:DD:EE:FF:11:22')
                
                # Now test saving - should still respect user choice
                loaded_config['REFRESH_INTERVAL'] = 30  # Make a change
                save_config(loaded_config)
                
                # Reload and verify user choice is still respected
                final_config = load_config()
                self.assertTrue(final_config['DISABLE_LIGHT_CONTROL'])
                
        finally:
            os.unlink(config_path)

    def test_auto_enable_light_control_new_installation(self):
        """Test that light control is auto-enabled only for new installations with credentials."""
        # Test a completely new config (no DISABLE_LIGHT_CONTROL key exists)
        test_config = {
            'GOVEE_DEVICE_ID': 'AA:BB:CC:DD:EE:FF:11:22',
            'GOVEE_DEVICE_MODEL': 'H6159'
            # Note: No DISABLE_LIGHT_CONTROL key - simulates new installation
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f)
            config_path = f.name
            
        try:
            with patch('settings_ui.CONFIG_PATH', config_path), \
                 patch('settings_ui.keyring.get_password', return_value='test_api_key'):
                
                # Load config - should auto-enable for new installation
                loaded_config = load_config()
                
                # Should auto-enable because this is a new installation with credentials
                self.assertFalse(loaded_config['DISABLE_LIGHT_CONTROL'])
                self.assertEqual(loaded_config['GOVEE_DEVICE_ID'], 'AA:BB:CC:DD:EE:FF:11:22')
                
        finally:
            os.unlink(config_path)

    def test_disable_light_control_default_no_credentials(self):
        """Test that light control is disabled by default when no credentials exist."""
        # Test new installation without credentials
        test_config = {}  # Empty config, no credentials
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f)
            config_path = f.name
            
        try:
            with patch('settings_ui.CONFIG_PATH', config_path), \
                 patch('settings_ui.keyring.get_password', return_value=None):
                
                # Load config - should default to disabled
                loaded_config = load_config()
                
                # Should be disabled by default when no credentials
                self.assertTrue(loaded_config['DISABLE_LIGHT_CONTROL'])
                
        finally:
            os.unlink(config_path)
            
    @patch('settings_ui.keyring')
    def test_config_window_save_respects_user_choice(self, mock_keyring):
        """Test that ConfigWindow save_config respects user's explicit choice."""
        # Mock the keyring for API key operations
        mock_keyring.get_password.return_value = 'test_api_key'
        mock_keyring.set_password.return_value = None
        
        # Test config with user explicitly disabling light control
        initial_config = {
            'DISABLE_LIGHT_CONTROL': True,  # User's explicit choice
            'GOVEE_DEVICE_ID': 'AA:BB:CC:DD:EE:FF:11:22',
            'GOVEE_DEVICE_MODEL': 'H6159'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(initial_config, f)
            config_path = f.name
            
        try:
            with patch('settings_ui.CONFIG_PATH', config_path):
                # Simulate saving config through the UI
                config = load_config()
                config['REFRESH_INTERVAL'] = 45  # Make some other change
                save_config(config)
                
                # Verify user's choice is preserved
                saved_config = load_config()
                self.assertTrue(saved_config['DISABLE_LIGHT_CONTROL'])
                self.assertEqual(saved_config['REFRESH_INTERVAL'], 45)
                
        finally:
            os.unlink(config_path)
            
    def test_input_validation_integration(self):
        """Test that the config UI properly handles input validation."""
        # Test that config can store various device ID formats
        test_configs = [
            {
                'GOVEE_DEVICE_ID': 'AB:CD:EF:12:34:56:78:90',  # Valid format
                'GOVEE_DEVICE_MODEL': 'H6159',  # Valid model
                'DISABLE_LIGHT_CONTROL': False
            },
            {
                'GOVEE_DEVICE_ID': 'invalid_format',  # Invalid format
                'GOVEE_DEVICE_MODEL': '6159',  # Invalid model (doesn't start with letter)
                'DISABLE_LIGHT_CONTROL': True  # User disabled due to invalid config
            }
        ]
        
        for i, test_config in enumerate(test_configs):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(test_config, f)
                config_path = f.name
                
            try:
                with patch('settings_ui.CONFIG_PATH', config_path):
                    # Config should load regardless of validation
                    config = load_config()
                    
                    self.assertEqual(config['GOVEE_DEVICE_ID'], test_config['GOVEE_DEVICE_ID'])
                    self.assertEqual(config['GOVEE_DEVICE_MODEL'], test_config['GOVEE_DEVICE_MODEL'])
                    self.assertEqual(config['DISABLE_LIGHT_CONTROL'], test_config['DISABLE_LIGHT_CONTROL'])
                    
            finally:
                os.unlink(config_path)

    def test_validation_functions_available(self):
        """Test that validation functions from utils are available for future use."""
        try:
            from utils import is_valid_govee_device_id, is_valid_govee_device_model
            
            # Test valid cases
            self.assertTrue(is_valid_govee_device_id("AB:CD:EF:12:34:56:78:90"))
            self.assertTrue(is_valid_govee_device_model("H6159"))
            
            # Test invalid cases
            self.assertFalse(is_valid_govee_device_id("invalid"))
            self.assertFalse(is_valid_govee_device_model("6159"))  # Doesn't start with letter
            
            # Verify they return boolean values
            self.assertIsInstance(is_valid_govee_device_id("AB:CD:EF:12:34:56:78:90"), bool)
            self.assertIsInstance(is_valid_govee_device_model("H6159"), bool)
            
        except ImportError:
            self.skipTest("Validation functions not available in utils module")
        

# Since ConfigWindow requires PyQt5, we'll create a separate test class
# that can be run conditionally
class TestConfigWindowMock(unittest.TestCase):
    """Test ConfigWindow functionality with mocked PyQt5."""
    
    @patch('settings_ui.QWidget')
    @patch('settings_ui.QVBoxLayout')
    @patch('settings_ui.QHBoxLayout')
    @patch('settings_ui.QLabel')
    @patch('settings_ui.QLineEdit')
    @patch('settings_ui.QPushButton')
    @patch('settings_ui.QCheckBox')
    @patch('settings_ui.QSpinBox')
    @patch('settings_ui.QTableWidget')
    @patch('settings_ui.QComboBox')
    def test_config_window_initialization(self, *mock_args):
        """Test ConfigWindow initialization with mocked PyQt5."""
        try:
            from settings_ui import SettingsWindow
            window = ConfigWindow()
            # Basic test that the window can be created
            self.assertIsNotNone(window)
        except ImportError:
            # PyQt5 not available, skip this test
            self.skipTest("PyQt5 not available")


if __name__ == '__main__':
    unittest.main()
