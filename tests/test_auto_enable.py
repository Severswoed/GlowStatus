#!/usr/bin/env python3
"""Test script to verify auto-enable light control logic."""

import sys
import os
import json
import tempfile

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config_ui import load_config, CONFIG_PATH
from logger import get_logger

logger = get_logger()

def test_auto_enable_logic():
    """Test the auto-enable light control logic."""
    
    # Test 1: Config with both API key and device ID should auto-enable light control
    print("Test 1: Config with both Govee credentials...")
    test_config = {
        "GOVEE_API_KEY": "test_api_key_123",
        "GOVEE_DEVICE_ID": "test_device_id_456"
    }
    
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_config, f)
        temp_config_path = f.name
    
    # Temporarily override CONFIG_PATH
    original_config_path = CONFIG_PATH
    import config_ui
    config_ui.CONFIG_PATH = temp_config_path
    
    try:
        config = load_config()
        print(f"DISABLE_LIGHT_CONTROL: {config.get('DISABLE_LIGHT_CONTROL')}")
        print(f"DISABLE_CALENDAR_SYNC: {config.get('DISABLE_CALENDAR_SYNC')}")
        
        # Should auto-enable light control (False means enabled)
        assert config.get('DISABLE_LIGHT_CONTROL') == False, "Light control should be auto-enabled"
        # Calendar sync should remain disabled (True means disabled)
        assert config.get('DISABLE_CALENDAR_SYNC') == True, "Calendar sync should remain disabled"
        print("✓ Test 1 passed: Light control auto-enabled, calendar sync remains disabled")
        
    finally:
        # Restore original path and cleanup
        config_ui.CONFIG_PATH = original_config_path
        os.unlink(temp_config_path)
    
    # Test 2: Config with missing device ID should not auto-enable
    print("\nTest 2: Config with missing device ID...")
    test_config = {
        "GOVEE_API_KEY": "test_api_key_123"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_config, f)
        temp_config_path = f.name
    
    config_ui.CONFIG_PATH = temp_config_path
    
    try:
        config = load_config()
        print(f"DISABLE_LIGHT_CONTROL: {config.get('DISABLE_LIGHT_CONTROL')}")
        
        # Should NOT auto-enable light control (True means disabled)
        assert config.get('DISABLE_LIGHT_CONTROL') == True, "Light control should remain disabled"
        print("✓ Test 2 passed: Light control remains disabled without complete credentials")
        
    finally:
        config_ui.CONFIG_PATH = original_config_path
        os.unlink(temp_config_path)
    
    # Test 3: Empty config should not auto-enable
    print("\nTest 3: Empty config...")
    test_config = {}
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_config, f)
        temp_config_path = f.name
    
    config_ui.CONFIG_PATH = temp_config_path
    
    try:
        config = load_config()
        print(f"DISABLE_LIGHT_CONTROL: {config.get('DISABLE_LIGHT_CONTROL')}")
        
        # Should NOT auto-enable light control (True means disabled)
        assert config.get('DISABLE_LIGHT_CONTROL') == True, "Light control should remain disabled"
        print("✓ Test 3 passed: Light control remains disabled with empty config")
        
    finally:
        config_ui.CONFIG_PATH = original_config_path
        os.unlink(temp_config_path)
    
    print("\n🎉 All tests passed! Auto-enable logic is working correctly.")

if __name__ == "__main__":
    test_auto_enable_logic()
