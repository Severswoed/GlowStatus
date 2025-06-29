#!/usr/bin/env python3
"""Simple test script to check configuration without Qt dependencies."""

import os
import json
import sys

# Add src to path
sys.path.insert(0, 'src')

# Import only what we need from config_ui
def load_config_simple():
    """Load config without Qt dependencies."""
    import sys
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller bundle - use user's app data directory
        if os.name == 'nt':  # Windows
            USER_CONFIG_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'GlowStatus')
        else:  # macOS/Linux
            USER_CONFIG_DIR = os.path.expanduser('~/.config/GlowStatus')
    elif getattr(sys, 'frozen', False):
        # Other bundle formats
        USER_CONFIG_DIR = os.path.expanduser('~/GlowStatus')
    else:
        # Development mode - use project directory
        USER_CONFIG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    CONFIG_PATH = os.path.join(USER_CONFIG_DIR, 'glowstatus_config.json')
    
    # For development, also check the actual file in the project root
    project_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'glowstatus_config.json')
    if os.path.exists(project_config):
        CONFIG_PATH = project_config
    
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
        except Exception as e:
            print(f"Error reading config file: {e}")
            config = {}
    else:
        config = {}
    
    return config, CONFIG_PATH

if __name__ == "__main__":
    config, config_path = load_config_simple()
    print(f"Config file location: {config_path}")
    print(f"Config file exists: {os.path.exists(config_path)}")
    print(f"Current DISABLE_LIGHT_CONTROL setting: {config.get('DISABLE_LIGHT_CONTROL', 'NOT SET')}")
    print(f"GOVEE_DEVICE_ID: {repr(config.get('GOVEE_DEVICE_ID', ''))}")
    print(f"Has GOVEE_API_KEY in config: {bool(config.get('GOVEE_API_KEY', ''))}")
    print(f"DISABLE_CALENDAR_SYNC: {config.get('DISABLE_CALENDAR_SYNC', 'NOT SET')}")
