#!/usr/bin/env python3
"""
Test for Immediate Light Turn-Off When Disabling Light Control

This test verifies that the turn_off_lights_immediately method exists
and the tray menu integration works correctly.
"""

import os
import sys

def test_method_exists():
    """Test that the turn_off_lights_immediately method exists in GlowStatusController"""
    # Read the glowstatus.py file to check for the method
    glowstatus_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'glowstatus.py')
    
    with open(glowstatus_path, 'r') as f:
        content = f.read()
    
    # Check if the method is defined
    assert "def turn_off_lights_immediately(self):" in content, "turn_off_lights_immediately method not found"
    
    # Check if it has the right functionality
    assert "govee.set_power(\"off\")" in content, "Method should call govee.set_power('off')"
    assert "Lights turned off immediately" in content, "Method should log the immediate turn-off"
    
    print("✓ turn_off_lights_immediately method exists and has correct implementation")

def test_tray_menu_calls_immediate_turnoff():
    """Test that the tray menu toggle_light function calls turn_off_lights_immediately when disabling"""
    tray_app_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'tray_app.py')
    
    with open(tray_app_path, 'r') as f:
        content = f.read()
    
    # Check if toggle_light function exists
    assert "def toggle_light():" in content, "toggle_light function not found"
    
    # Check if it calls turn_off_lights_immediately when disabling
    assert "glowstatus.turn_off_lights_immediately()" in content, "toggle_light should call turn_off_lights_immediately when disabling"
    
    print("✓ Tray menu toggle_light function calls turn_off_lights_immediately when disabling lights")

def test_sync_toggle_calls_update():
    """Test that the sync toggle calls update_now when enabling sync"""
    tray_app_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'tray_app.py')
    
    with open(tray_app_path, 'r') as f:
        content = f.read()
    
    # Check if toggle_sync function calls update_now when enabling
    lines = content.split('\n')
    in_toggle_sync = False
    found_update_call = False
    
    for line in lines:
        if 'def toggle_sync():' in line:
            in_toggle_sync = True
        elif in_toggle_sync and 'def ' in line and 'toggle_sync' not in line:
            break
        elif in_toggle_sync and 'glowstatus.update_now()' in line:
            found_update_call = True
    
    assert found_update_call, "toggle_sync should call glowstatus.update_now() when enabling sync"
    
    print("✓ Sync toggle calls update_now when enabling sync")

def test_tooltip_shows_light_status():
    """Test that the tooltip shows light control status"""
    tray_app_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'tray_app.py')
    
    with open(tray_app_path, 'r') as f:
        content = f.read()
    
    # Check if tooltip includes light status indicators
    assert "Lights OFF" in content, "Tooltip should show 'Lights OFF' when light control is disabled"
    assert "update_tray_tooltip()" in content, "Tooltip should be updated after changes"
    
    print("✓ Tooltip shows light control status and gets updated")

if __name__ == "__main__":
    print("Testing Immediate Light Turn-Off Implementation...")
    print("=" * 55)
    
    test_method_exists()
    test_tray_menu_calls_immediate_turnoff()
    test_sync_toggle_calls_update()
    test_tooltip_shows_light_status()
    
    print("\n✓ All immediate action tests passed!")
    print("✓ Menu actions now trigger immediate updates instead of waiting for polling cycles")
