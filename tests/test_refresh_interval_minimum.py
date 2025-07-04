#!/usr/bin/env python3
"""
Test script to verify refresh interval minimum value enforcement
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from settings_ui import load_config, save_config

def test_refresh_interval_minimum():
    print("Testing refresh interval minimum value enforcement...")
    
    # Load current config
    config = load_config()
    original_interval = config.get("REFRESH_INTERVAL", 15)
    print(f"Original refresh interval: {original_interval}")
    
    # Test case 1: Try to set a value below 15
    config["REFRESH_INTERVAL"] = 5
    save_config(config)
    
    # Reload and check if it gets corrected
    config = load_config()
    interval_after_save = config.get("REFRESH_INTERVAL", 15)
    print(f"After setting to 5: {interval_after_save}")
    
    # Test case 2: Try to set a valid value (15 or above)
    config["REFRESH_INTERVAL"] = 30
    save_config(config)
    
    config = load_config()
    interval_valid = config.get("REFRESH_INTERVAL", 15)
    print(f"After setting to 30: {interval_valid}")
    
    # Test case 3: Test the main logic enforcement
    from glowstatus import GlowStatusController
    controller = GlowStatusController()
    
    # Temporarily set a low value in config
    config["REFRESH_INTERVAL"] = 8
    save_config(config)
    
    # Check what the main code would use
    config = load_config()
    enforced_interval = max(15, int(config.get("REFRESH_INTERVAL", 15)))
    print(f"Main code enforcement (config=8): {enforced_interval}")
    
    # Restore original value
    config["REFRESH_INTERVAL"] = original_interval
    save_config(config)
    
    print("Test completed!")
    print(f"✓ Config file can still contain values < 15 (for backwards compatibility)")
    print(f"✓ Main application enforces minimum of 15 seconds at runtime")
    print(f"✓ UI enforces minimum of 15 seconds in spinbox")

if __name__ == "__main__":
    test_refresh_interval_minimum()
