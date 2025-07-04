#!/usr/bin/env python3
"""
Diagnostic test to verify the periodic status check loop is running correctly.
This will help identify if the 15-second timer is working properly.
"""

import sys
import os
import time
import threading
import datetime
from unittest.mock import patch, MagicMock

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from glowstatus import GlowStatusController


def test_periodic_loop_execution():
    """Test that the periodic loop actually executes every 15 seconds."""
    
    print("🔍 Testing Periodic Loop Execution")
    print("=" * 50)
    
    # Track loop executions
    loop_executions = []
    
    # Mock dependencies to prevent real API calls
    with patch('glowstatus.load_secret') as mock_load_secret, \
         patch('glowstatus.CalendarSync') as mock_calendar_sync, \
         patch('glowstatus.GoveeController') as mock_govee, \
         patch('glowstatus.resource_path') as mock_resource_path, \
         patch('glowstatus.os.path.exists') as mock_exists, \
         patch('glowstatus.load_config') as mock_load_config, \
         patch('glowstatus.save_config') as mock_save_config:
        
        # Setup mocks
        mock_load_secret.return_value = "test_api_key"
        mock_resource_path.return_value = "/path/to/client_secret.json"
        mock_exists.return_value = True
        
        # Mock config
        test_config = {
            "GOVEE_DEVICE_ID": "test_device",
            "GOVEE_DEVICE_MODEL": "H6159", 
            "SELECTED_CALENDAR_ID": "test@example.com",
            "STATUS_COLOR_MAP": {
                "in_meeting": {"color": "255,0,0", "power_off": False},
                "available": {"color": "0,255,0", "power_off": True}
            },
            "REFRESH_INTERVAL": 15,
            "DISABLE_CALENDAR_SYNC": False,
            "DISABLE_LIGHT_CONTROL": False,
            "CURRENT_STATUS": None
        }
        
        def track_config_access():
            """Track when the config is loaded (indicates loop execution)."""
            execution_time = datetime.datetime.now()
            loop_executions.append(execution_time)
            print(f"  ⏰ Loop execution #{len(loop_executions)} at {execution_time.strftime('%H:%M:%S.%f')[:-3]}")
            return test_config.copy()
        
        mock_load_config.side_effect = track_config_access
        
        # Mock calendar sync
        mock_calendar = MagicMock()
        mock_calendar.get_current_status.return_value = ("available", None)
        mock_calendar_sync.return_value = mock_calendar
        
        # Mock Govee controller
        mock_govee_instance = MagicMock()
        mock_govee.return_value = mock_govee_instance
        
        # Create and start controller
        controller = GlowStatusController()
        
        print("🚀 Starting GlowStatus controller...")
        controller.start()
        
        # Let it run for about 45 seconds to see multiple executions
        test_duration = 45
        print(f"⏳ Running for {test_duration} seconds to observe periodic execution...")
        
        start_time = time.time()
        time.sleep(test_duration)
        
        print("🛑 Stopping controller...")
        controller.stop()
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        print(f"\n📊 Test Results:")
        print(f"   • Test Duration: {actual_duration:.1f} seconds")
        print(f"   • Expected Executions: ~{int(actual_duration / 15)}")
        print(f"   • Actual Executions: {len(loop_executions)}")
        
        if len(loop_executions) >= 2:
            print(f"   • ✅ Loop is executing periodically!")
            
            # Check timing intervals
            if len(loop_executions) >= 2:
                intervals = []
                for i in range(1, len(loop_executions)):
                    interval = (loop_executions[i] - loop_executions[i-1]).total_seconds()
                    intervals.append(interval)
                    print(f"     Interval {i}: {interval:.2f} seconds")
                
                avg_interval = sum(intervals) / len(intervals)
                print(f"   • Average Interval: {avg_interval:.2f} seconds")
                
                if 14 <= avg_interval <= 16:
                    print(f"   • ✅ Timing is correct (~15 seconds)")
                else:
                    print(f"   • ❌ Timing is incorrect (expected ~15 seconds)")
        else:
            print(f"   • ❌ Loop is NOT executing properly!")
            print(f"   • This indicates the periodic status check is broken")
            
        return len(loop_executions) >= 2


def test_thread_lifecycle():
    """Test that the controller thread starts and stops properly."""
    
    print("\n🧵 Testing Thread Lifecycle")
    print("=" * 50)
    
    controller = GlowStatusController()
    
    print("🔍 Initial state:")
    print(f"   • _running: {controller._running}")
    print(f"   • _thread: {controller._thread}")
    
    print("🚀 Starting controller...")
    controller.start()
    
    print("🔍 After start:")
    print(f"   • _running: {controller._running}")
    print(f"   • _thread: {controller._thread}")
    print(f"   • Thread alive: {controller._thread.is_alive() if controller._thread else 'None'}")
    
    time.sleep(2)  # Let it run briefly
    
    print("🛑 Stopping controller...")
    controller.stop()
    
    print("🔍 After stop:")
    print(f"   • _running: {controller._running}")
    print(f"   • _thread: {controller._thread}")
    
    if controller._running:
        print("   • ❌ Controller not properly stopped")
        return False
    else:
        print("   • ✅ Controller properly stopped")
        return True


def test_exception_handling():
    """Test that exceptions in the loop don't kill the thread."""
    
    print("\n💥 Testing Exception Handling")
    print("=" * 50)
    
    with patch('glowstatus.load_config') as mock_load_config:
        # Make load_config throw an exception
        mock_load_config.side_effect = Exception("Test exception")
        
        controller = GlowStatusController()
        controller.start()
        
        # Let it run briefly and see if thread survives
        time.sleep(3)
        
        is_alive = controller._thread.is_alive() if controller._thread else False
        print(f"   • Thread alive after exception: {is_alive}")
        
        controller.stop()
        
        if is_alive:
            print("   • ✅ Thread survived exceptions")
            return True
        else:
            print("   • ❌ Thread died from exceptions")
            return False


if __name__ == "__main__":
    print("🩺 GLOWSTATUS PERIODIC LOOP DIAGNOSTIC")
    print("=" * 60)
    
    results = []
    
    # Test 1: Periodic execution
    try:
        result1 = test_periodic_loop_execution()
        results.append(("Periodic Execution", result1))
    except Exception as e:
        print(f"❌ Periodic execution test failed: {e}")
        results.append(("Periodic Execution", False))
    
    # Test 2: Thread lifecycle
    try:
        result2 = test_thread_lifecycle()
        results.append(("Thread Lifecycle", result2))
    except Exception as e:
        print(f"❌ Thread lifecycle test failed: {e}")
        results.append(("Thread Lifecycle", False))
    
    # Test 3: Exception handling
    try:
        result3 = test_exception_handling()
        results.append(("Exception Handling", result3))
    except Exception as e:
        print(f"❌ Exception handling test failed: {e}")
        results.append(("Exception Handling", False))
    
    print("\n📋 Final Results:")
    print("=" * 30)
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! The periodic loop should be working correctly.")
    else:
        print("\n⚠️  Some tests failed! There's likely an issue with the periodic execution.")
    
    print("\n🔧 If the periodic loop isn't working:")
    print("   1. Check the logs for exceptions in the main loop")
    print("   2. Verify the thread isn't dying silently")
    print("   3. Ensure config loading isn't failing repeatedly")
    print("   4. Check if DISABLE_CALENDAR_SYNC or DISABLE_LIGHT_CONTROL is set")
