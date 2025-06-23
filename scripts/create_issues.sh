#!/bin/bash

# Titles, bodies, and labels for issues
declare -a TITLES=(
  "[story] Integrate OAuth 2.0 Google Authentication"
  "[story] Add UI for Customizing Light Colors and Status Mapping"
  "[story] Sync Status with Slack and Microsoft Teams"
  "[task] Add Tray Icon with Manual Override for Status Control"
  "[story] Auto Dimming of Lights Based on Time or Ambient Light"
  "[story] Build Configuration UI for Non-Technical Users"
  "[story] Initiate Partner Outreach for GlowStatus Integrations"
  "[task] Track Partner Response - LIFX"
  "[task] Track Partner Response - Nanoleaf"
  "[task] Track Partner Response - Philips Hue"
)

declare -a BODIES=(
  "Enable OAuth 2.0 authentication with Google accounts to allow secure and scoped access to the user's calendar.

**Acceptance Criteria:**
- User can sign in with their Google account
- Auth token is securely stored and refreshed
- Calendar read-only permission scoped"

  "Allow users to customize RGB light colors for different availability statuses (e.g., busy, available, away).

**Acceptance Criteria:**
- UI for mapping status to specific RGB values
- Persisted user preferences"

  "Extend functionality to optionally sync user presence/status with Slack or Microsoft Teams.

**Acceptance Criteria:**
- Toggle Slack/Teams sync via settings
- Respect availability from synced platform"

  "Implement a system tray icon allowing users to view status and override availability manually.

**Acceptance Criteria:**
- Tray icon available on launch
- Right-click menu includes manual override options (Busy, Available, etc.)"

  "Support auto-dimming feature based on either a user-defined time range (e.g. after 8pm) or ambient light sensor input (if supported).

**Acceptance Criteria:**
- Configurable time-based dimming
- Optional ambient light sensor detection
- Overrides don’t disable availability updates"

  "Create a user-friendly GUI to manage configuration options, replacing or supplementing \`.env\` or CLI-only setups.

**Acceptance Criteria:**
- Cross-platform support (Mac, Windows)
- Allow easy input for tokens, Govee device selection, status mapping
- Save and persist settings"

  "Kick off outreach to partners and third-party developers (e.g. Govee, Slack, Microsoft) for potential collaboration, API insights, and early integration guidance.

**Acceptance Criteria:**
- Identify initial list of contacts at Govee, Slack, and Microsoft
- Prepare introduction email/template
- Track responses and potential partnerships"

  "Track response and follow-up with LIFX regarding integration partnership request.

**Acceptance Criteria:**
- Initial request sent
- Response received or follow-up documented
- Status updated"

  "Track response and follow-up with Nanoleaf regarding integration partnership request.

**Acceptance Criteria:**
- Initial request sent
- Response received or follow-up documented
- Status updated"

  "Track response and follow-up with Philips Hue regarding integration partnership request.

**Acceptance Criteria:**
- Initial request sent
- Response received or follow-up documented
- Status updated"
)

declare -a LABELS=(
  "authentication,google,enhancement,backlog,story"
  "ui,settings,enhancement,backlog,story"
  "integration,slack,teams,enhancement,backlog,story"
  "ui,tray,manual-override,task,backlog"
  "enhancement,ux,sensor,backlog,story"
  "ui,config,accessibility,enhancement,backlog,story"
  "partnerships,outreach,integration,backlog,story"
  "partnerships,outreach,tracking,task,backlog"
  "partnerships,outreach,tracking,task,backlog"
  "partnerships,outreach,tracking,task,backlog"
)

# Create all unique labels before creating issues
ALL_LABELS=$(printf "%s\n" "${LABELS[@]}" | tr ',' '\n' | sort -u)
for label in $ALL_LABELS; do
  if ! gh label list | grep -q "^$label"; then
    echo "Creating label: $label"
    gh label create "$label" --color "ededed" --description "$label"
  fi
done

# Create issues
for i in "${!TITLES[@]}"; do
  echo "Creating issue: ${TITLES[$i]}"
  gh issue create \
    --title "${TITLES[$i]}" \
    --body "${BODIES[$i]}" \
    --label "${LABELS[$i]}"
done