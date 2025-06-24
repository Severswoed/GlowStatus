import sys
import os
import json
import keyring
import pickle
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QColorDialog, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox, QCheckBox, QSpinBox, QFrame
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
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("GlowStatus Configuration")
        self.setFixedWidth(500)
        self.init_ui()
        self.load_existing()

    def init_ui(self):
        layout = QVBoxLayout()

        # Authenticated email label (added)
        self.google_email_label = QLabel("Not authenticated")
        layout.addWidget(self.google_email_label)

        # --- Govee Configuration Section ---
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line1)

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

        # --- Google Calendar Configuration Section ---
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line2)

        # Google OAuth Button
        self.oauth_btn = QPushButton("Connect Google Calendar (OAuth)")
        self.oauth_btn.clicked.connect(self.handle_oauth)
        layout.addWidget(self.oauth_btn)

        # Calendar Selection Dropdown
        self.calendar_dropdown = QComboBox()
        self.calendar_dropdown.setEditable(False)
        layout.addWidget(QLabel("Select Calendar to Monitor:"))
        layout.addWidget(self.calendar_dropdown)

        # --- Other Settings Section ---
        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)
        line3.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line3)

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

        # Off for Unknown Status
        self.off_for_unknown_input = QCheckBox("Turn lights off for unknown status")
        self.off_for_unknown_input.setChecked(True)
        layout.addWidget(self.off_for_unknown_input)

        # Status/Color Mapping Table
        default_statuses = [("in_meeting", "255,0,0"), ("focus", "0,0,255"), ("available", "0,255,0")]
        self.status_table = QTableWidget(len(default_statuses), 2)
        self.status_table.setHorizontalHeaderLabels(["Status Keyword", "Color (RGB)"])
        self.status_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for i, (status, color) in enumerate(default_statuses):
            self.status_table.setItem(i, 0, QTableWidgetItem(status))
            self.status_table.setItem(i, 1, QTableWidgetItem(color))
        layout.addWidget(QLabel("Status/Color Mapping:"))
        layout.addWidget(self.status_table)

        # --- Tray Icon Section ---
        line_tray = QFrame()
        line_tray.setFrameShape(QFrame.HLine)
        line_tray.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line_tray)

        # Tray Icon Picker
        img_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../img"))
        tray_icons = [f for f in os.listdir(img_dir) if "_tray_" in f]
        self.tray_icon_dropdown = QComboBox()
        self.tray_icon_dropdown.addItems(tray_icons)
        layout.addWidget(QLabel("Tray Icon:"))
        layout.addWidget(self.tray_icon_dropdown)
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
        self.refresh_interval_input.setValue(config.get("REFRESH_INTERVAL", 60))
        self.disable_calendar_sync_input.setChecked(bool(config.get("DISABLE_CALENDAR_SYNC", False)))
        self.power_off_input.setChecked(bool(config.get("POWER_OFF_WHEN_AVAILABLE", True)))
        self.off_for_unknown_input.setChecked(bool(config.get("OFF_FOR_UNKNOWN_STATUS", True)))
        api_key = load_secret("GOVEE_API_KEY")
        if api_key:
            self.govee_api_input.setText(api_key)
        # Load status/color mapping if present
        mapping = config.get("STATUS_COLOR_MAP", {})
        for i, (status, color) in enumerate(mapping.items()):
            if i < self.status_table.rowCount():
                self.status_table.setItem(i, 0, QTableWidgetItem(status))
                self.status_table.setItem(i, 1, QTableWidgetItem(color))
        # Tray icon
        img_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../img"))
        tray_icons = [f for f in os.listdir(img_dir) if "_tray_" in f]
        self.tray_icon_dropdown.clear()
        self.tray_icon_dropdown.addItems(tray_icons)
        self.tray_icon_dropdown.setCurrentText(config.get("TRAY_ICON", tray_icons[0] if tray_icons else ""))

        # Load calendar selection
        self.selected_calendar_id = config.get("SELECTED_CALENDAR_ID", "")
        self.calendar_dropdown.clear()
        if os.path.exists(TOKEN_PATH):
            try:
                with open(TOKEN_PATH, "rb") as token:
                    creds = pickle.load(token)
                service = build("calendar", "v3", credentials=creds)
                user_info = service.calendarList().list().execute()
                primary_calendar = next((cal for cal in user_info.get("items", []) if cal.get("primary")), None)
                email = primary_calendar.get("id") if primary_calendar else "Unknown"
                self.google_email_label.setText(f"Authenticated as: {email}")

                calendars = user_info.get("items", [])
                for cal in calendars:
                    label = f"{cal.get('summary')} ({cal.get('id')})"
                    self.calendar_dropdown.addItem(label, cal.get("id"))
                # Set dropdown to saved calendar if present
                if self.selected_calendar_id:
                    idx = self.calendar_dropdown.findData(self.selected_calendar_id)
                    if idx >= 0:
                        self.calendar_dropdown.setCurrentIndex(idx)
            except Exception:
                self.google_email_label.setText("Not authenticated")
        else:
            self.google_email_label.setText("Not authenticated")

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
            "TRAY_ICON": self.tray_icon_dropdown.currentText(),
            "SELECTED_CALENDAR_ID": self.calendar_dropdown.currentData(),
            "REFRESH_INTERVAL": self.refresh_interval_input.value(),
            "DISABLE_CALENDAR_SYNC": self.disable_calendar_sync_input.isChecked(),
            "POWER_OFF_WHEN_AVAILABLE": self.power_off_input.isChecked(),
            "OFF_FOR_UNKNOWN_STATUS": self.off_for_unknown_input.isChecked(),
            "STATUS_COLOR_MAP": mapping,
        }
        save_config(config)
        save_secret("GOVEE_API_KEY", self.govee_api_input.text().strip())
        QMessageBox.information(self, "Saved", "Configuration saved securely!")
        self.close()

    def handle_oauth(self):
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
        user_info = service.calendarList().list().execute()
        primary_calendar = next((cal for cal in user_info.get("items", []) if cal.get("primary")), None)
        email = primary_calendar.get("id") if primary_calendar else "Unknown"
        self.google_email_label.setText(f"Authenticated as: {email}")

        calendars = user_info.get("items", [])
        self.calendar_dropdown.clear()
        if not calendars:
            QMessageBox.warning(self, "No Calendars", "No calendars found for this account.")
            return
        for cal in calendars:
            label = f"{cal.get('summary')} ({cal.get('id')})"
            self.calendar_dropdown.addItem(label, cal.get("id"))
        if calendars:
            self.calendar_dropdown.setCurrentIndex(0)
            QMessageBox.information(self, "Google OAuth", f"Connected to calendar: {calendars[0].get('summary')}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ConfigWindow()
    window.show()
    sys.exit(app.exec())