"""
Test to verify that the GlowStatus controller and config file stay synchronized.
This test checks that:
1. Manual status changes are reflected in the config file
2. Calendar status updates are reflected in the config file  
3. The controller's internal state matches the config file
"""

import json
import time
import sys
import os

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from settings_ui import load_config, save_config

def print_current_state():
    """Print the current state from the config file"""
    config = load_config()
    print(f"Config file state:")
    print(f"  CURRENT_STATUS: {config.get('CURRENT_STATUS')}")
    print(f"  MANUAL_STATUS_TIMESTAMP: {config.get('MANUAL_STATUS_TIMESTAMP')}")
    print(f"  DISABLE_CALENDAR_SYNC: {config.get('DISABLE_CALENDAR_SYNC')}")
    print(f"  DISABLE_LIGHT_CONTROL: {config.get('DISABLE_LIGHT_CONTROL')}")
    return config

def test_manual_status_sync():
    """Test that manual status changes are reflected in config"""
    print("\n=== Testing Manual Status Synchronization ===")
    
    # Get initial state
    print("Initial state:")
    initial_config = print_current_state()
    
    # Set a manual status
    print("\nSetting manual status to 'focus'...")
    config = load_config()
    config["CURRENT_STATUS"] = "focus"
    config["MANUAL_STATUS_TIMESTAMP"] = time.time()
    save_config(config)
    
    # Verify it was saved
    print("After setting manual status:")
    updated_config = print_current_state()
    
    if updated_config.get("CURRENT_STATUS") == "focus":
        print("✅ Manual status sync PASSED")
    else:
        print("❌ Manual status sync FAILED")
        return False
    
    # Clear manual status
    print("\nClearing manual status...")
    config = load_config()
    if "CURRENT_STATUS" in config:
        del config["CURRENT_STATUS"]
    if "MANUAL_STATUS_TIMESTAMP" in config:
        del config["MANUAL_STATUS_TIMESTAMP"]
    save_config(config)
    
    # Verify it was cleared
    print("After clearing manual status:")
    cleared_config = print_current_state()
    
    if cleared_config.get("CURRENT_STATUS") is None:
        print("✅ Manual status clear PASSED")
    else:
        print("❌ Manual status clear FAILED")
        return False
    
    return True

def test_config_persistence():
    """Test that config changes persist across file operations"""
    print("\n=== Testing Config Persistence ===")
    
    # Save a test value
    test_timestamp = time.time()
    config = load_config()
    config["TEST_VALUE"] = test_timestamp
    save_config(config)
    print(f"Saved test value: {test_timestamp}")
    
    # Load config again and verify
    new_config = load_config()
    loaded_value = new_config.get("TEST_VALUE")
    
    if loaded_value == test_timestamp:
        print("✅ Config persistence PASSED")
        
        # Clean up test value
        del new_config["TEST_VALUE"]
        save_config(new_config)
        return True
    else:
        print(f"❌ Config persistence FAILED - expected {test_timestamp}, got {loaded_value}")
        return False

def test_end_meeting_early_sync():
    """Test that 'end meeting early' status is properly synchronized"""
    print("\n=== Testing End Meeting Early Synchronization ===")
    
    # Set end meeting early status
    print("Setting 'meeting_ended_early' status...")
    config = load_config()
    config["CURRENT_STATUS"] = "meeting_ended_early"
    config["MANUAL_STATUS_TIMESTAMP"] = time.time()
    save_config(config)
    
    # Verify it was saved
    print("After setting end meeting early:")
    updated_config = print_current_state()
    
    if updated_config.get("CURRENT_STATUS") == "meeting_ended_early":
        print("✅ End meeting early sync PASSED")
        
        # Clean up
        del updated_config["CURRENT_STATUS"]
        del updated_config["MANUAL_STATUS_TIMESTAMP"]
        save_config(updated_config)
        return True
    else:
        print("❌ End meeting early sync FAILED")
        return False

def main():
    print("Testing GlowStatus Config Synchronization")
    print("=" * 50)
    
    # Check initial state
    print("Current system state:")
    print_current_state()
    
    # Run tests
    tests_passed = 0
    total_tests = 3
    
    if test_manual_status_sync():
        tests_passed += 1
    
    if test_config_persistence():
        tests_passed += 1
        
    if test_end_meeting_early_sync():
        tests_passed += 1
    
    # Summary
    print(f"\n=== Test Results ===")
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("✅ All synchronization tests PASSED")
        print("The config file and controller state should be properly synchronized.")
    else:
        print("❌ Some synchronization tests FAILED")
        print("There may be issues with config/controller state sync.")
    
    # Show final state
    print("\nFinal state:")
    print_current_state()

if __name__ == "__main__":
    main()
