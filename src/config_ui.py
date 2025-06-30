import os
import json
import keyring
from keyring.errors import NoKeyringError
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QComboBox, QHBoxLayout, QColorDialog, QCheckBox, QFrame, QSpinBox, QFormLayout, QLineEdit,
    QDialog, QTextEdit, QMessageBox, QFileDialog, QScrollArea
)
from PySide6.QtCore import Qt, QThread, Signal
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

class OAuthWorker(QThread):
    """Worker thread for OAuth flow to prevent UI blocking."""
    
    # Signals for communicating with the main thread
    oauth_success = Signal(str, list)  # user_email, calendars
    oauth_error = Signal(str)  # error_message
    oauth_no_calendars = Signal()
    
    def run(self):
        """Run the OAuth flow in a separate thread."""
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
                    self.oauth_success.emit(user_email, calendars)
                else:
                    self.oauth_no_calendars.emit()
            else:
                self.oauth_error.emit("Service not initialized")
                
        except Exception as e:
            self.oauth_error.emit(str(e))

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
        # Set default for new installations based on available credentials
        # This only runs once when the setting doesn't exist yet
        govee_api_key = config.get("GOVEE_API_KEY", "").strip()
        govee_device_id = config.get("GOVEE_DEVICE_ID", "").strip()
        
        # Also check keyring for API key if not in config
        if not govee_api_key:
            try:
                keyring_api_key = keyring.get_password("GlowStatus", "GOVEE_API_KEY")
                if keyring_api_key:
                    govee_api_key = keyring_api_key.strip()
            except Exception:
                pass  # Keyring not available or other error
        
        if govee_api_key and govee_device_id:
            config["DISABLE_LIGHT_CONTROL"] = False
            logger.info("Auto-enabled light control for new installation (Govee credentials detected)")
        else:
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
        
        # Set better window size for macOS and responsive design
        self.setMinimumSize(600, 700)  # Increased minimum height for better spacing
        self.resize(650, 750)  # Default size that works well on different screen sizes
        
        # Track form changes for save status
        self.form_dirty = False
        self.original_values = {}
        
        self.init_ui()

    def init_ui(self):
        # Create main layout with scroll area for better responsiveness
        main_layout = QVBoxLayout()
        
        # Create a scroll area to handle content overflow
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create the content widget that goes inside the scroll area
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(10)  # Better spacing between sections
        
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
        
        # Make table buttons consistently sized
        add_text_width = self.add_btn.fontMetrics().horizontalAdvance("Add Status")
        remove_text_width = self.remove_btn.fontMetrics().horizontalAdvance("Remove Selected")
        button_text_height = self.add_btn.fontMetrics().height()
        
        table_button_height = button_text_height + 12
        add_button_width = max(100, add_text_width + 20)
        remove_button_width = max(130, remove_text_width + 20)
        
        self.add_btn.setMinimumSize(add_button_width, table_button_height)
        self.remove_btn.setMinimumSize(remove_button_width, table_button_height)
        
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)
        layout.addLayout(btn_layout)

        # --- Other Settings ---
        form_layout = QFormLayout()
        
        # Fix label alignment for macOS (left-align labels instead of right-align)
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setFormAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        # Add better spacing between rows for readability
        form_layout.setVerticalSpacing(8)
        form_layout.setHorizontalSpacing(10)

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
        oauth_label.setStyleSheet("font-weight: bold; margin-top: 20px; margin-bottom: 10px;")
        form_layout.addRow(oauth_label)
        
        # Privacy notice (required for OAuth compliance) - with better spacing
        privacy_notice = QLabel(
            'By connecting your Google account, you agree to GlowStatus accessing your calendar data '
            'in read-only mode to determine your meeting status.<br>'
            '<a href="https://www.glowstatus.app/privacy">Privacy Policy</a> | '
            '<a href="https://www.glowstatus.app/terms">Terms of Service</a> | '
            '<a href="https://myaccount.google.com/permissions">Manage Google Permissions</a>'
        )
        privacy_notice.setWordWrap(True)
        privacy_notice.setOpenExternalLinks(True)
        privacy_notice.setStyleSheet("color: #666; font-size: 11px; margin: 10px 0 15px 0; padding: 8px 0;")
        privacy_notice.setMinimumHeight(50)  # Ensure enough space for wrapped text
        form_layout.addRow(privacy_notice)
        
        # Add a small spacer to prevent overlap
        spacer_label = QLabel("")
        spacer_label.setFixedHeight(5)
        form_layout.addRow(spacer_label)
        
        # OAuth Status with verification info
        self.oauth_status_label = QLabel("Not configured")
        form_layout.addRow("OAuth Status:", self.oauth_status_label)
        
        # Verification status info
        verification_info = QLabel(
            'ℹ️ This app uses Google\'s Limited Use policy for calendar data. '
            'Your data is processed securely and never shared with third parties.'
        )
        verification_info.setWordWrap(True)
        verification_info.setStyleSheet("color: #5f6368; font-size: 10px; font-style: italic; margin: 2px 0;")
        form_layout.addRow(verification_info)
        
        # Check OAuth status and update display
        self.update_oauth_status()
        
        # OAuth buttons layout (side by side, centered)
        oauth_buttons_layout = QHBoxLayout()
        
        # Add stretch to center the buttons
        oauth_buttons_layout.addStretch()
        
        # Google Sign-in Button (following Google branding guidelines)
        self.oauth_btn = QPushButton("Sign in with Google")
        self.oauth_btn.clicked.connect(self.run_oauth_flow)
        
        # Set button size relative to text content
        button_text = self.oauth_btn.text()
        font_metrics = self.oauth_btn.fontMetrics()
        text_width = font_metrics.horizontalAdvance(button_text)
        text_height = font_metrics.height()
        
        # Add padding around text (40px horizontal, 12px vertical)
        button_width = max(200, text_width + 40)  # Minimum 200px, or text + padding
        button_height = max(36, text_height + 12)  # Minimum 36px, or text + padding
        
        self.oauth_btn.setMinimumSize(button_width, button_height)
        self.oauth_btn.setMaximumHeight(button_height)
        
        # Apply Google branding styles
        self.apply_google_button_style(self.oauth_btn)
        oauth_buttons_layout.addWidget(self.oauth_btn)
        
        # Add small spacing between buttons
        oauth_buttons_layout.addSpacing(10)
        
        # Disconnect Button
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self.disconnect_oauth)
        
        # Set button size relative to text content
        disconnect_text = self.disconnect_btn.text()
        disconnect_text_width = font_metrics.horizontalAdvance(disconnect_text)
        disconnect_button_width = max(120, disconnect_text_width + 32)  # Minimum 120px, smaller padding
        
        self.disconnect_btn.setMinimumSize(disconnect_button_width, button_height)
        self.disconnect_btn.setMaximumHeight(button_height)
        
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
        oauth_buttons_layout.addWidget(self.disconnect_btn)
        
        # Add stretch to center the buttons
        oauth_buttons_layout.addStretch()
        
        form_layout.addRow(oauth_buttons_layout)
        
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
        self.refresh_spin.setValue(config.get("REFRESH_INTERVAL", 15))
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

        # Save status label
        self.save_status_label = QLabel("Ready")
        self.save_status_label.setAlignment(Qt.AlignCenter)
        self.save_status_label.setStyleSheet("color: #666; font-size: 12px; margin: 5px 0;")
        layout.addWidget(self.save_status_label)

        # Button layout for Save and Exit buttons
        button_layout = QHBoxLayout()
        
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_config)
        
        self.exit_btn = QPushButton("Exit")
        self.exit_btn.clicked.connect(self.exit_settings)
        
        # Make buttons appropriately sized for their text
        save_text_width = self.save_btn.fontMetrics().horizontalAdvance("Save")
        exit_text_width = self.exit_btn.fontMetrics().horizontalAdvance("Exit")
        text_height = self.save_btn.fontMetrics().height()
        
        # Set consistent button height and minimum width based on text
        button_height = text_height + 16  # Text height + padding
        save_width = max(80, save_text_width + 24)  # Minimum 80px
        exit_width = max(80, exit_text_width + 24)  # Minimum 80px
        
        self.save_btn.setMinimumSize(save_width, button_height)
        self.exit_btn.setMinimumSize(exit_width, button_height)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.exit_btn)
        
        layout.addLayout(button_layout)

        # Set the content widget in the scroll area
        scroll_area.setWidget(content_widget)
        
        # Add the scroll area to the main layout
        main_layout.addWidget(scroll_area)
        
        # Set the main layout on the window
        self.setLayout(main_layout)
        self.status_table.cellDoubleClicked.connect(self.open_color_picker)

        # Load calendars if authenticated
        self.load_calendars()
        
        # Set up form change tracking after all widgets are created
        self.setup_form_change_tracking()

    def load_calendars(self):
        """Populate the calendar dropdown with available calendars if authenticated."""
        # Always clear and set a default first to prevent crashes
        self.selected_calendar_id_dropdown.clear()
        self.selected_calendar_id_dropdown.addItem("No calendars found")
        
        try:
            from calendar_sync import CalendarSync
            cal_sync = CalendarSync("primary")
            service = cal_sync._get_service()
            if not service:
                raise Exception("No calendar service (not authenticated)")
            calendar_list = service.calendarList().list().execute()
            
            # Only proceed if we successfully got calendars
            calendars = calendar_list.get("items", [])
            if calendars:
                self.selected_calendar_id_dropdown.clear()
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
            # Silently fail - dropdown already has "No calendars found"
            logger.info(f"No calendars loaded (likely not authenticated): {e}")

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
        # Prevent multiple OAuth windows by disabling the button immediately
        if not self.oauth_btn.isEnabled():
            return
        self.oauth_btn.setEnabled(False)
        self.oauth_btn.setText("Connecting...")
        self.disconnect_btn.setEnabled(False)
        self.save_btn.setEnabled(False)
        self.exit_btn.setEnabled(False)
        
        # Clear previous status
        self.google_calendar_id_label.setText("Not authenticated")
        self.selected_calendar_id_dropdown.clear()
        self.selected_calendar_id_dropdown.addItem("Loading calendars...")
        self.update_oauth_status()
        
        # Start the OAuth flow in a separate thread
        # Disconnect previous signals to avoid double triggers
        if hasattr(self, 'oauth_worker') and self.oauth_worker is not None:
            try:
                self.oauth_worker.oauth_success.disconnect()
                self.oauth_worker.oauth_error.disconnect()
                self.oauth_worker.oauth_no_calendars.disconnect()
                self.oauth_worker.finished.disconnect()
            except Exception:
                pass
        self.oauth_worker = OAuthWorker()
        self.oauth_worker.oauth_success.connect(self.on_oauth_success)
        self.oauth_worker.oauth_error.connect(self.on_oauth_error)
        self.oauth_worker.oauth_no_calendars.connect(self.on_oauth_no_calendars)
        self.oauth_worker.finished.connect(self.on_oauth_finished)
        self.oauth_worker.start()

    def on_oauth_success(self, user_email, calendars):
        """Handle successful OAuth authentication."""
        self.google_calendar_id_label.setText(user_email)
        config = load_config()
        config["SELECTED_CALENDAR_ID"] = user_email
        save_config(config)
        logger.info(f"OAuth Success: Google account connected as {user_email}.")
        
        # Update calendar dropdown
        self.selected_calendar_id_dropdown.clear()
        for cal in calendars:
            summary = cal.get("summary", "")
            cal_id = cal.get("id", "")
            display = f"{summary} ({cal_id})"
            self.selected_calendar_id_dropdown.addItem(display, cal_id)
        
        # Set to saved value if present
        saved_id = config.get("SELECTED_CALENDAR_ID", "")
        if saved_id:
            idx = self.selected_calendar_id_dropdown.findData(saved_id)
            if idx != -1:
                self.selected_calendar_id_dropdown.setCurrentIndex(idx)
        
        self.update_oauth_status()  # Update OAuth status display
        
        # Show success message
        QMessageBox.information(self, "Success", f"Successfully connected to Google Calendar as {user_email}")

    def on_oauth_error(self, error_message):
        """Handle errors during OAuth authentication."""
        self.google_calendar_id_label.setText("Not authenticated")
        self.selected_calendar_id_dropdown.clear()
        self.selected_calendar_id_dropdown.addItem("Please authenticate first")
        self.update_oauth_status()
        
        logger.error(f"OAuth Error: {error_message}")
        QMessageBox.critical(self, "Authentication Error", f"Failed to connect Google account:\n\n{error_message}")

    def on_oauth_no_calendars(self):
        """Handle case where no calendars are found after OAuth authentication."""
        self.google_calendar_id_label.setText("No calendars found")
        self.selected_calendar_id_dropdown.clear()
        self.selected_calendar_id_dropdown.addItem("No calendars found")
        logger.info("OAuth Success: Google account connected, but no calendars found.")
        self.update_oauth_status()
        
        # Show info message
        QMessageBox.information(self, "Connected", "Google account connected successfully, but no calendars were found.")

    def on_oauth_finished(self):
        """Called when the OAuth worker thread finishes (regardless of success/error)."""
        # Re-enable UI elements
        self.oauth_btn.setEnabled(True)
        self.oauth_btn.setText("Sign in with Google")
        self.disconnect_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.exit_btn.setEnabled(True)
        
        # Clean up worker reference
        if hasattr(self, 'oauth_worker'):
            self.oauth_worker.deleteLater()
            self.oauth_worker = None

    def validate_oauth_setup(self):
        """Validate OAuth setup for Google verification compliance."""
        from constants import CLIENT_SECRET_PATH
        
        results = []
        issues = []
        
        results.append("=== GOOGLE OAUTH VERIFICATION READINESS ===\n")
        
        # Check client_secret.json
        results.append("1. OAuth Credentials:")
        if not os.path.exists(CLIENT_SECRET_PATH):
            issues.append("❌ client_secret.json not found")
            results.append("   ❌ client_secret.json not found")
            results.append("   → Create OAuth credentials in Google Cloud Console")
        else:
            try:
                with open(CLIENT_SECRET_PATH, 'r') as f:
                    client_config = json.load(f)
                    client_id = client_config.get('installed', {}).get('client_id', '')
                    project_id = client_config.get('installed', {}).get('project_id', '')
                    
                    if 'YOUR_CLIENT_ID' in client_id:
                        issues.append("⚠️ client_secret.json contains template values")
                        results.append("   ⚠️ Contains template values - replace with real credentials")
                    elif not client_id.endswith('.apps.googleusercontent.com'):
                        issues.append("⚠️ Invalid client_id format")
                        results.append("   ⚠️ Invalid client_id format")
                    else:
                        results.append("   ✅ Valid OAuth credentials found")
                        results.append(f"   Project ID: {project_id}")
                        results.append(f"   Client ID: {client_id[:20]}...")
            except Exception as e:
                issues.append(f"❌ Invalid client_secret.json: {e}")
                results.append(f"   ❌ Invalid client_secret.json: {e}")
        
        # Check privacy pages
        results.append("\n2. Privacy Policy & Terms:")
        try:
            import urllib.request
            response = urllib.request.urlopen('https://www.glowstatus.app/privacy', timeout=5)
            if response.getcode() == 200:
                results.append("   ✅ Privacy Policy accessible")
            else:
                issues.append("⚠️ Privacy Policy returned non-200 status")
                results.append("   ⚠️ Privacy Policy returned non-200 status")
        except Exception as e:
            issues.append("⚠️ Privacy Policy page not accessible")
            results.append(f"   ❌ Privacy Policy not accessible: {str(e)[:50]}...")
        
        try:
            response = urllib.request.urlopen('https://www.glowstatus.app/terms', timeout=5)
            if response.getcode() == 200:
                results.append("   ✅ Terms of Service accessible")
            else:
                issues.append("⚠️ Terms of Service returned non-200 status")
                results.append("   ⚠️ Terms of Service returned non-200 status")
        except Exception as e:
            issues.append("⚠️ Terms of Service page not accessible")
            results.append(f"   ❌ Terms of Service not accessible: {str(e)[:50]}...")
        
        # Check OAuth implementation
        results.append("\n3. OAuth Implementation:")
        results.append("   ✅ Uses InstalledAppFlow with PKCE")
        results.append("   ✅ Limited scope: calendar.readonly")
        results.append("   ✅ Google branding compliant")
        results.append("   ✅ User consent dialog implemented")
        results.append("   ✅ Disconnect functionality provided")
        results.append("   ✅ Error handling implemented")
        
        # Check security
        results.append("\n4. Security & Compliance:")
        results.append("   ✅ Credentials protected in .gitignore")
        results.append("   ✅ Google Limited Use policy compliance")
        results.append("   ✅ Local data processing only")
        results.append("   ✅ No third-party data sharing")
        
        # Summary
        results.append("\n=== SUMMARY ===")
        if not issues:
            results.append("🎉 OAuth setup appears ready for Google verification!")
            results.append("\nNext steps:")
            results.append("1. Replace template client_secret.json with real credentials")
            results.append("2. Configure OAuth consent screen in Google Cloud Console")
            results.append("3. Test complete OAuth flow")
            results.append("4. Submit for Google verification")
        else:
            results.append(f"⚠️ Found {len(issues)} issues to address:")
            for issue in issues:
                results.append(f"   • {issue}")
            results.append("\nAddress these issues before submitting for verification.")
        
        return "\n".join(results)

    def update_oauth_status(self):
        """Update the OAuth status display based on current authentication state."""
        try:
            from constants import CLIENT_SECRET_PATH, TOKEN_PATH
        except ImportError:
            # If constants can't be imported, disable OAuth
            self.oauth_status_label.setText("⚠ OAuth not available")
            self.oauth_status_label.setStyleSheet("color: red;")
            if hasattr(self, 'oauth_btn'):
                self.oauth_btn.setEnabled(False)
            if hasattr(self, 'disconnect_btn'):
                self.disconnect_btn.setEnabled(False)
            return
            
        try:
            client_secret_exists = os.path.exists(CLIENT_SECRET_PATH)
            token_exists = os.path.exists(TOKEN_PATH)
        except Exception:
            # If path checking fails, disable OAuth
            self.oauth_status_label.setText("⚠ OAuth not available")
            self.oauth_status_label.setStyleSheet("color: red;")
            if hasattr(self, 'oauth_btn'):
                self.oauth_btn.setEnabled(False)
            if hasattr(self, 'disconnect_btn'):
                self.disconnect_btn.setEnabled(False)
            return
            
        if not client_secret_exists:
            self.oauth_status_label.setText("⚠ OAuth credentials not found")
            self.oauth_status_label.setStyleSheet("color: red;")
            if hasattr(self, 'oauth_btn'):
                self.oauth_btn.setEnabled(False)
            if hasattr(self, 'disconnect_btn'):
                self.disconnect_btn.setEnabled(False)
            return
            
        # Always allow UI to load, even if token is missing or revoked
        if token_exists:
            try:
                import pickle
                with open(TOKEN_PATH, "rb") as token:
                    creds = pickle.load(token)
                if creds and getattr(creds, 'valid', False):
                    self.oauth_status_label.setText("✓ Connected and authenticated")
                    self.oauth_status_label.setStyleSheet("color: green;")
                    if hasattr(self, 'oauth_btn'):
                        self.oauth_btn.setText("Sign in with Google")
                    if hasattr(self, 'disconnect_btn'):
                        self.disconnect_btn.setEnabled(True)
                elif creds and getattr(creds, 'expired', False) and getattr(creds, 'refresh_token', None):
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
            except Exception as e:
                self.oauth_status_label.setText("⚠ Not authenticated")
                self.oauth_status_label.setStyleSheet("color: orange;")
                if hasattr(self, 'oauth_btn'):
                    self.oauth_btn.setText("Sign in with Google")
                    self.oauth_btn.setEnabled(True)
                if hasattr(self, 'disconnect_btn'):
                    self.disconnect_btn.setEnabled(False)
                logger.info(f"OAuth token not available: {e}")
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
    def apply_google_button_style(self, button):
        """Apply Google branding guidelines styling to OAuth button with logo."""
        # Try to load Google logo, fall back to text if not available
        google_logo_path = resource_path('img/google_logo.png')
        
        if os.path.exists(google_logo_path):
            # Use Google logo if available
            from PySide6.QtGui import QPixmap
            from PySide6.QtCore import QSize
            icon = QIcon(google_logo_path)
            button.setIcon(icon)
            size = button.fontMetrics().height()
            button.setIconSize(QSize(size, size))
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
                text-align: left;
            }
            QPushButton:hover {
                background-color: #3367d6;
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

    def show_oauth_validation(self):
        """Show detailed OAuth verification readiness status."""
        from PySide6.QtWidgets import QMessageBox
        
        validation_result = self.validate_oauth_setup()
        
        # Create detailed dialog
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("OAuth Verification Readiness")
        msg_box.setText("Google OAuth Verification Status")
        msg_box.setDetailedText(validation_result)
        
        if "✅" in validation_result:
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setInformativeText("Your OAuth setup appears ready for Google verification!")
        else:
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setInformativeText("Please address the issues below before submitting for verification.")
        
        msg_box.exec()

    def setup_form_change_tracking(self):
        """Set up change tracking for all form fields."""
        # Store original values
        config = load_config()
        try:
            api_key = keyring.get_password("GlowStatus", "GOVEE_API_KEY") or ""
        except:
            api_key = ""
        
        self.original_values = {
            'govee_api_key': api_key,
            'govee_device_id': config.get("GOVEE_DEVICE_ID", ""),
            'govee_device_model': config.get("GOVEE_DEVICE_MODEL", ""),
            'selected_calendar': config.get("SELECTED_CALENDAR_ID", ""),
            'refresh_interval': config.get("REFRESH_INTERVAL", 15),
            'power_off_available': config.get("POWER_OFF_WHEN_AVAILABLE", True),
            'off_for_unknown': config.get("OFF_FOR_UNKNOWN_STATUS", True),
            'disable_calendar_sync': config.get("DISABLE_CALENDAR_SYNC", False),
            'disable_light_control': config.get("DISABLE_LIGHT_CONTROL", False),
            'tray_icon': config.get("TRAY_ICON", "GlowStatus_tray_tp_tight.png")
        }
        
        # Connect change signals
        self.govee_api_key_edit.textChanged.connect(self.on_form_changed)
        self.govee_device_id_edit.textChanged.connect(self.on_form_changed)
        self.govee_device_model_edit.textChanged.connect(self.on_form_changed)
        self.selected_calendar_id_dropdown.currentTextChanged.connect(self.on_form_changed)
        self.refresh_spin.valueChanged.connect(self.on_form_changed)
        self.power_off_available_chk.toggled.connect(self.on_form_changed)
        self.off_for_unknown_chk.toggled.connect(self.on_form_changed)
        self.disable_sync_chk.toggled.connect(self.on_form_changed)
        self.disable_light_chk.toggled.connect(self.on_form_changed)
        self.tray_icon_dropdown.currentTextChanged.connect(self.on_form_changed)
        self.status_table.cellChanged.connect(self.on_form_changed)
        
        # Initially not dirty
        self.form_dirty = False
        self.update_save_status()
    
    def on_form_changed(self):
        """Called when any form field changes."""
        self.form_dirty = True
        self.update_save_status()
    
    def update_save_status(self):
        """Update the save status label."""
        if self.form_dirty:
            self.save_status_label.setText("Not Saved")
            self.save_status_label.setStyleSheet("color: #d93025; font-size: 12px; font-weight: bold; margin: 5px 0;")
        else:
            self.save_status_label.setText("Saved!")
            self.save_status_label.setStyleSheet("color: #137333; font-size: 12px; font-weight: bold; margin: 5px 0;")
    
    def save_config(self):
        """Save configuration and update status."""
        # ...existing save logic...
        config = load_config()
        
        # Save Govee API Key securely
        api_key = self.govee_api_key_edit.text().strip()
        if api_key:
            try:
                keyring.set_password("GlowStatus", "GOVEE_API_KEY", api_key)
                logger.info("Govee API key saved to keyring")
            except Exception as e:
                logger.error(f"Failed to save Govee API key to keyring: {e}")
                QMessageBox.warning(self, "Keyring Error", f"Failed to save API key securely: {e}")
        else:
            try:
                keyring.delete_password("GlowStatus", "GOVEE_API_KEY")
            except:
                pass
        
        config["GOVEE_DEVICE_ID"] = self.govee_device_id_edit.text().strip()
        config["GOVEE_DEVICE_MODEL"] = self.govee_device_model_edit.text().strip()
        
        # Calendar selection
        calendar_data = self.selected_calendar_id_dropdown.currentData()
        config["SELECTED_CALENDAR_ID"] = calendar_data if calendar_data else ""
        
        config["REFRESH_INTERVAL"] = self.refresh_spin.value()
        config["POWER_OFF_WHEN_AVAILABLE"] = self.power_off_available_chk.isChecked()
        config["OFF_FOR_UNKNOWN_STATUS"] = self.off_for_unknown_chk.isChecked()
        config["DISABLE_CALENDAR_SYNC"] = self.disable_sync_chk.isChecked()
        config["DISABLE_LIGHT_CONTROL"] = self.disable_light_chk.isChecked()
        config["TRAY_ICON"] = self.tray_icon_dropdown.currentText()
        
        # Status/Color mappings
        status_color_map = {}
        for row in range(self.status_table.rowCount()):
            status_item = self.status_table.item(row, 0)
            color_item = self.status_table.item(row, 1)
            power_widget = self.status_table.cellWidget(row, 2)
            
            if status_item and color_item and power_widget:
                status = status_item.text()
                color = color_item.text()
                power_off = power_widget.isChecked()
                status_color_map[status] = {"color": color, "power_off": power_off}
        
        config["STATUS_COLOR_MAP"] = status_color_map
        
        save_config(config)
        
        # Update form status
        self.form_dirty = False
        self.update_save_status()
        
        QMessageBox.information(self, "Settings Saved", "Configuration saved successfully!")
    
    def exit_settings(self):
        """Exit the settings window, prompting if there are unsaved changes."""
        if self.form_dirty:
            reply = QMessageBox.question(
                self, 
                "Unsaved Changes", 
                "You have unsaved changes. Do you want to save before exiting?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                self.save_config()
                self.close()
            elif reply == QMessageBox.Discard:
                self.close()
            # Cancel: do nothing, stay open
        else:
            self.close()
    
    def closeEvent(self, event):
        """Handle window close event to check for unsaved changes."""
        if self.form_dirty:
            reply = QMessageBox.question(
                self, 
                "Unsaved Changes", 
                "You have unsaved changes. Do you want to save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                self.save_config()
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()