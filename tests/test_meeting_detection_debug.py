#!/usr/bin/env python3
"""
Debug test to identify why lights don't turn on during meetings.
This test checks the actual meeting detection logic and configuration.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
import time

def test_meeting_detection_debug():
    """Test the meeting detection logic to find why lights don't turn on."""
    
    print("🔍 MEETING DETECTION DEBUG TEST")
    print("=" * 60)
    
    # Import after adding to path
    from glowstatus import GlowStatusController
    from settings_ui import load_config
    
    # Check current configuration
    print("\n📋 Current Configuration:")
    config = load_config()
    
    critical_settings = [
        "DISABLE_CALENDAR_SYNC",
        "DISABLE_LIGHT_CONTROL", 
        "SELECTED_CALENDAR_ID",
        "GOVEE_DEVICE_ID",
        "GOVEE_DEVICE_MODEL",
        "STATUS_COLOR_MAP"
    ]
    
    for setting in critical_settings:
        value = config.get(setting)
        if setting.startswith("DISABLE_"):
            status = "🔴 DISABLED" if value else "✅ ENABLED"
        elif value:
            status = f"✅ SET: {str(value)[:50]}"
        else:
            status = "❌ NOT SET"
        print(f"   {setting:<25}: {status}")
    
    print(f"\n🔧 Key Issues Check:")
    
    # Check 1: Calendar sync disabled?
    if config.get("DISABLE_CALENDAR_SYNC", False):
        print("   ❌ CRITICAL: Calendar sync is DISABLED!")
        print("      This would prevent meeting detection entirely.")
        return False
    else:
        print("   ✅ Calendar sync is enabled")
    
    # Check 2: Light control disabled?
    if config.get("DISABLE_LIGHT_CONTROL", False):
        print("   ❌ CRITICAL: Light control is DISABLED!")
        print("      This would prevent lights from turning on.")
        return False
    else:
        print("   ✅ Light control is enabled")
    
    # Check 3: Calendar ID set?
    if not config.get("SELECTED_CALENDAR_ID"):
        print("   ❌ CRITICAL: No calendar ID selected!")
        print("      This would prevent calendar access.")
        return False
    else:
        print("   ✅ Calendar ID is configured")
    
    # Check 4: Govee credentials set?
    govee_id = config.get("GOVEE_DEVICE_ID")
    govee_model = config.get("GOVEE_DEVICE_MODEL")
    if not govee_id or not govee_model:
        print("   ❌ CRITICAL: Govee device not configured!")
        print(f"      Device ID: {govee_id}")
        print(f"      Model: {govee_model}")
        return False
    else:
        print("   ✅ Govee device is configured")
    
    # Check 5: Status color map has in_meeting?
    color_map = config.get("STATUS_COLOR_MAP", {})
    if "in_meeting" not in color_map:
        print("   ❌ WARNING: No 'in_meeting' color mapping!")
        print("      This could cause default behavior.")
    else:
        meeting_config = color_map["in_meeting"]
        print(f"   ✅ Meeting color config: {meeting_config}")
        
        # Check if meeting is set to power off (wrong!)
        if isinstance(meeting_config, dict) and meeting_config.get("power_off", False):
            print("   ❌ CRITICAL: Meeting is configured to turn lights OFF!")
            print("      This would explain why lights don't turn on.")
            return False
    
    print(f"\n🧪 Testing Calendar Access:")
    try:
        from calendar_sync import CalendarSync
        from utils import resource_path
        
        # Check if client_secret.json exists
        client_secret_path = resource_path('resources/client_secret.json')
        if not os.path.exists(client_secret_path):
            print(f"   ❌ CRITICAL: client_secret.json not found at {client_secret_path}")
            return False
        else:
            print("   ✅ client_secret.json exists")
        
        # Try to create calendar sync instance
        calendar_id = config.get("SELECTED_CALENDAR_ID")
        calendar = CalendarSync(calendar_id)
        print("   ✅ Calendar sync instance created successfully")
        
        # Try to get current status
        try:
            status, next_event = calendar.get_current_status(return_next_event_time=True, color_map=color_map)
            print(f"   ✅ Calendar status retrieved: {status}")
            if next_event:
                print(f"   📅 Next event: {next_event}")
            else:
                print("   📅 No upcoming events")
        except Exception as e:
            print(f"   ❌ Calendar status retrieval failed: {e}")
            return False
            
    except Exception as e:
        print(f"   ❌ Calendar access failed: {e}")
        return False
    
    print(f"\n🔬 Testing Light Control:")
    try:
        from govee_controller import GoveeController
        from utils import load_secret
        
        # Check Govee API key
        api_key = load_secret("GOVEE_API_KEY")
        if not api_key:
            print("   ❌ CRITICAL: GOVEE_API_KEY not found!")
            return False
        else:
            print("   ✅ Govee API key is loaded")
        
        # Try to create Govee instance
        govee = GoveeController(api_key, govee_id, govee_model)
        print("   ✅ Govee controller created successfully")
        
        # Test light command (but don't actually change lights)
        print("   ℹ️  Light control test would work (not executing)")
        
    except Exception as e:
        print(f"   ❌ Govee controller failed: {e}")
        return False
    
    print(f"\n🎯 Summary:")
    print("   All critical components appear to be working.")
    print("   The issue might be:")
    print("   1. Meeting detection timing (calendar polling interval)")
    print("   2. Meeting status keywords not matching")
    print("   3. Color map configuration issue")
    print("   4. OAuth token expiration")
    
    return True

def test_status_keyword_matching():
    """Test if the calendar is returning the right status keywords."""
    print(f"\n🔤 Testing Status Keyword Matching:")
    
    # Common meeting keywords that should trigger "in_meeting"
    test_titles = [
        "Team Meeting",
        "1:1 with Manager", 
        "Sprint Planning",
        "All Hands",
        "Interview",
        "Standup",
        "Review",
        "Call with Client",
        "Project Discussion"
    ]
    
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
        from utils import normalize_status
        from settings_ui import load_config
        
        config = load_config()
        color_map = config.get("STATUS_COLOR_MAP", {})
        
        print(f"   Available status mappings: {list(color_map.keys())}")
        
        for title in test_titles:
            status = normalize_status(title, color_map)
            print(f"   '{title}' → '{status}'")
            
            if status != "in_meeting":
                print(f"   ⚠️  This might not trigger meeting lights!")
        
    except Exception as e:
        print(f"   ❌ Status keyword test failed: {e}")

if __name__ == "__main__":
    success = test_meeting_detection_debug()
    test_status_keyword_matching()
    
    if success:
        print(f"\n✅ Configuration appears correct!")
        print("   Try checking the actual log files during a meeting.")
    else:
        print(f"\n❌ Found configuration issues that need fixing!")
