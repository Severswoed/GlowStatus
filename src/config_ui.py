import sys, os, json, keyring, pickle
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QColorDialog, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QInputDialog, QCheckBox, QSpinBox
)
from PySide6.QtCore import Qt
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CONFIG_DIR = "./config"
CONFIG_PATH = os.path.join(CONFIG_DIR, "glowstatus_config.json")
TOKEN_PATH = os.path.join(CONFIG_DIR, "google_token.pickle")
CLIENT_SECRET_PATH = os.path.join("resources", "client_secret.json")
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def save_config(data):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}

def save_secret(key, value):
    keyring.set_password("GlowStatus", key, value)

def load_secret(key):
    return keyring.get_password("GlowStatus", key)

class ConfigWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GlowStatus Configuration")
        self.setFixedWidth(500)
        self.init_ui()
        self.load_existing()

    def init_ui(self):
        layout = QVBoxLayout()

        # Govee API Key
        self.govee_api_input = QLineEdit()
        self.govee_api_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel("Govee API Key:"))
        layout.addWidget(self.govee_api_input)

        # Govee Device ID
        self.govee_id_input = QLineEdit()
        layout.addWidget(QLabel("Govee Device ID:"))
        layout.addWidget(self.govee_id_input)

        # Govee Device Model
        self.govee_model_input = QLineEdit()
        layout.addWidget(QLabel("Govee Device Model:"))
        layout.addWidget(self.govee_model_input)

        # Google Calendar ID (auto-filled)
        self.calendar_id_input = QLineEdit()
        layout.addWidget(QLabel("Google Calendar ID:"))
        layout.addWidget(self.calendar_id_input)

        # Google OAuth Button
        self.oauth_btn = QPushButton("Connect Google Calendar (OAuth)")
        self.oauth_btn.clicked.connect(self.handle_oauth)
        layout.addWidget(self.oauth_btn)

        # Refresh Interval
        self.refresh_interval_input = QSpinBox()
        self.refresh_interval_input.setRange(10, 3600)
        self.refresh_interval_input.setValue(60)
        layout.addWidget(QLabel("Refresh Interval (seconds):"))
        layout.addWidget(self.refresh_interval_input)

        # Disable Calendar Sync
        self.disable_calendar_sync_input = QCheckBox("Disable Calendar Sync")
        layout.addWidget(self.disable_calendar_sync_input)

        # Power Off When Available
        self.power_off_input = QCheckBox("Power Off When Available")
        self.power_off_input.setChecked(True)
        layout.addWidget(self.power_off_input)

        # Status/Color Mapping Table
        self.status_table = QTableWidget(3, 2)
        self.status_table.setHorizontalHeaderLabels(["Status Keyword", "Color (RGB)"])
        self.status_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        default_statuses = [("in_meeting", "255,0,0"), ("focus", "0,0,255"), ("available", "0,255,0")]
        for i, (status, color) in enumerate(default_statuses):
            self.status_table.setItem(i, 0, QTableWidgetItem(status))
            self.status_table.setItem(i, 1, QTableWidgetItem(color))
        layout.addWidget(QLabel("Status/Color Mapping:"))
        layout.addWidget(self.status_table)

        self.setLayout(layout)

        # Save Button
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_config)
        layout.addWidget(self.save_btn)

        # Optional: Color picker on double-click
        self.status_table.cellDoubleClicked.connect(self.open_color_picker)

    def open_color_picker(self, row, col):
        if col == 1:
            color = QColorDialog.getColor()
            if color.isValid():
                rgb = f"{color.red()},{color.green()},{color.blue()}"
                self.status_table.setItem(row, 1, QTableWidgetItem(rgb))

    def load_existing(self):
        config = load_config()
        self.govee_id_input.setText(config.get("GOVEE_DEVICE_ID", ""))
        self.govee_model_input.setText(config.get("GOVEE_DEVICE_MODEL", ""))
        self.calendar_id_input.setText(config.get("GOOGLE_CALENDAR_ID", ""))
        self.refresh_interval_input.setValue(config.get("REFRESH_INTERVAL", 60))
        self.disable_calendar_sync_input.setChecked(bool(config.get("DISABLE_CALENDAR_SYNC", False)))
        self.power_off_input.setChecked(bool(config.get("POWER_OFF_WHEN_AVAILABLE", True)))
        api_key = load_secret("GOVEE_API_KEY")
        if api_key:
            self.govee_api_input.setText(api_key)
        # Load status/color mapping if present
        mapping = config.get("STATUS_COLOR_MAP", {})
        for i, (status, color) in enumerate(mapping.items()):
            if i < self.status_table.rowCount():
                self.status_table.setItem(i, 0, QTableWidgetItem(status))
                self.status_table.setItem(i, 1, QTableWidgetItem(color))

    def save_config(self):
        # Save status/color mapping
        mapping = {}
        for row in range(self.status_table.rowCount()):
            status = self.status_table.item(row, 0)
            color = self.status_table.item(row, 1)
            if status and color:
                mapping[status.text().strip()] = color.text().strip()
        config = {
            "GOVEE_DEVICE_ID": self.govee_id_input.text().strip(),
            "GOVEE_DEVICE_MODEL": self.govee_model_input.text().strip(),
            "GOOGLE_CALENDAR_ID": self.calendar_id_input.text().strip(),
            "REFRESH_INTERVAL": self.refresh_interval_input.value(),
            "DISABLE_CALENDAR_SYNC": self.disable_calendar_sync_input.isChecked(),
            "POWER_OFF_WHEN_AVAILABLE": self.power_off_input.isChecked(),
            "STATUS_COLOR_MAP": mapping,
        }
        save_config(config)
        save_secret("GOVEE_API_KEY", self.govee_api_input.text().strip())
        QMessageBox.information(self, "Saved", "Configuration saved securely!")
        self.close()

    def handle_oauth(self):
        # Run OAuth flow and let user pick a calendar
        creds = None
        if os.path.exists(TOKEN_PATH):
            with open(TOKEN_PATH, "rb") as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_PATH, "wb") as token:
                pickle.dump(creds, token)
        service = build("calendar", "v3", credentials=creds)
        calendars = service.calendarList().list().execute().get("items", [])
        if not calendars:
            QMessageBox.warning(self, "No Calendars", "No calendars found for this account.")
            return
        calendar_names = [f"{c.get('summary')} ({c.get('id')})" for c in calendars]
        selected_idx, ok = QInputDialog.getItem(self, "Select Calendar", "Choose your calendar:", calendar_names, 0, False)
        if ok and selected_idx:
            selected = calendars[calendar_names.index(selected_idx)]
            self.calendar_id_input.setText(selected.get("id"))
            QMessageBox.information(self, "Google OAuth", f"Connected to calendar: {selected.get('summary')}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConfigWindow()
    window.show()
    sys.exit(app.exec())