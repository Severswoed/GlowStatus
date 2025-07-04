#!/usr/bin/env python3
"""
Test script to verify the light control configuration bug fix.

This script specifically tests that:
1. User's choice to disable light control is respected
2. Auto-enabling only happens for new installations 
3. The save_config function doesn't override user preferences
"""

import sys
import os
import tempfile
import json
from unittest.mock import patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock PySide6 to avoid Qt dependencies
sys.modules['PySide6'] = MagicMock()
sys.modules['PySide6.QtWidgets'] = MagicMock()
sys.modules['PySide6.QtCore'] = MagicMock()
sys.modules['PySide6.QtGui'] = MagicMock()

from settings_ui import load_config, save_config


def test_bug_fix():
    """Test the specific bug fix for light control auto-enabling."""
    print("🔧 Testing Light Control Configuration Bug Fix")
    print("=" * 60)
    
    # Test 1: User explicitly disables light control, should be respected
    print("\n1️⃣ Test: User choice to disable should be respected")
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
        with patch('config_ui.CONFIG_PATH', config_path):
            # Load config
            loaded_config = load_config()
            print(f"   ✅ DISABLE_LIGHT_CONTROL after load: {loaded_config['DISABLE_LIGHT_CONTROL']}")
            assert loaded_config['DISABLE_LIGHT_CONTROL'] == True, "User choice should be preserved on load"
            
            # Save config (this used to auto-enable, but shouldn't anymore)
            loaded_config['REFRESH_INTERVAL'] = 30  # Make a change
            save_config(loaded_config)
            print(f"   ✅ Config saved successfully")
            
            # Reload and verify
            final_config = load_config()
            print(f"   ✅ DISABLE_LIGHT_CONTROL after save/reload: {final_config['DISABLE_LIGHT_CONTROL']}")
            assert final_config['DISABLE_LIGHT_CONTROL'] == True, "User choice should be preserved after save"
            
    finally:
        os.unlink(config_path)
    
    print("   ✅ PASS: User choice is respected")
    
    # Test 2: New installation with credentials should auto-enable
    print("\n2️⃣ Test: New installation should auto-enable with credentials")
    new_config = {
        'GOVEE_DEVICE_ID': 'AA:BB:CC:DD:EE:FF:11:22',
        'GOVEE_DEVICE_MODEL': 'H6159'
        # Note: No DISABLE_LIGHT_CONTROL key - simulates new installation
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(new_config, f)
        config_path = f.name
    
    try:
        with patch('config_ui.CONFIG_PATH', config_path), \
             patch('config_ui.keyring.get_password', return_value='test_api_key'):
            
            loaded_config = load_config()
            print(f"   ✅ DISABLE_LIGHT_CONTROL for new install: {loaded_config['DISABLE_LIGHT_CONTROL']}")
            assert loaded_config['DISABLE_LIGHT_CONTROL'] == False, "Should auto-enable for new installation"
            
    finally:
        os.unlink(config_path)
    
    print("   ✅ PASS: New installation auto-enables appropriately")
    
    # Test 3: New installation without credentials should default to disabled
    print("\n3️⃣ Test: New installation without credentials should default to disabled")
    empty_config = {}
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(empty_config, f)
        config_path = f.name
    
    try:
        with patch('config_ui.CONFIG_PATH', config_path), \
             patch('config_ui.keyring.get_password', return_value=None):
            
            loaded_config = load_config()
            print(f"   ✅ DISABLE_LIGHT_CONTROL with no credentials: {loaded_config['DISABLE_LIGHT_CONTROL']}")
            assert loaded_config['DISABLE_LIGHT_CONTROL'] == True, "Should default to disabled without credentials"
            
    finally:
        os.unlink(config_path)
    
    print("   ✅ PASS: Defaults to disabled without credentials")
    
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ Bug fix verified: User choice to disable light control is now respected")
    print("✅ Auto-enabling only occurs for new installations with credentials")
    print("✅ save_config() no longer overrides user preferences")


if __name__ == '__main__':
    test_bug_fix()
