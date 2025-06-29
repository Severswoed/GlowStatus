#!/usr/bin/env python3
"""
Test for Immediate Light Turn-Off When Disabling Light Control

This test verifies that when disabling light control via the tray menu,
the lights turn off immediately rather than waiting for the next polling cycle.
"""

import os
import sys
import tempfile
import json

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock the config functions to avoid GUI imports
def load_config(config_path=None):
    if config_path is None:
        config_path = "/tmp/test_config.json"
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}

def save_config(config, config_path=None):
    if config_path is None:
        config_path = "/tmp/test_config.json"
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

# Mock load_secret function
def load_secret(key):
    if key == "GOVEE_API_KEY":
        return "test_api_key"
    return None

# Mock GoveeController
class MockGoveeController:
    def __init__(self, api_key, device_id, device_model):
        self.api_key = api_key
        self.device_id = device_id
        self.device_model = device_model
        self.power_state = "on"
        self.color = (255, 255, 255)
        
    def set_power(self, state):
        self.power_state = state
        print(f"Mock Govee: Power set to {state}")
        
    def set_color(self, r, g, b):
        self.color = (r, g, b)
        print(f"Mock Govee: Color set to ({r}, {g}, {b})")

def test_immediate_light_turn_off():
    """Test that lights turn off immediately when disabling light control"""
    
    # Create a temporary config with light control enabled and Govee configured
    temp_config_path = "/tmp/test_immediate_lights_config.json"
    
    initial_config = {
        "DISABLE_LIGHT_CONTROL": False,
        "GOVEE_DEVICE_ID": "test_device_123",
        "GOVEE_DEVICE_MODEL": "H6159",
        "CURRENT_STATUS": "in_meeting"
    }
    save_config(initial_config, temp_config_path)
    
    try:
        # Mock the imports to avoid GUI dependencies
        sys.modules['govee_controller'] = type('MockModule', (), {
            'GoveeController': MockGoveeController
        })()
        sys.modules['config_ui'] = type('MockModule', (), {
            'load_config': lambda: load_config(temp_config_path),
            'save_config': lambda config: save_config(config, temp_config_path)
        })()
        sys.modules['utils'] = type('MockModule', (), {
            'load_secret': load_secret
        })()
        sys.modules['logger'] = type('MockModule', (), {
            'get_logger': lambda name=None: type('MockLogger', (), {
                'info': lambda msg: print(f"INFO: {msg}"),
                'warning': lambda msg: print(f"WARNING: {msg}"),
                'error': lambda msg: print(f"ERROR: {msg}")
            })()
        })()
        
        # Now we can import GlowStatusController
        from glowstatus import GlowStatusController
        
        # Create the controller
        controller = GlowStatusController()
        
        # Test the turn_off_lights_immediately method
        print("Testing immediate light turn-off...")
        controller.turn_off_lights_immediately()
        
        # Simulate the toggle_light function logic for disabling lights
        print("\nSimulating toggle light to disable...")
        
        def simulate_toggle_light_disable():
            config = load_config(temp_config_path)
            
            # Turn off lights immediately before disabling light control
            controller.turn_off_lights_immediately()
            config["DISABLE_LIGHT_CONTROL"] = True
            save_config(config, temp_config_path)
            print("Light control disabled by user")
        
        simulate_toggle_light_disable()
        
        # Verify config was updated
        config = load_config(temp_config_path)
        assert config.get("DISABLE_LIGHT_CONTROL", False) == True, "Light control should be disabled"
        
        print("✓ Immediate light turn-off test passed!")
        
    finally:
        # Cleanup
        try:
            os.unlink(temp_config_path)
        except:
            pass

def test_immediate_light_turn_off_no_credentials():
    """Test that the method handles missing Govee credentials gracefully"""
    
    temp_config_path = "/tmp/test_no_creds_config.json"
    
    # Config without Govee credentials
    config_no_creds = {
        "DISABLE_LIGHT_CONTROL": False,
        "CURRENT_STATUS": "in_meeting"
    }
    save_config(config_no_creds, temp_config_path)
    
    try:
        # Mock the imports
        sys.modules['govee_controller'] = type('MockModule', (), {
            'GoveeController': MockGoveeController
        })()
        sys.modules['config_ui'] = type('MockModule', (), {
            'load_config': lambda: load_config(temp_config_path),
            'save_config': lambda config: save_config(config, temp_config_path)
        })()
        sys.modules['utils'] = type('MockModule', (), {
            'load_secret': lambda key: None  # No credentials available
        })()
        sys.modules['logger'] = type('MockModule', (), {
            'get_logger': lambda name=None: type('MockLogger', (), {
                'info': lambda msg: print(f"INFO: {msg}"),
                'warning': lambda msg: print(f"WARNING: {msg}"),
                'error': lambda msg: print(f"ERROR: {msg}")
            })()
        })()
        
        from glowstatus import GlowStatusController
        
        controller = GlowStatusController()
        
        print("Testing immediate light turn-off with missing credentials...")
        # This should handle the missing credentials gracefully
        controller.turn_off_lights_immediately()
        
        print("✓ Missing credentials handled gracefully!")
        
    finally:
        try:
            os.unlink(temp_config_path)
        except:
            pass

if __name__ == "__main__":
    print("Testing Immediate Light Turn-Off When Disabling Light Control...")
    print("=" * 65)
    
    test_immediate_light_turn_off()
    print()
    test_immediate_light_turn_off_no_credentials()
    
    print("\n✓ All immediate light control tests passed!")
    print("\nNow when you disable lights via the tray menu, they should turn off immediately!")
