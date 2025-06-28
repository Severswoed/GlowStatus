#!/usr/bin/env python3
"""
Test script to verify that custom status keywords work correctly
"""

import sys
import os
sys.path.append('.')

from src.utils import normalize_status

def test_status_detection():
    # Example custom color map from settings
    custom_color_map = {
        "lunch": {"color": "0,255,0", "power_off": True},
        "break": {"color": "255,255,0", "power_off": True}, 
        "focus": {"color": "0,0,255", "power_off": False},
        "deep work": {"color": "128,0,128", "power_off": False},
        "in_meeting": {"color": "255,0,0", "power_off": False},
        "available": {"color": "0,255,0", "power_off": True},
    }

    test_cases = [
        "Lunch with team",
        "Break time", 
        "Focus mode - deep work",
        "Team meeting",
        "Morning standup",
        "Coffee break",
        "Available for questions",
        "Random event title",
    ]

    print("=" * 60)
    print("Testing Custom Status Keyword Detection")
    print("=" * 60)
    print(f"Custom keywords: {list(custom_color_map.keys())}")
    print()

    for event_title in test_cases:
        detected_status = normalize_status(event_title, custom_color_map)
        print(f"'{event_title}' -> '{detected_status}'")
    
    print()
    print("=" * 60)
    print("Testing Default Behavior (without custom map)")
    print("=" * 60)
    
    for event_title in test_cases:
        detected_status = normalize_status(event_title)
        print(f"'{event_title}' -> '{detected_status}'")

if __name__ == "__main__":
    test_status_detection()
