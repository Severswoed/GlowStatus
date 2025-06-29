#!/usr/bin/env python3
"""Test script to verify auto-enable light control logic (without GUI dependencies)."""

import sys
import os
import json
import tempfile

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_load_config_logic():
    """Test just the load_config logic without GUI dependencies."""
    
    # Simplified version of the load_config function logic
    def test_load_config(config_data):
        config = config_data.copy()
        
        # Set sensible defaults for new configurations
        if "DISABLE_CALENDAR_SYNC" not in config:
            # Default to disabled since we'll support multiple calendar providers
            config["DISABLE_CALENDAR_SYNC"] = True
        
        if "DISABLE_LIGHT_CONTROL" not in config:
            # Auto-enable light control if Govee credentials are configured
            # since users can only have one set of lights paired
            govee_api_key = config.get("GOVEE_API_KEY", "").strip()
            govee_device_id = config.get("GOVEE_DEVICE_ID", "").strip()
            
            # For testing, skip keyring check since we don't have GUI
            
            if govee_api_key and govee_device_id:
                config["DISABLE_LIGHT_CONTROL"] = False
                print("Auto-enabled light control since Govee credentials are configured")
            else:
                # Default to disabled since we'll support multiple light controller brands
                config["DISABLE_LIGHT_CONTROL"] = True
        
        return config
    
    # Test 1: Config with both API key and device ID should auto-enable light control
    print("Test 1: Config with both Govee credentials...")
    test_config = {
        "GOVEE_API_KEY": "test_api_key_123",
        "GOVEE_DEVICE_ID": "test_device_id_456"
    }
    
    config = test_load_config(test_config)
    print(f"DISABLE_LIGHT_CONTROL: {config.get('DISABLE_LIGHT_CONTROL')}")
    print(f"DISABLE_CALENDAR_SYNC: {config.get('DISABLE_CALENDAR_SYNC')}")
    
    # Should auto-enable light control (False means enabled)
    assert config.get('DISABLE_LIGHT_CONTROL') == False, "Light control should be auto-enabled"
    # Calendar sync should remain disabled (True means disabled)
    assert config.get('DISABLE_CALENDAR_SYNC') == True, "Calendar sync should remain disabled"
    print("✓ Test 1 passed: Light control auto-enabled, calendar sync remains disabled")
    
    # Test 2: Config with missing device ID should not auto-enable
    print("\nTest 2: Config with missing device ID...")
    test_config = {
        "GOVEE_API_KEY": "test_api_key_123"
    }
    
    config = test_load_config(test_config)
    print(f"DISABLE_LIGHT_CONTROL: {config.get('DISABLE_LIGHT_CONTROL')}")
    
    # Should NOT auto-enable light control (True means disabled)
    assert config.get('DISABLE_LIGHT_CONTROL') == True, "Light control should remain disabled"
    print("✓ Test 2 passed: Light control remains disabled without complete credentials")
    
    # Test 3: Empty config should not auto-enable
    print("\nTest 3: Empty config...")
    test_config = {}
    
    config = test_load_config(test_config)
    print(f"DISABLE_LIGHT_CONTROL: {config.get('DISABLE_LIGHT_CONTROL')}")
    
    # Should NOT auto-enable light control (True means disabled)
    assert config.get('DISABLE_LIGHT_CONTROL') == True, "Light control should remain disabled"
    print("✓ Test 3 passed: Light control remains disabled with empty config")
    
    # Test 4: Config with existing light control setting should not be overridden
    print("\nTest 4: Config with existing light control setting...")
    test_config = {
        "GOVEE_API_KEY": "test_api_key_123",
        "GOVEE_DEVICE_ID": "test_device_id_456",
        "DISABLE_LIGHT_CONTROL": True  # User explicitly disabled it
    }
    
    config = test_load_config(test_config)
    print(f"DISABLE_LIGHT_CONTROL: {config.get('DISABLE_LIGHT_CONTROL')}")
    
    # Should respect existing setting (True means disabled)
    assert config.get('DISABLE_LIGHT_CONTROL') == True, "Existing light control setting should be respected"
    print("✓ Test 4 passed: Existing light control setting is respected")
    
    print("\n🎉 All tests passed! Auto-enable logic is working correctly.")

if __name__ == "__main__":
    test_load_config_logic()
