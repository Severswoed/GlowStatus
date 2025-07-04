#!/usr/bin/env python3
"""
Test the thread monitoring fix for GlowStatus.
This will test if the periodic loop stays alive with the new monitoring.
"""

import sys
import os
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_thread_monitoring():
    """Test the thread monitoring and recovery system."""
    
    print("🧵 TESTING THREAD MONITORING FIX")
    print("=" * 50)
    
    from glowstatus import GlowStatusController
    
    print("🚀 Starting GlowStatus controller with monitoring...")
    controller = GlowStatusController()
    controller.start()
    
    print("⏰ Running for 60 seconds to test periodic updates...")
    start_time = time.time()
    
    while time.time() - start_time < 60:
        if controller._thread and controller._thread.is_alive():
            print(f"✅ Thread alive at {time.time() - start_time:.1f}s")
        else:
            print(f"❌ Thread died at {time.time() - start_time:.1f}s")
            break
        time.sleep(10)
    
    print("🛑 Stopping controller...")
    controller.stop()
    
    print("✅ Test completed")

if __name__ == "__main__":
    test_thread_monitoring()
