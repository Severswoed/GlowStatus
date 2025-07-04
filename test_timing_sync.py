#!/usr/bin/env python3
"""
Test the timing synchronization to ensure the app checks at precise intervals
(15-second boundaries: 0, 15, 30, 45 seconds past each minute)
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from datetime import datetime
import time

def test_15_second_sync_calculation():
    """Test the calculation logic for 15-second boundary synchronization."""
    
    print("Testing 15-second boundary sync calculation...")
    print("=" * 50)
    
    # Test various times and their expected next boundaries
    test_cases = [
        # (current_seconds, expected_next_boundary, description)
        (0.0, 15, "At 0 seconds -> next is 15"),
        (7.5, 15, "At 7.5 seconds -> next is 15"),
        (14.9, 15, "At 14.9 seconds -> next is 15"),
        (15.0, 30, "At 15 seconds -> next is 30"),
        (22.3, 30, "At 22.3 seconds -> next is 30"),
        (29.9, 30, "At 29.9 seconds -> next is 30"),
        (30.0, 45, "At 30 seconds -> next is 45"),
        (37.1, 45, "At 37.1 seconds -> next is 45"),
        (44.9, 45, "At 44.9 seconds -> next is 45"),
        (45.0, 60, "At 45 seconds -> next is 0 (next minute)"),
        (52.7, 60, "At 52.7 seconds -> next is 0 (next minute)"),
        (59.9, 60, "At 59.9 seconds -> next is 0 (next minute)"),
    ]
    
    for seconds_into_minute, expected_boundary, description in test_cases:
        # This is the calculation from the updated _sleep_until_next_interval
        next_boundary = ((int(seconds_into_minute) // 15) + 1) * 15
        if next_boundary >= 60:
            next_boundary = 0
            sleep_time = 60 - seconds_into_minute
        else:
            sleep_time = next_boundary - seconds_into_minute
        
        actual_boundary = next_boundary if next_boundary > 0 else 60
        
        print(f"{description}")
        print(f"  Current: {seconds_into_minute:05.1f}s -> Next boundary: {actual_boundary:02d}s -> Sleep: {sleep_time:.1f}s")
        
        # Verify the calculation
        if actual_boundary != expected_boundary:
            print(f"  ❌ ERROR: Expected {expected_boundary}, got {actual_boundary}")
        else:
            print(f"  ✅ Correct")
        print()

def test_real_time_sync():
    """Test with actual current time to see what the sync would do."""
    
    print("\nTesting with current real time...")
    print("=" * 50)
    
    now = datetime.now()
    seconds_into_minute = now.second + now.microsecond / 1_000_000
    
    print(f"Current time: {now.strftime('%H:%M:%S.%f')[:-3]}")
    print(f"Seconds into minute: {seconds_into_minute:.3f}")
    
    # Calculate 15-second boundary sync
    next_boundary = ((int(seconds_into_minute) // 15) + 1) * 15
    if next_boundary >= 60:
        next_boundary = 0
        sleep_time = 60 - seconds_into_minute
        next_check_desc = "next minute at :00"
    else:
        sleep_time = next_boundary - seconds_into_minute
        next_check_desc = f":{next_boundary:02d}"
    
    print(f"Next 15s boundary: {next_check_desc}")
    print(f"Sleep time needed: {sleep_time:.3f} seconds")
    
    # Simulate what the next check time would be
    next_check_time = now.timestamp() + sleep_time
    next_check_dt = datetime.fromtimestamp(next_check_time)
    print(f"Next check would be at: {next_check_dt.strftime('%H:%M:%S.%f')[:-3]}")
    print(f"Next check seconds: :{next_check_dt.second:02d}")
    
    # Verify it's on a 15-second boundary
    expected_boundaries = [0, 15, 30, 45]
    if next_check_dt.second in expected_boundaries:
        print("✅ Next check time is correctly aligned to 15-second boundary")
    else:
        print(f"❌ Next check time is NOT aligned! Second value: {next_check_dt.second}")

def demonstrate_sync_sequence():
    """Show what a sequence of sync points would look like."""
    
    print("\nDemonstrating sync sequence...")
    print("=" * 50)
    
    # Start from an arbitrary time
    base_time = datetime(2025, 7, 4, 12, 17, 23, 456789)  # 12:17:23.456
    print(f"Starting from: {base_time.strftime('%H:%M:%S.%f')[:-3]}")
    print()
    
    current_time = base_time
    
    for i in range(8):  # Show 8 sync points
        seconds_into_minute = current_time.second + current_time.microsecond / 1_000_000
        
        # Calculate sleep time to next boundary
        next_boundary = ((int(seconds_into_minute) // 15) + 1) * 15
        if next_boundary >= 60:
            sleep_time = 60 - seconds_into_minute
            next_boundary_desc = "00"
        else:
            sleep_time = next_boundary - seconds_into_minute
            next_boundary_desc = f"{next_boundary:02d}"
        
        print(f"Check #{i+1}: {current_time.strftime('%H:%M:%S.%f')[:-3]} -> sleep {sleep_time:.3f}s -> next check at :{next_boundary_desc}")
        
        # Advance to next check time
        next_time_seconds = current_time.timestamp() + sleep_time
        current_time = datetime.fromtimestamp(next_time_seconds)

if __name__ == "__main__":
    test_15_second_sync_calculation()
    test_real_time_sync()
    demonstrate_sync_sequence()
