# Getting Started with GlowStatus

Welcome to GlowStatus! This guide will walk you through the essential steps to get up and running, from Google OAuth setup to smart light integration and calendar sync.

---

## 1. Google OAuth Setup

GlowStatus uses Google Calendar to detect your meeting and focus status. To enable this, you need to connect your Google account:

1. **Launch GlowStatus.**
2. In the settings window, on the OAuth page, click **"Connect Google Calendar (OAuth)"**.
3. Sign in with your Google account and grant the requested permissions.
4. After authentication, select your preferred calendar from the dropdown list on the calendar page.

> **Tip:** Your OAuth credentials are stored securely in `resources/client_secret.json` and your token in `config/google_token.pickle`.

---

## 2. Govee Smart Light Integration

GlowStatus can control your Govee smart lights to visually indicate your status.

1. **Obtain your Govee API Key:**
   - Follow the instructions in [docs/govee_apikey_instructions.md](./docs/govee_apikey_instructions.md).
2. **Find your Device ID and Model:**
   - See [docs/govee_device_id_instructions.md](./docs/govee_device_id_instructions.md).
3. **Enter your credentials:**
   - Open the settings window in GlowStatus.
   - Enter your API key, device ID, and device model.

---

## 3. Calendar Sync Setup

1. **Choose your calendar:**
   - After OAuth, select the calendar you want GlowStatus to monitor.
2. **Configure status keywords:**
   - Add or edit keywords (e.g., `focus`, `meeting`, `lunch`) in the settings window.
   - Assign colors and power-off options for each status.

---

## 4. Enable Sync and Lights

1. **Enable calendar sync:**
   - Toggle the sync option in the settings window to start automatic status detection.
2. **Test your setup:**
   - Create a test event in your calendar with a matching keyword (e.g., `focus`).
   - Your Govee light should change color according to your configuration.
3. **Manual override:**
   - Use the tray menu to set your status manually if needed.

---

## 5. Troubleshooting & Support

- If you encounter issues, check the logs or see the [Troubleshooting](./README.md#%F0%9F%9B%A0%EF%B8%8F-troubleshooting) section in the main README.
- Join our [Discord server](https://discord.gg/TcKVQkS274) for real-time help and community support.

---

You're all set! Enjoy automated, visual status updates with GlowStatus.
