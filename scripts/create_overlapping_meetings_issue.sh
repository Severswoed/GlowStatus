#!/bin/bash
# Script to create GitHub issues for GlowStatus feature requests and improvements

# Issue: Overlapping Meetings - Meeting Selection and Alignment
gh issue create \
  --title "Feature: Meeting Selection for Overlapping Events" \
  --body "## Problem
When multiple calendar events overlap, GlowStatus currently uses the first/earliest meeting to determine status and light behavior. However, users may want to align their status with a specific meeting from the overlapping set.

## Current Behavior
- System automatically selects meeting based on calendar API response order
- No user control over which overlapping meeting to prioritize
- Status changes are tied to the system-selected meeting's timing

## Proposed Enhancement
Add functionality to allow users to:
1. **View overlapping meetings** when they occur
2. **Select which meeting to align status with** 
3. **Switch alignment** between overlapping meetings during the overlap period
4. **Set preferences** for automatic selection (earliest start, latest end, specific keywords, etc.)

## User Stories
- As a user with back-to-back meetings, I want to choose which meeting my status reflects
- As a user with optional vs required meetings, I want to prioritize the required one
- As a user with personal vs work overlaps, I want to select the work meeting for status
- As a user with long meetings, I want to switch to a shorter overlapping meeting when it starts

## Implementation Considerations
- **UI/UX**: Tray menu option to show/select active meetings
- **Persistence**: Remember user's choice for similar future overlaps  
- **Notifications**: Alert user when overlapping meetings are detected
- **Calendar Integration**: Respect meeting importance/priority if available
- **Status Transitions**: Handle light changes when switching between meetings

## Acceptance Criteria
- [ ] Detect when multiple meetings overlap
- [ ] Present meeting selection interface to user
- [ ] Allow real-time switching between overlapping meetings
- [ ] Maintain status alignment with selected meeting
- [ ] Provide preference settings for automatic selection rules
- [ ] Handle edge cases (meeting ends early, new meeting added, etc.)

## Priority
Medium - Enhances user control and meeting management accuracy

## Related
- Meeting transition logic (already implemented)
- Manual override functionality  
- Tray menu interactions
- Calendar sync improvements" \
  --label "enhancement,user-experience,calendar-sync" \
  --assignee "@me"

echo "✅ Created GitHub issue for overlapping meetings feature"
