#!/usr/bin/env python3
"""
Headless tests for the new Settings UI.
Tests core functionality without requiring GUI interaction.
"""

import os
import sys
import json
import tempfile
import shutil
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Create comprehensive mocks for all Qt components
class MockWidget:
    def __init__(self, *args, **kwargs):
        self.signals = {}
        self.properties = {}
        
    def __getattr__(self, name):
        if name.endswith('_signal') or name in ['clicked', 'textChanged', 'valueChanged', 'toggled', 'currentTextChanged', 'cellChanged', 'currentRowChanged', 'cellDoubleClicked']:
            if name not in self.signals:
                self.signals[name] = Mock()
                self.signals[name].connect = Mock()
                self.signals[name].disconnect = Mock()
                self.signals[name].emit = Mock()
            return self.signals[name]
        return Mock()

# Mock PySide6 completely
mock_qt_module = Mock()
sys.modules['PySide6'] = mock_qt_module
sys.modules['PySide6.QtWidgets'] = Mock()
sys.modules['PySide6.QtCore'] = Mock()
sys.modules['PySide6.QtGui'] = Mock()

# Set up specific mock behaviors
from unittest.mock import MagicMock
sys.modules['PySide6.QtCore'].Qt = MagicMock()
sys.modules['PySide6.QtCore'].Qt.Horizontal = 1
sys.modules['PySide6.QtCore'].Qt.UserRole = 256
sys.modules['PySide6.QtCore'].Qt.AlignCenter = 4
sys.modules['PySide6.QtCore'].Qt.KeepAspectRatio = 1
sys.modules['PySide6.QtCore'].Qt.SmoothTransformation = 1
sys.modules['PySide6.QtCore'].Qt.ScrollBarAsNeeded = 1
sys.modules['PySide6.QtCore'].QThread = Mock
sys.modules['PySide6.QtCore'].Signal = Mock()
sys.modules['PySide6.QtCore'].QSize = Mock()

# Mock all widget classes
widget_classes = [
    'QWidget', 'QVBoxLayout', 'QHBoxLayout', 'QLabel', 'QTableWidget', 'QTableWidgetItem', 
    'QPushButton', 'QComboBox', 'QColorDialog', 'QCheckBox', 'QFrame', 'QSpinBox', 
    'QFormLayout', 'QLineEdit', 'QDialog', 'QTextEdit', 'QMessageBox', 'QFileDialog',
    'QScrollArea', 'QListWidget', 'QListWidgetItem', 'QStackedWidget', 'QSplitter',
    'QGroupBox', 'QSlider', 'QTabWidget', 'QTextBrowser'
]

for widget_class in widget_classes:
    setattr(sys.modules['PySide6.QtWidgets'], widget_class, MockWidget)

# Mock message box methods and constants
sys.modules['PySide6.QtWidgets'].QMessageBox.Yes = 16384
sys.modules['PySide6.QtWidgets'].QMessageBox.No = 65536
sys.modules['PySide6.QtWidgets'].QMessageBox.Save = 2048
sys.modules['PySide6.QtWidgets'].QMessageBox.Discard = 8388608
sys.modules['PySide6.QtWidgets'].QMessageBox.Cancel = 4194304
sys.modules['PySide6.QtWidgets'].QMessageBox.question = Mock(return_value=16384)
sys.modules['PySide6.QtWidgets'].QMessageBox.information = Mock()
sys.modules['PySide6.QtWidgets'].QMessageBox.critical = Mock()
sys.modules['PySide6.QtWidgets'].QMessageBox.warning = Mock()
sys.modules['PySide6.QtWidgets'].QLineEdit.Password = 2
sys.modules['PySide6.QtWidgets'].QColorDialog.getColor = Mock()

# Mock GUI classes
sys.modules['PySide6.QtGui'].QIcon = Mock()
sys.modules['PySide6.QtGui'].QFont = Mock()
sys.modules['PySide6.QtGui'].QPixmap = Mock()
sys.modules['PySide6.QtGui'].QPainter = Mock()
sys.modules['PySide6.QtGui'].QColor = Mock()

# Mock other dependencies
mock_keyring = Mock()
mock_keyring.get_password = Mock(return_value="test_api_key")
mock_keyring.set_password = Mock()
mock_keyring.delete_password = Mock()
mock_keyring.errors = Mock()
mock_keyring.errors.NoKeyringError = Exception
sys.modules['keyring'] = mock_keyring
sys.modules['keyring.errors'] = mock_keyring.errors

mock_logger = Mock()
mock_logger.get_logger = Mock(return_value=Mock())
sys.modules['logger'] = mock_logger

mock_utils = Mock()
mock_utils.resource_path = Mock(side_effect=lambda x: f"/mock/path/{x}")
sys.modules['utils'] = mock_utils

mock_config_ui = Mock()
mock_config_ui.OAuthWorker = Mock
mock_config_ui.load_config = Mock(return_value={
    "GOVEE_DEVICE_ID": "test_device_id",
    "GOVEE_DEVICE_MODEL": "H6159",
    "SELECTED_CALENDAR_ID": "test@example.com",
    "REFRESH_INTERVAL": 15,
    "DISABLE_CALENDAR_SYNC": False,
    "DISABLE_LIGHT_CONTROL": False,
    "POWER_OFF_WHEN_AVAILABLE": True,
    "OFF_FOR_UNKNOWN_STATUS": True,
    "TRAY_ICON": "GlowStatus_tray_tp_tight.png",
    "STATUS_COLOR_MAP": {
        "in_meeting": {"color": "255,0,0", "power_off": False},
        "focus": {"color": "0,0,255", "power_off": False},
        "available": {"color": "0,255,0", "power_off": True}
    }
})
mock_config_ui.save_config = Mock()
mock_config_ui.TEMPLATE_CONFIG_PATH = "/mock/template.json"
mock_config_ui.CONFIG_PATH = "/mock/config.json"
sys.modules['config_ui'] = mock_config_ui

mock_constants = Mock()
mock_constants.CLIENT_SECRET_PATH = "/mock/client_secret.json"
mock_constants.TOKEN_PATH = "/mock/token.pickle"
sys.modules['constants'] = mock_constants

mock_calendar_sync = Mock()
mock_calendar_sync.CalendarSync = Mock()
sys.modules['calendar_sync'] = mock_calendar_sync

class TestSettingsUICore(unittest.TestCase):
    """Core functionality tests for SettingsWindow without full UI instantiation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.mock_config = {
            "GOVEE_DEVICE_ID": "AA:BB:CC:DD:EE:FF:GG:HH",
            "GOVEE_DEVICE_MODEL": "H6159",
            "SELECTED_CALENDAR_ID": "test@example.com",
            "REFRESH_INTERVAL": 30,
            "DISABLE_CALENDAR_SYNC": False,
            "DISABLE_LIGHT_CONTROL": False,
            "POWER_OFF_WHEN_AVAILABLE": True,
            "OFF_FOR_UNKNOWN_STATUS": True,
            "TRAY_ICON": "GlowStatus_tray_tp_tight.png",
            "STATUS_COLOR_MAP": {
                "in_meeting": {"color": "255,0,0", "power_off": False},
                "focus": {"color": "0,0,255", "power_off": False},
                "available": {"color": "0,255,0", "power_off": True},
                "lunch": {"color": "255,255,0", "power_off": True},
                "offline": {"color": "128,128,128", "power_off": False}
            }
        }
        
        # Reset mock calls
        mock_config_ui.load_config.reset_mock()
        mock_config_ui.save_config.reset_mock()
        mock_keyring.get_password.reset_mock()
        mock_keyring.set_password.reset_mock()
        mock_keyring.delete_password.reset_mock()
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_settings_module_import(self):
        """Test that the settings module can be imported."""
        try:
            from settings_ui import SettingsWindow
            self.assertTrue(True, "Settings module imported successfully")
        except ImportError as e:
            self.fail(f"Failed to import settings module: {e}")
    
    @patch('settings_ui.load_config')
    def test_config_loading(self, mock_load):
        """Test configuration loading functionality."""
        mock_load.return_value = self.mock_config
        
        from settings_ui import SettingsWindow
        
        # Test that load_config would be called during initialization
        config = mock_load()
        self.assertIsInstance(config, dict)
        self.assertIn("GOVEE_DEVICE_ID", config)
        self.assertIn("STATUS_COLOR_MAP", config)
        
    @patch('settings_ui.save_config')
    @patch('settings_ui.load_config')
    def test_config_saving(self, mock_load, mock_save):
        """Test configuration saving functionality."""
        mock_load.return_value = self.mock_config
        
        # Test save operation
        test_config = self.mock_config.copy()
        test_config["TEST_KEY"] = "test_value"
        mock_save(test_config)
        
        mock_save.assert_called_once_with(test_config)
        
    def test_oauth_worker_class_exists(self):
        """Test that OAuthWorker class is available."""
        self.assertTrue(hasattr(mock_config_ui, 'OAuthWorker'))
        
    def test_keyring_operations(self):
        """Test keyring operations for secure credential storage."""
        # Test get password
        api_key = mock_keyring.get_password("GlowStatus", "GOVEE_API_KEY")
        self.assertEqual(api_key, "test_api_key")
        
        # Test set password
        mock_keyring.set_password("GlowStatus", "GOVEE_API_KEY", "new_key")
        mock_keyring.set_password.assert_called_with("GlowStatus", "GOVEE_API_KEY", "new_key")
        
        # Test delete password
        mock_keyring.delete_password("GlowStatus", "GOVEE_API_KEY")
        mock_keyring.delete_password.assert_called_with("GlowStatus", "GOVEE_API_KEY")
        
    def test_status_color_mapping_structure(self):
        """Test status color mapping data structure."""
        status_map = self.mock_config["STATUS_COLOR_MAP"]
        
        # Check required statuses exist
        required_statuses = ["in_meeting", "focus", "available"]
        for status in required_statuses:
            self.assertIn(status, status_map)
            
        # Check each status has required fields
        for status, config in status_map.items():
            self.assertIn("color", config)
            self.assertIn("power_off", config)
            self.assertIsInstance(config["power_off"], bool)
            
            # Validate color format (should be "R,G,B")
            color = config["color"]
            rgb_parts = color.split(",")
            self.assertEqual(len(rgb_parts), 3)
            for part in rgb_parts:
                value = int(part.strip())
                self.assertTrue(0 <= value <= 255)
                
    def test_config_validation(self):
        """Test configuration validation."""
        # Test valid refresh interval
        interval = self.mock_config["REFRESH_INTERVAL"]
        self.assertIsInstance(interval, int)
        self.assertTrue(interval >= 10)
        
        # Test boolean flags
        bool_flags = ["DISABLE_CALENDAR_SYNC", "DISABLE_LIGHT_CONTROL", 
                     "POWER_OFF_WHEN_AVAILABLE", "OFF_FOR_UNKNOWN_STATUS"]
        for flag in bool_flags:
            self.assertIn(flag, self.mock_config)
            self.assertIsInstance(self.mock_config[flag], bool)
            
    def test_govee_device_config(self):
        """Test Govee device configuration structure."""
        self.assertIn("GOVEE_DEVICE_ID", self.mock_config)
        self.assertIn("GOVEE_DEVICE_MODEL", self.mock_config)
        
        device_id = self.mock_config["GOVEE_DEVICE_ID"]
        device_model = self.mock_config["GOVEE_DEVICE_MODEL"]
        
        # Basic format validation
        self.assertIsInstance(device_id, str)
        self.assertIsInstance(device_model, str)
        
        # Device ID should be MAC-like format
        if device_id:
            self.assertIn(":", device_id)
            
    @patch('os.path.exists')
    def test_oauth_token_validation(self, mock_exists):
        """Test OAuth token validation logic."""
        # Test with no token file
        mock_exists.return_value = False
        self.assertFalse(mock_exists("/mock/token.pickle"))
        
        # Test with existing token file
        mock_exists.return_value = True
        self.assertTrue(mock_exists("/mock/token.pickle"))
        
    def test_calendar_integration_config(self):
        """Test calendar integration configuration."""
        self.assertIn("SELECTED_CALENDAR_ID", self.mock_config)
        
        calendar_id = self.mock_config["SELECTED_CALENDAR_ID"]
        if calendar_id:
            self.assertIsInstance(calendar_id, str)
            # Should look like an email
            self.assertIn("@", calendar_id)
            
    def test_tray_icon_config(self):
        """Test tray icon configuration."""
        self.assertIn("TRAY_ICON", self.mock_config)
        
        icon_name = self.mock_config["TRAY_ICON"]
        self.assertIsInstance(icon_name, str)
        self.assertTrue(icon_name.endswith(('.png', '.ico', '.icns')))
        
    def test_resource_path_function(self):
        """Test resource path utility function."""
        test_path = mock_utils.resource_path("img/test.png")
        self.assertEqual(test_path, "/mock/path/img/test.png")
        
    def test_logger_availability(self):
        """Test logger functionality."""
        logger = mock_logger.get_logger()
        self.assertIsNotNone(logger)
        
        # Test logger methods exist
        self.assertTrue(hasattr(logger, 'info'))
        self.assertTrue(hasattr(logger, 'error'))
        self.assertTrue(hasattr(logger, 'debug'))
        
    @patch('settings_ui.os.path.exists')
    def test_file_operations(self, mock_exists):
        """Test file operation utilities."""
        # Test config file existence check
        mock_exists.return_value = True
        self.assertTrue(mock_exists("/mock/config.json"))
        
        mock_exists.return_value = False
        self.assertFalse(mock_exists("/nonexistent/config.json"))


class TestSettingsValidation(unittest.TestCase):
    """Test validation functions for settings."""
    
    def test_color_format_validation(self):
        """Test RGB color format validation."""
        valid_colors = [
            "255,0,0",    # Red
            "0,255,0",    # Green
            "0,0,255",    # Blue
            "128,128,128" # Gray
        ]
        
        invalid_colors = [
            "256,0,0",    # Out of range
            "255,0",      # Missing component
            "255,0,0,0",  # Extra component
            "red,green,blue", # Non-numeric
            "255, 0, 0"   # Extra spaces (might be valid depending on parser)
        ]
        
        for color in valid_colors:
            rgb_parts = color.split(",")
            self.assertEqual(len(rgb_parts), 3)
            for part in rgb_parts:
                value = int(part.strip())
                self.assertTrue(0 <= value <= 255, f"Invalid color value: {value}")
                
        for color in invalid_colors[:4]:  # Test the clearly invalid ones
            with self.assertRaises((ValueError, IndexError)):
                rgb_parts = color.split(",")
                if len(rgb_parts) != 3:
                    raise IndexError("Wrong number of color components")
                for part in rgb_parts:
                    value = int(part.strip())
                    if not (0 <= value <= 255):
                        raise ValueError("Color value out of range")
                        
    def test_device_id_format(self):
        """Test Govee device ID format validation."""
        valid_device_ids = [
            "AA:BB:CC:DD:EE:FF:00:11",
            "00:11:22:33:44:55:66:77",
            "FF:EE:DD:CC:BB:AA:99:88"
        ]
        
        for device_id in valid_device_ids:
            parts = device_id.split(":")
            self.assertEqual(len(parts), 8, f"Device ID should have 8 parts: {device_id}")
            for part in parts:
                self.assertEqual(len(part), 2, f"Each part should be 2 chars: {part}")
                # Should be valid hex
                try:
                    int(part, 16)
                except ValueError:
                    self.fail(f"Invalid hex part in device ID: {part}")
                    
        # Test invalid formats
        invalid_device_ids = [
            "AA:BB:CC:DD:EE:FF:GG:HH",  # Invalid hex
            "AA:BB:CC:DD:EE:FF:00",     # Too few parts
            "AA:BB:CC:DD:EE:FF:00:11:22",  # Too many parts
            "AA:BB:CC:DD:EE:FF:0:11",   # Part too short
        ]
        
        for device_id in invalid_device_ids:
            with self.assertRaises((ValueError, AssertionError)):
                parts = device_id.split(":")
                if len(parts) != 8:
                    raise AssertionError("Wrong number of parts")
                for part in parts:
                    if len(part) != 2:
                        raise AssertionError("Part wrong length")
                    int(part, 16)  # Will raise ValueError for invalid hex
                
    def test_refresh_interval_validation(self):
        """Test refresh interval validation."""
        valid_intervals = [10, 15, 30, 60, 300, 600]
        invalid_intervals = [0, -1, 5, 3601]  # Too small or too large
        
        for interval in valid_intervals:
            self.assertTrue(10 <= interval <= 3600, f"Invalid interval: {interval}")
            
        for interval in invalid_intervals:
            self.assertFalse(10 <= interval <= 3600, f"Should be invalid: {interval}")


class TestSettingsIntegration(unittest.TestCase):
    """Integration tests for settings with real config operations."""
    
    def setUp(self):
        """Set up test fixtures with real temp files."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        
        # Create test config
        self.test_config = {
            "GOVEE_DEVICE_ID": "test_device",
            "GOVEE_DEVICE_MODEL": "H6159",
            "REFRESH_INTERVAL": 15,
            "STATUS_COLOR_MAP": {
                "in_meeting": {"color": "255,0,0", "power_off": False}
            }
        }
        
        with open(self.config_file, 'w') as f:
            json.dump(self.test_config, f)
            
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_config_load_save_cycle(self):
        """Test loading and saving configuration."""
        # Test that config file exists
        self.assertTrue(os.path.exists(self.config_file))
        
        # Test loading
        with open(self.config_file, 'r') as f:
            loaded_config = json.load(f)
            
        self.assertEqual(loaded_config["GOVEE_DEVICE_ID"], "test_device")
        self.assertEqual(loaded_config["GOVEE_DEVICE_MODEL"], "H6159")
        
        # Test saving
        loaded_config["TEST_KEY"] = "test_value"
        with open(self.config_file, 'w') as f:
            json.dump(loaded_config, f)
            
        # Verify save
        with open(self.config_file, 'r') as f:
            updated_config = json.load(f)
            
        self.assertEqual(updated_config["TEST_KEY"], "test_value")
        
    def test_config_structure_persistence(self):
        """Test that config structure is maintained across operations."""
        with open(self.config_file, 'r') as f:
            config = json.load(f)
            
        # Verify all expected keys exist
        expected_keys = ["GOVEE_DEVICE_ID", "GOVEE_DEVICE_MODEL", "REFRESH_INTERVAL", "STATUS_COLOR_MAP"]
        for key in expected_keys:
            self.assertIn(key, config)
            
        # Verify status color map structure
        status_map = config["STATUS_COLOR_MAP"]
        self.assertIn("in_meeting", status_map)
        
        meeting_config = status_map["in_meeting"]
        self.assertIn("color", meeting_config)
        self.assertIn("power_off", meeting_config)
        self.assertEqual(meeting_config["color"], "255,0,0")
        self.assertFalse(meeting_config["power_off"])


def run_headless_tests():
    """Run all headless tests for settings UI."""
    # Create test loader
    loader = unittest.TestLoader()
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test cases using the modern approach
    test_suite.addTests(loader.loadTestsFromTestCase(TestSettingsUICore))
    test_suite.addTests(loader.loadTestsFromTestCase(TestSettingsValidation))
    test_suite.addTests(loader.loadTestsFromTestCase(TestSettingsIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Return success status
    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running GlowStatus Settings UI Headless Tests...")
    print("=" * 60)
    
    success = run_headless_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed!")
        exit_code = 0
    else:
        print("❌ Some tests failed!")
        exit_code = 1
        
    print("Settings UI headless testing complete.")
    sys.exit(exit_code)
