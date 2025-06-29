#!/usr/bin/env python3
"""
Manual Test for Light Control Toggle in Tray Menu

STEPS TO TEST:
1. Run GlowStatus
2. Right-click the tray icon to open the context menu
3. Look for "Enable Lights" or "Disable Lights" menu item
4. Click the toggle and verify:
   - Menu text changes appropriately
   - Tooltip reflects the change (hover over tray icon)
   - If enabling lights with proper Govee config, lights should update immediately
   - Config is saved (check settings window)

EXPECTED BEHAVIOR:

Initial State (depends on config):
- If light control is enabled: Menu shows "Disable Lights"
- If light control is disabled: Menu shows "Enable Lights"

Toggle from Enabled to Disabled:
- Menu text changes from "Disable Lights" to "Enable Lights"
- Tooltip shows "(Lights OFF)" indicator
- No immediate light change (lights remain in current state)
- Settings window shows "Disable Light Control" checked

Toggle from Disabled to Enabled:
- Menu text changes from "Enable Lights" to "Disable Lights"
- Tooltip removes "(Lights OFF)" indicator
- If Govee is configured, lights update immediately to current status
- Settings window shows "Disable Light Control" unchecked

Tooltip Examples:
- Both enabled: "GlowStatus - available (primary)"
- Lights off: "GlowStatus - available (primary) (Lights OFF)"
- Sync off: "GlowStatus - available (primary) (Sync OFF)"
- Both off: "GlowStatus - available (primary) (Sync OFF, Lights OFF)"

CONFIGURATION TESTED:
- DISABLE_LIGHT_CONTROL config option
- Menu text updates
- Tooltip status indicators
- Immediate light updates when enabling
- Configuration persistence
"""

print("Manual test checklist created for Light Control Toggle in Tray Menu")
print("Run this checklist after starting GlowStatus to verify the feature works correctly.")
