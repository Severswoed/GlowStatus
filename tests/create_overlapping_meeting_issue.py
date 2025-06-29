#!/usr/bin/env python3
"""
Create GitHub issue for overlapping meetings alignment feature.
"""

import subprocess
import sys

def create_issue():
    """Create a GitHub issue for overlapping meetings alignment."""
    
    title = "Overlapping Meetings: User-Selectable Meeting Alignment and Priority"
    
    body = """## Problem Statement
When multiple calendar meetings overlap, GlowStatus currently uses automatic logic to determine which meeting to align with for status detection and light control. However, users need the ability to explicitly choose which meeting they want to align with, especially in scenarios with:

- **Back-to-back meetings with gaps**
- **Overlapping meetings of different importance** 
- **Personal vs. work meeting conflicts**
- **Meeting conflicts requiring different status displays**

## Current Behavior
- System automatically selects meetings based on timing logic
- User has no control over which overlapping meeting takes priority
- Manual overrides (`meeting_ended_early`) work but don't persist across meeting transitions

## Proposed Solution
Add overlapping meeting management features:

### 1. Meeting Selection UI
- **Tray menu option**: "Select Active Meeting" when overlaps detected
- **Quick picker**: Show list of overlapping meetings with start/end times
- **Priority setting**: Allow users to set default meeting priority rules

### 2. Meeting Priority Configuration  
- **Calendar-based rules**: Work calendar vs personal calendar priority
- **Keyword-based rules**: Meetings with certain keywords take priority
- **Duration-based rules**: Longer meetings vs shorter meetings
- **Participant-based rules**: Meetings with specific people/groups

### 3. Visual Indicators
- **Tray tooltip**: Show which meeting is currently "active" for status
- **Meeting conflict indicator**: Visual cue when overlaps are detected
- **Quick switch option**: Easy way to change active meeting

## User Stories
- **As a user**, I want to choose which overlapping meeting controls my status lights
- **As a user**, I want to set rules so important meetings always take priority
- **As a user**, I want to see which meeting is currently controlling my status
- **As a user**, I want to quickly switch between overlapping meetings

## Technical Considerations
- Requires enhancement to calendar sync logic
- Need persistent storage for user meeting preferences
- UI changes to tray menu and settings
- Backward compatibility with existing single-meeting logic

## Acceptance Criteria
- [ ] Detect when multiple meetings overlap
- [ ] Provide UI to select which meeting is "active"
- [ ] Save user meeting selection preferences
- [ ] Visual indicator of active meeting in tray
- [ ] Configuration options for automatic priority rules
- [ ] Smooth transition when overlaps resolve

## Priority
**Medium** - Enhances user experience for complex calendar scenarios

## Related Issues
- Meeting transition logic (recent fixes)
- Manual override improvements
- Calendar sync enhancements
"""

    labels = [
        "enhancement",
        "manual-override", 
        "config",
        "ux"
    ]
    
    # Build the command
    cmd = [
        "gh", "issue", "create",
        "--title", title,
        "--body", body,
    ]
    
    # Add labels
    for label in labels:
        cmd.extend(["--label", label])
    
    try:
        print("🚀 Creating GitHub issue for overlapping meetings alignment...")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        print("✅ Issue created successfully!")
        print(f"📋 Issue URL: {result.stdout.strip()}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create issue: {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)

if __name__ == "__main__":
    create_issue()
