# 🌟 GlowStatus

**Smart Presence Indicator with Govee + Google Workspace**

GlowStatus is a lightweight, cross-platform status indicator system that integrates Govee smart lights with your Google Calendar to show your availability at a glance. It’s perfect for home offices, shared spaces, and remote work setups.

---

## 🚀 Features

- ⏰ **Real-time Meeting Detection** – Syncs with Google Calendar to detect your meeting status
- 💡 **Smart Light Control** – Uses Govee API to change light colors based on presence
- ⚙️ **Configurable Modes** – Set custom color themes for:
  - In a Meeting
  - Available
  - Focus Mode
  - Offline
- 🔐 **Secure by Default** – Uses `.env` for secure API key and token management
- 📱 **Mobile & Codespace Friendly** – Designed to work on iPad via GitHub Codespaces

---

## 📦 Project Structure

```
GlowStatus/
├── src/
│   ├── glowstatus.py             # Main control logic
│   ├── govee_controller.py       # Govee API integration
│   ├── calendar_sync.py          # Google Calendar sync logic
│   ├── logger.py                 # Logging utilities
│   └── utils.py                  # Helper functions
├── tests/
│   └── test_man.py               # Unit tests for utilities and logic
├── .env.example                  # Sample env config
├── setup.sh                      # Bootstrap script
├── requirements.txt              # Python dependencies
├── README.md                     # You're here!
└── LICENSE                       # MIT License
```

---

## 🛠️ Setup Instructions

1. **Clone the Repo**
   ```bash
   git clone https://github.com/Severswoed/GlowStatus.git
   cd GlowStatus
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create and Configure `.env`**
   ```bash
   cp .env.example .env
   # Fill in Govee API Key, Device ID, Google Calendar ID, and service account JSON path.
   ```

4. **Run the App**
   ```bash
   python src/glowstatus.py
   ```

---

## 🧪 Example `.env`

```env
# .env.example
GOVEE_API_KEY=your-govee-api-key
GOVEE_DEVICE_ID=your-light-device-id
GOOGLE_CALENDAR_ID=primary
GOOGLE_SERVICE_ACCOUNT_JSON=/path/to/your/service_account.json
REFRESH_INTERVAL=60
```

---

## 🎯 Future Roadmap

- Slack/Teams status sync
- Tray icon with manual override
- Time-based or ambient-light auto dimming
- Config UI for non-technical users

---

## 📋 License

MIT License — see [LICENSE](./LICENSE) for full details.

---

## 💬 Feedback & Contributions

Ideas? Bugs? PRs are welcome. File an issue or drop a discussion topic!

---

### 🔗 Related Projects
- [Govee Developer Portal](https://developer.govee.com)
- [Google Calendar API Docs](https://developers.google.com/calendar/api)

---

Let your **GlowStatus** speak for you! 💙
