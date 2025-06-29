import os
import json
import keyring
from keyring.errors import NoKeyringError
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QComboBox, QHBoxLayout, QColorDialog, QCheckBox, QFrame, QSpinBox, QFormLayout, QLineEdit,
    QDialog, QTextEdit, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from logger import get_logger
from utils import resource_path

# Separate paths for template config (read-only) and user config (writable)
TEMPLATE_CONFIG_PATH = resource_path('config/glowstatus_config.json')

# User config goes to a writable location
import os
import sys
if hasattr(sys, '_MEIPASS'):
    # PyInstaller bundle - use user's app data directory
    if os.name == 'nt':  # Windows
        USER_CONFIG_DIR = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'GlowStatus')
    else:  # macOS/Linux
        USER_CONFIG_DIR = os.path.expanduser('~/.config/GlowStatus')
elif getattr(sys, 'frozen', False):
    # Other bundle formats
    USER_CONFIG_DIR = os.path.expanduser('~/GlowStatus')
else:
    # Development mode - use project directory
    USER_CONFIG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ensure config directory exists
os.makedirs(USER_CONFIG_DIR, exist_ok=True)
CONFIG_PATH = os.path.join(USER_CONFIG_DIR, 'glowstatus_config.json')

logger = get_logger()

def load_config():
    # If user config doesn't exist, copy from template
    if not os.path.exists(CONFIG_PATH) and os.path.exists(TEMPLATE_CONFIG_PATH):
        try:
            import shutil
            shutil.copy2(TEMPLATE_CONFIG_PATH, CONFIG_PATH)
            logger.info(f"Created user config from template: {CONFIG_PATH}")
        except Exception as e:
            logger.warning(f"Could not copy template config: {e}")
    
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"Error reading config file: {e}")
            config = {}
    else:
        config = {}
    
    # Set sensible defaults for new configurations
    if "DISABLE_CALENDAR_SYNC" not in config:
        # Default to disabled since we'll support multiple calendar providers
        config["DISABLE_CALENDAR_SYNC"] = True
    
    if "DISABLE_LIGHT_CONTROL" not in config:
        # Default to disabled since we'll support multiple light controller brands
        config["DISABLE_LIGHT_CONTROL"] = True
    
    return config

def save_config(config):
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
        logger.info(f"Config saved to: {CONFIG_PATH}")
    except Exception as e:
        logger.error(f"Error saving config to {CONFIG_PATH}: {e}")
        # Try fallback location
        fallback_path = os.path.join(os.path.expanduser('~'), 'glowstatus_config.json')
        try:
            with open(fallback_path, "w") as f:
                json.dump(config, f, indent=2)
            logger.info(f"Config saved to fallback location: {fallback_path}")
        except Exception as fallback_error:
            logger.error(f"Failed to save config to fallback location: {fallback_error}")
            raise

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

        # Google OAuth Setup Section
        oauth_label = QLabel("Google Calendar Setup:")
        oauth_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        form_layout.addRow(oauth_label)
        
        # OAuth Status
        self.oauth_status_label = QLabel("Not configured")
        form_layout.addRow("OAuth Status:", self.oauth_status_label)
        
        # Check OAuth status and update display
        self.update_oauth_status()
        
        # Google Sign-in Button (following Google branding guidelines)
        self.oauth_btn = QPushButton("Sign in with Google")
        self.oauth_btn.clicked.connect(self.run_oauth_flow)
        
        # Apply Google branding styles
        self.apply_google_button_style(self.oauth_btn)
        form_layout.addRow(self.oauth_btn)
        
        # Disconnect Button
        self.disconnect_btn = QPushButton("Disconnect Google Account")
        self.disconnect_btn.clicked.connect(self.disconnect_oauth)
        # Style disconnect button to be less prominent
        self.disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dadce0;
                border-radius: 4px;
                color: #3c4043;
                font-family: 'Google Sans', Roboto, Arial, sans-serif;
                font-size: 14px;
                font-weight: 500;
                padding: 8px 16px;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #f1f3f4;
                border-color: #dadce0;
            }
            QPushButton:pressed {
                background-color: #e8eaed;
            }
            QPushButton:disabled {
                background-color: #f8f9fa;
                color: #9aa0a6;
                border-color: #f8f9fa;
            }
        """)
        form_layout.addRow(self.disconnect_btn)
        
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

        # Disable Light Control
        self.disable_light_chk = QCheckBox("Disable Light Control")
        self.disable_light_chk.setChecked(config.get("DISABLE_LIGHT_CONTROL", False))
        form_layout.addRow(self.disable_light_chk)

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
            self.update_oauth_status()  # Update OAuth status display
        except Exception as e:
            logger.error(f"OAuth Error: Failed to connect Google account: {e}")

    def update_oauth_status(self):
        """Update the OAuth status display based on current authentication state."""
        from constants import CLIENT_SECRET_PATH, TOKEN_PATH
        import pickle
        
        client_secret_exists = os.path.exists(CLIENT_SECRET_PATH)
        token_exists = os.path.exists(TOKEN_PATH)
        
        if not client_secret_exists:
            self.oauth_status_label.setText("⚠ OAuth credentials not found")
            self.oauth_status_label.setStyleSheet("color: red;")
            if hasattr(self, 'oauth_btn'):
                self.oauth_btn.setEnabled(False)
            if hasattr(self, 'disconnect_btn'):
                self.disconnect_btn.setEnabled(False)
            return
        
        if token_exists:
            try:
                # Try to load and check if tokens are valid
                with open(TOKEN_PATH, "rb") as token:
                    creds = pickle.load(token)
                if creds and creds.valid:
                    self.oauth_status_label.setText("✓ Connected and authenticated")
                    self.oauth_status_label.setStyleSheet("color: green;")
                    if hasattr(self, 'oauth_btn'):
                        self.oauth_btn.setText("Sign in with Google")
                    if hasattr(self, 'disconnect_btn'):
                        self.disconnect_btn.setEnabled(True)
                elif creds and creds.expired and creds.refresh_token:
                    self.oauth_status_label.setText("⚠ Token expired (will auto-refresh)")
                    self.oauth_status_label.setStyleSheet("color: orange;")
                    if hasattr(self, 'oauth_btn'):
                        self.oauth_btn.setText("Sign in with Google")
                    if hasattr(self, 'disconnect_btn'):
                        self.disconnect_btn.setEnabled(True)
                else:
                    self.oauth_status_label.setText("⚠ Authentication required")
                    self.oauth_status_label.setStyleSheet("color: orange;")
                    if hasattr(self, 'oauth_btn'):
                        self.oauth_btn.setText("Sign in with Google")
                    if hasattr(self, 'disconnect_btn'):
                        self.disconnect_btn.setEnabled(False)
            except Exception:
                self.oauth_status_label.setText("⚠ Authentication required")
                self.oauth_status_label.setStyleSheet("color: orange;")
                if hasattr(self, 'oauth_btn'):
                    self.oauth_btn.setText("Sign in with Google")
                if hasattr(self, 'disconnect_btn'):
                    self.disconnect_btn.setEnabled(False)
        else:
            self.oauth_status_label.setText("⚠ Not authenticated")
            self.oauth_status_label.setStyleSheet("color: orange;")
            if hasattr(self, 'oauth_btn'):
                self.oauth_btn.setText("Sign in with Google")
                self.oauth_btn.setEnabled(True)
            if hasattr(self, 'disconnect_btn'):
                self.disconnect_btn.setEnabled(False)

    def disconnect_oauth(self):
        """Disconnect Google OAuth by removing stored tokens."""
        from constants import TOKEN_PATH
        from PySide6.QtWidgets import QMessageBox
        
        # Confirm disconnect
        reply = QMessageBox.question(
            self, 
            "Disconnect Google Account", 
            "Are you sure you want to disconnect your Google account?\n\nYou will need to re-authenticate to use calendar features.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Remove the token file
                if os.path.exists(TOKEN_PATH):
                    os.remove(TOKEN_PATH)
                
                # Update config
                config = load_config()
                config["SELECTED_CALENDAR_ID"] = ""
                save_config(config)
                
                # Update UI
                self.google_calendar_id_label.setText("Not authenticated")
                self.selected_calendar_id_dropdown.clear()
                self.selected_calendar_id_dropdown.addItem("Please authenticate first")
                self.update_oauth_status()
                
                QMessageBox.information(self, "Disconnected", "Google account disconnected successfully.")
                logger.info("Google OAuth disconnected by user")
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to disconnect: {e}")
                logger.error(f"Failed to disconnect OAuth: {e}")
    
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
        config["DISABLE_LIGHT_CONTROL"] = self.disable_light_chk.isChecked()
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

    def apply_google_button_style(self, button):
        """Apply Google branding guidelines styling to OAuth button with logo."""
        # Try to load Google logo, fall back to text if not available
        google_logo_path = resource_path('img/google_logo.png')
        
        if os.path.exists(google_logo_path):
            # Use Google logo if available
            from PySide6.QtGui import QPixmap
            icon = QIcon(google_logo_path)
            button.setIcon(icon)
            button.setIconSize(button.fontMetrics().height(), button.fontMetrics().height())
        else:
            # Create a simple "G" logo as fallback
            self.create_google_g_icon(button)
        
        button.setStyleSheet("""
            QPushButton {
                background-color: #4285f4;
                border: none;
                border-radius: 4px;
                color: white;
                font-family: 'Google Sans', Roboto, Arial, sans-serif;
                font-size: 14px;
                font-weight: 500;
                padding: 10px 24px 10px 20px;
                min-height: 20px;
                min-width: 200px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #3367d6;
                box-shadow: 0 1px 2px 0 rgba(66, 133, 244, 0.3), 0 1px 3px 1px rgba(66, 133, 244, 0.15);
            }
            QPushButton:pressed {
                background-color: #2d5aa0;
            }
            QPushButton:disabled {
                background-color: #f8f9fa;
                color: #5f6368;
                border: 1px solid #f8f9fa;
            }
        """)
        
        # Set appropriate size policy
        from PySide6.QtWidgets import QSizePolicy
        button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
    
    def create_google_g_icon(self, button):
        """Create a simple Google 'G' icon as fallback."""
        from PySide6.QtGui import QPixmap, QPainter, QFont, QColor
        from PySide6.QtCore import QSize
        
        # Create a small pixmap for the "G" logo
        size = button.fontMetrics().height()
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(255, 255, 255, 0))  # Transparent background
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw a circle background
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(QColor(220, 220, 220))
        painter.drawEllipse(1, 1, size-2, size-2)
        
        # Draw the "G" text
        font = QFont("Arial", max(8, size//2), QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(66, 133, 244))  # Google blue
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "G")
        
        painter.end()
        
        # Set the icon
        icon = QIcon(pixmap)
        button.setIcon(icon)
        button.setIconSize(QSize(size, size))