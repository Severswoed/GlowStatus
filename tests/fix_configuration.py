#!/usr/bin/env python3
"""
Configuration Fix Script - Enable Calendar Sync and Light Control
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

def fix_configuration():
    """Fix the configuration to enable calendar sync and light control."""
    
    print("🔧 GLOWSTATUS CONFIGURATION FIX")
    print("=" * 50)
    
    from settings_ui import load_config, save_config
    
    # Load current config
    config = load_config()
    
    print("\n📋 Current Settings:")
    print(f"   DISABLE_CALENDAR_SYNC: {config.get('DISABLE_CALENDAR_SYNC', False)}")
    print(f"   DISABLE_LIGHT_CONTROL: {config.get('DISABLE_LIGHT_CONTROL', False)}")
    print(f"   GOVEE_DEVICE_ID: {'SET' if config.get('GOVEE_DEVICE_ID') else 'NOT SET'}")
    print(f"   SELECTED_CALENDAR_ID: {'SET' if config.get('SELECTED_CALENDAR_ID') else 'NOT SET'}")
    
    print("\n🛠️  Fixing Configuration:")
    
    # Enable calendar sync
    if config.get('DISABLE_CALENDAR_SYNC', False):
        config['DISABLE_CALENDAR_SYNC'] = False
        print("   ✅ Enabled calendar sync")
    else:
        print("   ✅ Calendar sync already enabled")
    
    # Enable light control  
    if config.get('DISABLE_LIGHT_CONTROL', False):
        config['DISABLE_LIGHT_CONTROL'] = False
        print("   ✅ Enabled light control")
    else:
        print("   ✅ Light control already enabled")
    
    # Save the fixed config
    save_config(config)
    print("   ✅ Configuration saved")
    
    print("\n📋 Updated Settings:")
    config = load_config()  # Reload to verify
    print(f"   DISABLE_CALENDAR_SYNC: {config.get('DISABLE_CALENDAR_SYNC', False)}")
    print(f"   DISABLE_LIGHT_CONTROL: {config.get('DISABLE_LIGHT_CONTROL', False)}")
    
    print("\n⚠️  IMPORTANT REMINDERS:")
    print("   1. Make sure your Govee device ID and model are configured")
    print("   2. Make sure your Google Calendar ID is selected")
    print("   3. Restart the GlowStatus app for changes to take effect")
    print("   4. Check that your OAuth token is valid")
    
    if not config.get('GOVEE_DEVICE_ID') or not config.get('SELECTED_CALENDAR_ID'):
        print("\n❌ STILL NEED TO CONFIGURE:")
        if not config.get('GOVEE_DEVICE_ID'):
            print("   • Govee Device ID and Model")
        if not config.get('SELECTED_CALENDAR_ID'):
            print("   • Google Calendar ID")
        print("   Open the Settings UI to complete the configuration.")

if __name__ == "__main__":
    fix_configuration()
