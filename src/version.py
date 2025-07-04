"""
Version information utilities for GlowStatus.

This module provides access to version information from version.json
"""

import os
import json


def get_version_info():
    """
    Read version information from version.json in the root directory.
    
    Returns:
        dict: Version information with major, minor, patch, and pre fields
    """
    # Get the root directory (parent of src directory)
    src_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(src_dir)
    version_file = os.path.join(root_dir, 'version.json')
    
    try:
        with open(version_file, 'r') as f:
            version_data = json.load(f)
        
        # Validate required fields
        required_fields = ['major', 'minor', 'patch']
        for field in required_fields:
            if field not in version_data:
                raise ValueError(f"Missing required field '{field}' in version.json")
        
        # Ensure pre field exists
        if 'pre' not in version_data:
            version_data['pre'] = ""
        
        return version_data
    
    except FileNotFoundError:
        print(f"Warning: version.json not found at {version_file}")
        return {"major": 2, "minor": 1, "patch": 0, "pre": ""}
    
    except json.JSONDecodeError as e:
        print(f"Error parsing version.json: {e}")
        return {"major": 2, "minor": 1, "patch": 0, "pre": ""}
    
    except Exception as e:
        print(f"Error reading version.json: {e}")
        return {"major": 2, "minor": 1, "patch": 0, "pre": ""}


def get_version_string():
    """
    Get the version as a formatted string.
    
    Returns:
        str: Version string in format "major.minor.patch" or "major.minor.patch-pre"
    """
    version_info = get_version_info()
    version_str = f"{version_info['major']}.{version_info['minor']}.{version_info['patch']}"
    
    if version_info.get('pre'):
        version_str += f"-{version_info['pre']}"
    
    return version_str


def get_version_display():
    """
    Get a user-friendly version display string.
    
    Returns:
        str: Version string formatted for display
    """
    return f"Version {get_version_string()}"
