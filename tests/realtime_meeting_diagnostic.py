#!/usr/bin/env python3
"""
Real-time diagnostic for the current meeting detection issue.
Meeting at 1:14 PM, currently 1:13 PM, lights should be on but aren't.
"""

import sys
import os
import datetime
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def check_current_config():
    """Check the current configuration to see what might be preventing meeting detection."""
    
    print("🔍 REAL-TIME MEETING DETECTION DIAGNOSTIC")
    print("=" * 60)
    print(f"⏰ Current time: {datetime.datetime.now().strftime('%H:%M:%S')}")
    print(f"📅 Meeting time: 1:14 PM (should have triggered at 1:13 PM)")
    print()
    
    # Check config file
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'glowstatus_config.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print("📋 Current Configuration:")
        print(f"   DISABLE_CALENDAR_SYNC: {config.get('DISABLE_CALENDAR_SYNC')}")
        print(f"   DISABLE_LIGHT_CONTROL: {config.get('DISABLE_LIGHT_CONTROL')}")
        print(f"   CURRENT_STATUS: {config.get('CURRENT_STATUS')}")
        print(f"   MANUAL_STATUS_TIMESTAMP: {config.get('MANUAL_STATUS_TIMESTAMP')}")
        print(f"   SELECTED_CALENDAR_ID: {config.get('SELECTED_CALENDAR_ID')}")
        print(f"   REFRESH_INTERVAL: {config.get('REFRESH_INTERVAL')}")
        print()
        
        # Diagnose potential issues
        issues = []
        
        if config.get('DISABLE_CALENDAR_SYNC'):
            issues.append("❌ Calendar sync is DISABLED - app won't check for meetings")
        
        if config.get('DISABLE_LIGHT_CONTROL'):
            issues.append("❌ Light control is DISABLED - app won't control lights")
        
        if config.get('CURRENT_STATUS') and config.get('MANUAL_STATUS_TIMESTAMP') is None:
            issues.append(f"❌ Stuck manual status: '{config.get('CURRENT_STATUS')}' with no timestamp")
        
        if not config.get('SELECTED_CALENDAR_ID'):
            issues.append("❌ No calendar ID configured")
        
        if config.get('REFRESH_INTERVAL', 15) > 60:
            issues.append(f"❌ Refresh interval too long: {config.get('REFRESH_INTERVAL')}s (should be ≤60s for 1-min detection)")
        
        if issues:
            print("🚨 POTENTIAL ISSUES FOUND:")
            for issue in issues:
                print(f"   {issue}")
        else:
            print("✅ Configuration looks correct - issue may be elsewhere")
        
        print()
        
        # Check if this is the stuck manual status bug
        current_status = config.get('CURRENT_STATUS')
        manual_timestamp = config.get('MANUAL_STATUS_TIMESTAMP')
        
        if current_status and manual_timestamp is None:
            print("🎯 DIAGNOSIS: This is the STUCK MANUAL STATUS BUG!")
            print(f"   Status '{current_status}' is stuck without a timestamp")
            print("   This prevents calendar detection from working")
            print("   The fix we implemented should clear this on next update")
            
            if current_status != "meeting_ended_early":
                print(f"   ⚠️  Status '{current_status}' should be cleared immediately")
            else:
                print(f"   📝 Status 'meeting_ended_early' is allowed to persist without timestamp")
        
        return config
        
    except FileNotFoundError:
        print(f"❌ Config file not found: {config_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config file: {e}")
        return None

def check_calendar_access():
    """Check if calendar access is working."""
    print("📅 Testing Calendar Access:")
    
    try:
        from calendar_sync import CalendarSync
        from settings_ui import load_config
        
        config = load_config()
        calendar_id = config.get('SELECTED_CALENDAR_ID')
        
        if not calendar_id:
            print("   ❌ No calendar ID configured")
            return False
        
        print(f"   📧 Calendar ID: {calendar_id}")
        
        # Try to create calendar sync
        try:
            calendar = CalendarSync(calendar_id)
            print("   ✅ Calendar sync object created successfully")
            
            # Try to get current status
            try:
                status, next_event = calendar.get_current_status(return_next_event_time=True)
                print(f"   📊 Current calendar status: {status}")
                if next_event:
                    print(f"   ⏰ Next event: {next_event}")
                else:
                    print("   📝 No upcoming events found")
                return True
            except Exception as e:
                print(f"   ❌ Failed to get calendar status: {e}")
                return False
        except Exception as e:
            print(f"   ❌ Failed to create calendar sync: {e}")
            return False
    except ImportError as e:
        print(f"   ❌ Failed to import calendar modules: {e}")
        return False

def check_light_control():
    """Check if light control is working."""
    print("💡 Testing Light Control:")
    
    try:
        from govee_controller import GoveeController
        from settings_ui import load_config
        from utils import load_secret
        
        config = load_config()
        api_key = load_secret("GOVEE_API_KEY")
        device_id = config.get("GOVEE_DEVICE_ID")
        device_model = config.get("GOVEE_DEVICE_MODEL")
        
        print(f"   🔑 API Key: {'✅ Set' if api_key else '❌ Missing'}")
        print(f"   📱 Device ID: {device_id if device_id else '❌ Missing'}")
        print(f"   🏷️  Device Model: {device_model if device_model else '❌ Missing'}")
        
        if api_key and device_id and device_model:
            try:
                govee = GoveeController(api_key, device_id, device_model)
                print("   ✅ Govee controller created successfully")
                print("   💡 Light control should be working")
                return True
            except Exception as e:
                print(f"   ❌ Failed to create Govee controller: {e}")
                return False
        else:
            print("   ❌ Missing required Govee credentials")
            return False
    except ImportError as e:
        print(f"   ❌ Failed to import Govee modules: {e}")
        return False

if __name__ == "__main__":
    config = check_current_config()
    
    if config:
        print()
        calendar_ok = check_calendar_access()
        print()
        light_ok = check_light_control()
        
        print()
        print("🎯 REAL-TIME RECOMMENDATION:")
        
        if config.get('CURRENT_STATUS') and config.get('MANUAL_STATUS_TIMESTAMP') is None:
            print("   1. ⚡ IMMEDIATE: This is the stuck manual status bug!")
            print("   2. 🔧 The fix should clear this on the next 15-second update")
            print("   3. ⏰ Wait until 1:14:00 to see if lights turn on when meeting starts")
            print("   4. 🔄 If not, restart the app to clear the stuck status")
        elif not calendar_ok:
            print("   1. 📅 Calendar access is broken - check OAuth credentials")
            print("   2. 🔑 Re-run calendar setup in settings")
        elif not light_ok:
            print("   1. 💡 Light control is broken - check Govee credentials")
            print("   2. 🔑 Verify API key and device ID in settings")
        else:
            print("   1. ⏰ Everything looks configured correctly")
            print("   2. 🔍 Issue may be in the periodic update loop")
            print("   3. 📊 Check if app is actually running the 15-second checks")
    
    print()
    print("⏰ Keep watching - meeting starts in a few seconds!")
    print("💡 Lights should turn on at exactly 1:14:00 PM when meeting starts")
