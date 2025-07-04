#!/usr/bin/env python3
"""
Test script to verify tray menu and settings UI synchronization
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from settings_ui import load_config, save_config
from constants import TOKEN_PATH

def test_sync_light_validation():
    print("Testing sync and light control validation...")
    
    # Load current config
    config = load_config()
    print(f"Current config state:")
    print(f"  SELECTED_CALENDAR_ID: '{config.get('SELECTED_CALENDAR_ID', '')}'")
    print(f"  GOVEE_DEVICE_ID: '{config.get('GOVEE_DEVICE_ID', '')}'")
    print(f"  GOVEE_DEVICE_MODEL: '{config.get('GOVEE_DEVICE_MODEL', '')}'")
    print(f"  DISABLE_CALENDAR_SYNC: {config.get('DISABLE_CALENDAR_SYNC', False)}")
    print(f"  DISABLE_LIGHT_CONTROL: {config.get('DISABLE_LIGHT_CONTROL', False)}")
    print(f"  OAuth token exists: {os.path.exists(TOKEN_PATH)}")
    
    # Test calendar sync validation
    def can_enable_calendar_sync():
        has_calendar = bool(config.get("SELECTED_CALENDAR_ID"))
        has_auth = os.path.exists(TOKEN_PATH)
        from utils import resource_path
        has_client_secret = os.path.exists(resource_path('resources/client_secret.json'))
        return has_calendar and has_auth and has_client_secret
    
    # Test light control validation
    def can_enable_light_control():
        has_device_id = bool(config.get("GOVEE_DEVICE_ID"))
        has_device_model = bool(config.get("GOVEE_DEVICE_MODEL"))
        return has_device_id and has_device_model
    
    sync_can_enable = can_enable_calendar_sync()
    light_can_enable = can_enable_light_control()
    
    print(f"\nValidation results:")
    print(f"  Calendar sync can be enabled: {sync_can_enable}")
    print(f"  Light control can be enabled: {light_can_enable}")
    
    # Show what would happen with tray menu logic
    sync_config_enabled = not config.get("DISABLE_CALENDAR_SYNC", False)
    light_config_enabled = not config.get("DISABLE_LIGHT_CONTROL", False)
    
    effective_sync_enabled = sync_config_enabled and sync_can_enable
    effective_light_enabled = light_config_enabled and light_can_enable
    
    print(f"\nEffective states (config + validation):")
    print(f"  Sync enabled: {effective_sync_enabled} (config: {sync_config_enabled}, can enable: {sync_can_enable})")
    print(f"  Light enabled: {effective_light_enabled} (config: {light_config_enabled}, can enable: {light_can_enable})")
    
    # Show what tray menu would display
    print(f"\nTray menu would show:")
    print(f"  {'Disable Sync' if effective_sync_enabled else 'Enable Sync'}")
    print(f"  {'Disable Lights' if effective_light_enabled else 'Enable Lights'}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_sync_light_validation()
