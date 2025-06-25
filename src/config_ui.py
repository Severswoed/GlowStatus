import os
import json
import keyring
from keyring.errors import NoKeyringError
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QComboBox, QHBoxLayout, QColorDialog, QCheckBox, QFrame, QSpinBox, QFormLayout, QLineEdit
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from logger import get_logger
from utils import resource_path

CONFIG_PATH = resource_path('config/glowstatus_config.json')
logger = get_logger()

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

class ConfigWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(os.path.abspath(os.path.join(os.path.dirname(__file__), "../img/GlowStatus_tray_tp_tight.png"))))
        self.setWindowTitle("GlowStatus Settings")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Status/Color/Power Mapping:"))

        self.status_table = QTableWidget(0, 3)
        self.status_table.setHorizontalHeaderLabels(["Status", "Color (R,G,B)", "Power Off"])
        self.status_table.horizontalHeader().setStretchLastSection(True)

        config = load_config()
        color_map = config.get("STATUS_COLOR_MAP", {})
        if not color_map:
            # Provide sensible defaults if missing
            color_map = {
                "in_meeting": {"color": "255,0,0", "power_off": False},
                "focus": {"color": "0,0,255", "power_off": False},
                "available": {"color": "0,255,0", "power_off": True},
                "lunch": {"color": "0,255,0", "power_off": True},
                "offline": {"color": "128,128,128", "power_off": False},
            }
        for status, entry in color_map.items():
            self.add_status_row(status, entry.get("color", ""), entry.get("power_off", False))

        layout.addWidget(self.status_table)

        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Status")
        self.add_btn.clicked.connect(self.add_status_row)
        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self.remove_selected_row)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)
        layout.addLayout(btn_layout)

        # --- Other Settings ---
        form_layout = QFormLayout()

        # Govee API Key (securely stored in keyring)
        try:
            api_key = keyring.get_password("GlowStatus", "GOVEE_API_KEY")
        except NoKeyringError:
            logger.error("No secure keyring backend available. Please ensure your system keychain is accessible.")
            api_key = ""
        self.govee_api_key_edit = QLineEdit()
        self.govee_api_key_edit.setText(api_key if api_key else "")
        self.govee_api_key_edit.setPlaceholderText("Set in keychain for security")
        self.govee_api_key_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Govee API Key:", self.govee_api_key_edit)

        # Govee Device ID
        self.govee_device_id_edit = QLineEdit()
        self.govee_device_id_edit.setText(config.get("GOVEE_DEVICE_ID", ""))
        form_layout.addRow("Govee Device ID:", self.govee_device_id_edit)

        # Govee Device Model
        self.govee_device_model_edit = QLineEdit()
        self.govee_device_model_edit.setText(config.get("GOVEE_DEVICE_MODEL", ""))
        form_layout.addRow("Govee Device Model:", self.govee_device_model_edit)

        # OAuth Button
        self.oauth_btn = QPushButton("Connect Google Account (OAuth)")
        self.oauth_btn.clicked.connect(self.run_oauth_flow)
        form_layout.addRow(self.oauth_btn)
        
        # Google Calendar ID (display only)
        self.google_calendar_id_label = QLabel(config.get("SELECTED_CALENDAR_ID", "Not authenticated"))
        form_layout.addRow("Authenticated as:", self.google_calendar_id_label)

        # Selected Calendar ID (dropdown)
        self.selected_calendar_id_dropdown = QComboBox()
        self.selected_calendar_id_dropdown.setEditable(False)
        self.selected_calendar_id_dropdown.addItem("Loading...")  # Placeholder
        form_layout.addRow("Selected Calendar:", self.selected_calendar_id_dropdown)

        # Refresh Interval
        self.refresh_spin = QSpinBox()
        self.refresh_spin.setMinimum(10)
        self.refresh_spin.setMaximum(3600)
        self.refresh_spin.setValue(config.get("REFRESH_INTERVAL", 60))
        form_layout.addRow("Refresh Interval (seconds):", self.refresh_spin)

        # Power Off When Available
        self.power_off_available_chk = QCheckBox("Turn light off when available")
        self.power_off_available_chk.setChecked(config.get("POWER_OFF_WHEN_AVAILABLE", True))
        form_layout.addRow(self.power_off_available_chk)

        # Off For Unknown Status
        self.off_for_unknown_chk = QCheckBox("Turn light off for unknown status")
        self.off_for_unknown_chk.setChecked(config.get("OFF_FOR_UNKNOWN_STATUS", True))
        form_layout.addRow(self.off_for_unknown_chk)

        # Disable Calendar Sync
        self.disable_sync_chk = QCheckBox("Disable Calendar Sync")
        self.disable_sync_chk.setChecked(config.get("DISABLE_CALENDAR_SYNC", False))
        form_layout.addRow(self.disable_sync_chk)

        layout.addLayout(form_layout)

        # Tray Icon Picker
        line_tray = QFrame()
        line_tray.setFrameShape(QFrame.HLine)
        line_tray.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line_tray)

        img_dir = resource_path('img')
        if os.path.exists(img_dir):
            tray_icons = [f for f in os.listdir(img_dir) if "_tray_" in f]
        else:
            tray_icons = []
        self.tray_icon_dropdown = QComboBox()
        self.tray_icon_dropdown.addItems(tray_icons)
        if config.get("TRAY_ICON") in tray_icons:
            self.tray_icon_dropdown.setCurrentText(config.get("TRAY_ICON"))
        layout.addWidget(QLabel("Tray Icon:"))
        layout.addWidget(self.tray_icon_dropdown)

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_config)
        layout.addWidget(self.save_btn)

        self.setLayout(layout)
        self.status_table.cellDoubleClicked.connect(self.open_color_picker)

        # Load calendars if authenticated
        self.load_calendars()

    def load_calendars(self):
        """Populate the calendar dropdown with available calendars if authenticated."""
        try:
            from calendar_sync import CalendarSync
            cal_sync = CalendarSync("primary")
            service = cal_sync._get_service()
            calendar_list = service.calendarList().list().execute()
            self.selected_calendar_id_dropdown.clear()
            calendars = calendar_list.get("items", [])
            for cal in calendars:
                summary = cal.get("summary", "")
                cal_id = cal.get("id", "")
                display = f"{summary} ({cal_id})"
                self.selected_calendar_id_dropdown.addItem(display, cal_id)
            # Set to saved value if present
            config = load_config()
            saved_id = config.get("SELECTED_CALENDAR_ID", "")
            if saved_id:
                idx = self.selected_calendar_id_dropdown.findData(saved_id)
                if idx != -1:
                    self.selected_calendar_id_dropdown.setCurrentIndex(idx)
        except Exception as e:
            self.selected_calendar_id_dropdown.clear()
            self.selected_calendar_id_dropdown.addItem("No calendars found")
            logger.error(f"Failed to load calendars: {e}")

    def add_status_row(self, status="", color="", power_off=False):
        row = self.status_table.rowCount()
        self.status_table.insertRow(row)
        self.status_table.setItem(row, 0, QTableWidgetItem(status))
        self.status_table.setItem(row, 1, QTableWidgetItem(color))
        chk = QCheckBox()
        chk.setChecked(power_off)
        self.status_table.setCellWidget(row, 2, chk)
        self.status_table.item(row, 0).setTextAlignment(Qt.AlignCenter)
        self.status_table.item(row, 1).setTextAlignment(Qt.AlignCenter)

    def remove_selected_row(self):
        row = self.status_table.currentRow()
        if row >= 0:
            self.status_table.removeRow(row)

    def open_color_picker(self, row, col):
        if col == 1:
            current = self.status_table.item(row, col)
            color_str = current.text() if current else ""
            initial = [int(x) for x in color_str.split(",")] if color_str else [255,255,255]
            color = QColorDialog.getColor()
            if color.isValid():
                rgb = f"{color.red()},{color.green()},{color.blue()}"
                self.status_table.setItem(row, col, QTableWidgetItem(rgb))

    def run_oauth_flow(self):
        try:
            from calendar_sync import CalendarSync
            cal_sync = CalendarSync("primary")
            service = cal_sync._get_service()
            if service:
                # Fetch the user's email from the primary calendar
                calendar_list = service.calendarList().list().execute()
                calendars = calendar_list.get("items", [])
                user_email = None
                for cal in calendars:
                    if cal.get("primary"):
                        user_email = cal.get("id")
                        break
                if not user_email and calendars:
                    user_email = calendars[0].get("id", "Unknown")
                if user_email:
                    self.google_calendar_id_label.setText(user_email)
                    config = load_config()
                    config["SELECTED_CALENDAR_ID"] = user_email
                    save_config(config)
                    logger.info(f"OAuth Success: Google account connected as {user_email}.")
                else:
                    self.google_calendar_id_label.setText("No calendars found")
                    logger.info("OAuth Success: Google account connected, but no calendars found.")
            else:
                self.google_calendar_id_label.setText("Not authenticated")
                logger.info("OAuth failed: Service not initialized.")
            self.load_calendars()  # Refresh calendar list after OAuth
        except Exception as e:
            logger.error(f"OAuth Error: Failed to connect Google account: {e}")
    
    def save_config(self):
        config = load_config()
        color_map = {}
        for row in range(self.status_table.rowCount()):
            status = self.status_table.item(row, 0).text().strip().lower()
            color = self.status_table.item(row, 1).text().strip()
            power_off = self.status_table.cellWidget(row, 2).isChecked()
            if status:
                color_map[status] = {"color": color, "power_off": power_off}
        config["STATUS_COLOR_MAP"] = color_map
        config["TRAY_ICON"] = self.tray_icon_dropdown.currentText()
        config["REFRESH_INTERVAL"] = self.refresh_spin.value()
        config["POWER_OFF_WHEN_AVAILABLE"] = self.power_off_available_chk.isChecked()
        config["OFF_FOR_UNKNOWN_STATUS"] = self.off_for_unknown_chk.isChecked()
        config["DISABLE_CALENDAR_SYNC"] = self.disable_sync_chk.isChecked()
        config["GOVEE_DEVICE_ID"] = self.govee_device_id_edit.text().strip()
        config["GOVEE_DEVICE_MODEL"] = self.govee_device_model_edit.text().strip()
        # Save the selected calendar ID from the dropdown
        selected_idx = self.selected_calendar_id_dropdown.currentIndex()
        selected_id = self.selected_calendar_id_dropdown.itemData(selected_idx)
        if selected_id:
            config["SELECTED_CALENDAR_ID"] = selected_id
        else:
            config["SELECTED_CALENDAR_ID"] = self.google_calendar_id_label.text().strip()
        save_config(config)
        logger.info("Settings saved successfully.")

        # Save Govee API key securely to keyring
        api_key = self.govee_api_key_edit.text().strip()
        if api_key and api_key != "Set in environment or .env for security":
            try:
                keyring.set_password("GlowStatus", "GOVEE_API_KEY", api_key)
                logger.info("Govee API key saved to keyring.")
            except NoKeyringError:
                logger.error("No secure keyring backend available. Cannot save API key.")