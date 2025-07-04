#!/usr/bin/env python3
"""
Test sidebar structure without Qt dependencies
"""

def test_sidebar_structure():
    """Test that the sidebar setup method structure is correct"""
    
    # Read the settings_ui.py file and verify the sidebar structure
    with open('src/settings_ui.py', 'r') as f:
        content = f.read()
    
    # Check for key components
    checks = [
        ('sidebar_container', 'sidebar_container' in content),
        ('discord_btn', 'discord_btn' in content),
        ('github_btn', 'github_btn' in content), 
        ('sponsor_btn', 'sponsor_btn' in content),
        ('setup_sidebar method', 'def setup_sidebar(self):' in content),
        ('Quick Links title', 'Quick Links' in content),
        ('Discord button styling', '#5865f2' in content),  # Discord blue
        ('GitHub button styling', '#24292f' in content),  # GitHub dark
        ('Sponsor button styling', '#ea4aaa' in content), # Pink sponsor color
        ('Actions menu', 'actions_menu' in content),
        ('Menu bar Actions', '🎯 Actions' in content),
    ]
    
    print("🔍 Testing sidebar structure...")
    print("=" * 50)
    
    all_passed = True
    for name, check in checks:
        status = "✓" if check else "✗"
        print(f"{status} {name}")
        if not check:
            all_passed = False
    
    print("=" * 50)
    
    if all_passed:
        print("🎉 All sidebar structure tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False

if __name__ == '__main__':
    import os
    os.chdir('/workspaces/GlowStatus')
    test_sidebar_structure()
