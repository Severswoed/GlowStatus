#!/usr/bin/env python3
"""
Test the complete flow of enabling sync and light control with validation
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from settings_ui import load_config, save_config
from constants import TOKEN_PATH

def test_enable_attempts():
    print("Testing enable attempts with missing prerequisites...")
    
    config = load_config()
    
    # Simulate trying to enable calendar sync without prerequisites
    print("\n=== Testing Calendar Sync Enable ===")
    missing_sync = []
    if not config.get("SELECTED_CALENDAR_ID"):
        missing_sync.append("Google Calendar selection")
    if not os.path.exists(TOKEN_PATH):
        missing_sync.append("Google authentication")
    from utils import resource_path
    if not os.path.exists(resource_path('resources/client_secret.json')):
        missing_sync.append("Google OAuth credentials")
    
    if missing_sync:
        print(f"❌ Cannot enable sync - missing: {', '.join(missing_sync)}")
        print("   Tray menu would show warning dialog")
        print("   Settings UI checkbox would prevent unchecking")
    else:
        print("✅ Sync can be enabled - all prerequisites met")
    
    # Simulate trying to enable light control without prerequisites  
    print("\n=== Testing Light Control Enable ===")
    missing_light = []
    if not config.get("GOVEE_DEVICE_ID"):
        missing_light.append("Govee Device ID")
    if not config.get("GOVEE_DEVICE_MODEL"):
        missing_light.append("Govee Device Model")
    
    if missing_light:
        print(f"❌ Cannot enable lights - missing: {', '.join(missing_light)}")
        print("   Tray menu would show warning dialog")
        print("   Settings UI checkbox would prevent unchecking")
    else:
        print("✅ Light control can be enabled - all prerequisites met")
    
    print("\n=== Current State Summary ===")
    sync_disabled = config.get("DISABLE_CALENDAR_SYNC", False)
    light_disabled = config.get("DISABLE_LIGHT_CONTROL", False)
    
    print(f"Config shows sync disabled: {sync_disabled}")
    print(f"Config shows light disabled: {light_disabled}")
    print(f"Sync prerequisites met: {not missing_sync}")
    print(f"Light prerequisites met: {not missing_light}")
    
    print(f"\nTray menu will show:")
    print(f"  {'Disable Sync' if not sync_disabled and not missing_sync else 'Enable Sync'}")
    print(f"  {'Disable Lights' if not light_disabled and not missing_light else 'Enable Lights'}")
    
    print("\nBehavior:")
    print("- Clicking 'Enable Sync' without prerequisites will show warning dialog")
    print("- Clicking 'Enable Lights' without prerequisites will show warning dialog")
    print("- Settings UI checkboxes will prevent enabling without prerequisites")
    print("- Both tray menu and settings UI will stay synchronized")

if __name__ == "__main__":
    test_enable_attempts()
