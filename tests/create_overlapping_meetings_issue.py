#!/usr/bin/env python3
"""
Create a GitHub issue for overlapping meetings feature.
"""

import subprocess
import sys
import os

def create_github_issue():
    """Create GitHub issue for overlapping meetings alignment feature."""
    
    title = "Feature: Meeting Priority Selection for Overlapping Meetings"
    
    body = """## Feature Request: Meeting Priority Selection for Overlapping Meetings

### Problem
When multiple meetings overlap, GlowStatus currently uses the first meeting it encounters from the calendar API. Users have no control over which meeting should take priority for status indication and light control.

### Use Cases
1. **Back-to-back meetings with overlap**: User ends Meeting A early, Meeting B is already active
2. **Double-booked meetings**: Two meetings scheduled at the same time  
3. **Meeting extensions**: Meeting A runs over into Meeting B's time slot
4. **Optional vs Required meetings**: User wants to prioritize required meetings over optional ones

### Proposed Solution

#### Phase 1: Meeting Selection UI
- Add tray menu option: "Select Active Meeting" when overlaps detected
- Show submenu with overlapping meeting titles and times
- Allow user to select which meeting should control status/lights
- Store selection temporarily (until meetings end)

#### Phase 2: Smart Priority Rules (Future)
- Meeting importance/priority detection from calendar
- Keyword-based priority (e.g., "standup" < "client call")
- Learning from user selections
- Auto-priority based on meeting attributes

### Technical Implementation
- Enhance `calendar_sync.py` to detect overlapping meetings
- Add meeting selection state to config
- Update status logic to respect selected meeting
- Add tray menu integration for meeting selection
- Store selected meeting ID temporarily

### User Experience
1. When overlap detected: Notification bubble "Multiple meetings detected"
2. Tray icon shows indication of overlap (e.g., blinking or special color)
3. Right-click tray → "Select Active Meeting" → Choose from list
4. Status/lights align to selected meeting duration and calendar
5. Selection persists until all overlapping meetings end

### Priority
**Medium** - Affects users with busy calendars and overlapping meetings

### Acceptance Criteria
- [ ] Detect overlapping meetings in calendar sync
- [ ] Display meeting selection UI in tray menu
- [ ] Store and respect user's meeting selection
- [ ] Status/lights follow selected meeting timeline
- [ ] Clear selection when all meetings end
- [ ] Add configuration option to disable feature

### Related
- Builds on meeting transition fixes in recent commits
- Enhances user control over calendar-driven status management
- Improves accuracy for users with complex meeting schedules

---
*This issue was automatically generated to track the overlapping meetings feature request.*
"""
    
    try:
        # Create the GitHub issue using gh CLI
        cmd = [
            "gh", "issue", "create",
            "--title", title,
            "--body", body,
            "--label", "enhancement,feature-request"
        ]
        
        print("Creating GitHub issue...")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        print("✅ GitHub issue created successfully!")
        print(f"Issue URL: {result.stdout.strip()}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create GitHub issue: {e}")
        print(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ GitHub CLI (gh) not found. Please install it to create issues.")
        print("Install instructions: https://cli.github.com/")
        return False

if __name__ == "__main__":
    success = create_github_issue()
    sys.exit(0 if success else 1)
