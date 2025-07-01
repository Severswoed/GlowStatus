import os
import json
import keyring
from keyring.errors import NoKeyringError
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QComboBox, QColorDialog, QCheckBox, QFrame, QSpinBox, QFormLayout, QLineEdit,
    QDialog, QTextEdit, QMessageBox, QFileDialog, QScrollArea, QListWidget, QListWidgetItem,
    QStackedWidget, QSplitter, QGroupBox, QSlider, QTabWidget, QTextBrowser
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QIcon, QFont, QPixmap, QPainter, QColor
from logger import get_logger
from utils import resource_path
from config_ui import OAuthWorker, load_config, save_config, TEMPLATE_CONFIG_PATH, CONFIG_PATH

logger = get_logger()

class SettingsWindow(QWidget):
    """Modern tabbed settings interface for GlowStatus."""
    
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(resource_path("img/GlowStatus_tray_tp_tight.png")))
        self.setWindowTitle("GlowStatus Settings")
        
        # Set window size for optimal layout
        self.setMinimumSize(900, 700)
        self.resize(1000, 750)
        
        # Track form changes for save status
        self.form_dirty = False
        self.original_values = {}
        
        self.init_ui()
        self.setup_form_change_tracking()

    def init_ui(self):
        """Initialize the tabbed user interface."""
        # Main layout
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create sidebar navigation
        self.sidebar = QListWidget()
        self.sidebar.setMaximumWidth(200)
        self.sidebar.setMinimumWidth(180)
        self.setup_sidebar()
        
        # Create content area with stacked widget
        self.content_stack = QStackedWidget()
        self.setup_content_pages()
        
        # Create splitter for resizable layout
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.content_stack)
        splitter.setSizes([200, 800])  # Default proportions
        
        main_layout.addWidget(splitter)
        
        # Add bottom bar with save status and buttons
        self.create_bottom_bar(main_layout)
        
        self.setLayout(main_layout)
        
        # Connect sidebar selection to content switching
        self.sidebar.currentRowChanged.connect(self.content_stack.setCurrentIndex)
        
        # Set default selection
        self.sidebar.setCurrentRow(0)

    def setup_sidebar(self):
        """Set up the sidebar navigation."""
        self.sidebar.setStyleSheet("""
            QListWidget {
                background-color: #f5f5f5;
                border: none;
                border-right: 1px solid #ddd;
                outline: none;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 12px 16px;
                border-bottom: 1px solid #eee;
                color: #333;
            }
            QListWidget::item:selected {
                background-color: #4285f4;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #e8f0fe;
                color: #1a73e8;
            }
            QListWidget::item:selected:hover {
                background-color: #3367d6;
                color: white;
            }
        """)
        
        # Add navigation items
        nav_items = [
            ("About", "ℹ️"),
            ("OAuth", "🔐"),
            ("Integrations", "🔗"),
            ("Calendar", "📅"),
            ("Status", "💡"),
            ("Options", "⚙️"),
            ("Accessibility", "♿")
        ]
        
        for title, icon in nav_items:
            item = QListWidgetItem(f"{icon}  {title}")
            item.setData(Qt.UserRole, title.lower())
            self.sidebar.addItem(item)

    def setup_content_pages(self):
        """Set up all content pages."""
        # Create pages
        self.about_page = self.create_about_page()
        self.oauth_page = self.create_oauth_page()
        self.integrations_page = self.create_integrations_page()
        self.calendar_page = self.create_calendar_page()
        self.status_page = self.create_status_page()
        self.options_page = self.create_options_page()
        self.accessibility_page = self.create_accessibility_page()
        
        # Add pages to stack
        self.content_stack.addWidget(self.about_page)
        self.content_stack.addWidget(self.oauth_page)
        self.content_stack.addWidget(self.integrations_page)
        self.content_stack.addWidget(self.calendar_page)
        self.content_stack.addWidget(self.status_page)
        self.content_stack.addWidget(self.options_page)
        self.content_stack.addWidget(self.accessibility_page)

    def create_scrollable_page(self, title):
        """Create a scrollable page with title."""
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px; color: #1a73e8;")
        layout.addWidget(title_label)
        
        # Scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        return page, content_layout

    def create_about_page(self):
        """Create the About page."""
        page, layout = self.create_scrollable_page("About GlowStatus")
        
        # Logo and basic info
        logo_label = QLabel()
        logo_path = resource_path("img/GlowStatus.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)
        
        # Version and description
        version_label = QLabel("Version 1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px 0;")
        layout.addWidget(version_label)
        
        description = QTextBrowser()
        description.setMaximumHeight(200)
        description.setHtml("""
        <p><strong>GlowStatus</strong> is a smart status light controller that automatically adjusts your lights based on your calendar status.</p>
        
        <p><strong>Features:</strong></p>
        <ul>
        <li>🔗 Google Calendar integration</li>
        <li>💡 Govee smart light control</li>
        <li>🎨 Customizable status colors</li>
        <li>⚙️ Flexible configuration options</li>
        <li>🔒 Secure credential storage</li>
        </ul>
        
        <p>Perfect for remote workers, streamers, and anyone who wants to visually communicate their availability.</p>
        """)
        layout.addWidget(description)
        
        # Links section
        links_group = QGroupBox("Links & Support")
        links_layout = QVBoxLayout(links_group)
        
        link_style = "color: #1a73e8; text-decoration: underline; margin: 5px 0;"
        
        website_link = QLabel('<a href="https://www.glowstatus.app">Official Website</a>')
        website_link.setStyleSheet(link_style)
        website_link.setOpenExternalLinks(True)
        links_layout.addWidget(website_link)
        
        privacy_link = QLabel('<a href="https://www.glowstatus.app/privacy">Privacy Policy</a>')
        privacy_link.setStyleSheet(link_style)
        privacy_link.setOpenExternalLinks(True)
        links_layout.addWidget(privacy_link)
        
        terms_link = QLabel('<a href="https://www.glowstatus.app/terms">Terms of Service</a>')
        terms_link.setStyleSheet(link_style)
        terms_link.setOpenExternalLinks(True)
        links_layout.addWidget(terms_link)
        
        layout.addWidget(links_group)
        layout.addStretch()
        
        return page

    def create_oauth_page(self):
        """Create the OAuth/Authentication page."""
        page, layout = self.create_scrollable_page("OAuth & Authentication")
        
        # Google OAuth Section
        google_group = QGroupBox("Google Account")
        google_layout = QFormLayout(google_group)
        
        # OAuth Status
        self.oauth_status_label = QLabel("Not configured")
        google_layout.addRow("Status:", self.oauth_status_label)
        
        # User info
        self.google_user_label = QLabel("Not authenticated")
        google_layout.addRow("Authenticated as:", self.google_user_label)
        
        # OAuth buttons
        oauth_buttons = QHBoxLayout()
        
        self.oauth_btn = QPushButton("Sign in with Google")
        self.oauth_btn.clicked.connect(self.run_oauth_flow)
        self.apply_google_button_style(self.oauth_btn)
        oauth_buttons.addWidget(self.oauth_btn)
        
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self.disconnect_oauth)
        self.disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dadce0;
                border-radius: 4px;
                color: #3c4043;
                font-size: 14px;
                font-weight: 500;
                padding: 8px 16px;
                min-height: 20px;
            }
            QPushButton:hover { background-color: #f1f3f4; }
            QPushButton:pressed { background-color: #e8eaed; }
            QPushButton:disabled { background-color: #f8f9fa; color: #9aa0a6; }
        """)
        oauth_buttons.addWidget(self.disconnect_btn)
        oauth_buttons.addStretch()
        
        google_layout.addRow("Actions:", oauth_buttons)
        
        # Privacy notice
        privacy_notice = QLabel(
            'By connecting your Google account, you agree to GlowStatus accessing your calendar data '
            'in read-only mode to determine your meeting status.'
        )
        privacy_notice.setWordWrap(True)
        privacy_notice.setStyleSheet("color: #666; font-size: 11px; margin: 10px 0; padding: 8px; "
                                   "background-color: #f8f9fa; border-radius: 4px;")
        google_layout.addRow(privacy_notice)
        
        layout.addWidget(google_group)
        
        # Update OAuth status
        self.update_oauth_status()
        
        layout.addStretch()
        return page

    def create_integrations_page(self):
        """Create the Integrations page for third-party services."""
        page, layout = self.create_scrollable_page("Integrations")
        
        # Govee Integration
        govee_group = QGroupBox("Govee Smart Lights")
        govee_layout = QFormLayout(govee_group)
        
        # API Key (secure)
        self.govee_api_key_edit = QLineEdit()
        try:
            api_key = keyring.get_password("GlowStatus", "GOVEE_API_KEY")
            self.govee_api_key_edit.setText(api_key if api_key else "")
        except NoKeyringError:
            logger.error("No secure keyring backend available")
            
        self.govee_api_key_edit.setPlaceholderText("Enter your Govee API key")
        self.govee_api_key_edit.setEchoMode(QLineEdit.Password)
        govee_layout.addRow("API Key:", self.govee_api_key_edit)
        
        # Device ID
        config = load_config()
        self.govee_device_id_edit = QLineEdit()
        self.govee_device_id_edit.setText(config.get("GOVEE_DEVICE_ID", ""))
        self.govee_device_id_edit.setPlaceholderText("Enter device ID (e.g., AA:BB:CC:DD:EE:FF:GG:HH)")
        govee_layout.addRow("Device ID:", self.govee_device_id_edit)
        
        # Device Model
        self.govee_device_model_edit = QLineEdit()
        self.govee_device_model_edit.setText(config.get("GOVEE_DEVICE_MODEL", ""))
        self.govee_device_model_edit.setPlaceholderText("Enter device model (e.g., H6159)")
        govee_layout.addRow("Device Model:", self.govee_device_model_edit)
        
        # Setup instructions
        instructions = QTextBrowser()
        instructions.setMaximumHeight(150)
        instructions.setHtml("""
        <p><strong>Setup Instructions:</strong></p>
        <ol>
        <li>Open the Govee Home app on your phone</li>
        <li>Go to Settings → About Us → Apply for API Key</li>
        <li>Follow the instructions to get your API key</li>
        <li>Find your device ID in the app settings</li>
        <li>Enter the information above and save</li>
        </ol>
        """)
        govee_layout.addRow("Setup Help:", instructions)
        
        layout.addWidget(govee_group)
        
        # Future integrations placeholder
        future_group = QGroupBox("Future Integrations")
        future_layout = QVBoxLayout(future_group)
        
        future_label = QLabel("Coming soon: Support for Philips Hue, LIFX, and other smart light brands!")
        future_label.setStyleSheet("color: #666; font-style: italic; padding: 20px;")
        future_label.setAlignment(Qt.AlignCenter)
        future_layout.addWidget(future_label)
        
        layout.addWidget(future_group)
        layout.addStretch()
        
        return page

    def create_calendar_page(self):
        """Create the Calendar settings page."""
        page, layout = self.create_scrollable_page("Calendar Settings")
        
        config = load_config()
        
        # Calendar Selection
        cal_group = QGroupBox("Calendar Selection")
        cal_layout = QFormLayout(cal_group)
        
        # Selected calendar dropdown
        self.selected_calendar_dropdown = QComboBox()
        self.selected_calendar_dropdown.setEditable(False)
        cal_layout.addRow("Calendar:", self.selected_calendar_dropdown)
        
        # Load calendars
        self.load_calendars()
        
        layout.addWidget(cal_group)
        
        # Sync Settings
        sync_group = QGroupBox("Sync Settings")
        sync_layout = QFormLayout(sync_group)
        
        # Refresh interval
        self.refresh_interval_spin = QSpinBox()
        self.refresh_interval_spin.setMinimum(10)
        self.refresh_interval_spin.setMaximum(3600)
        self.refresh_interval_spin.setValue(config.get("REFRESH_INTERVAL", 15))
        self.refresh_interval_spin.setSuffix(" seconds")
        sync_layout.addRow("Refresh Interval:", self.refresh_interval_spin)
        
        # Disable calendar sync
        self.disable_calendar_sync_chk = QCheckBox("Disable automatic calendar sync")
        self.disable_calendar_sync_chk.setChecked(config.get("DISABLE_CALENDAR_SYNC", False))
        sync_layout.addRow(self.disable_calendar_sync_chk)
        
        layout.addWidget(sync_group)
        
        # Manual Status Override
        manual_group = QGroupBox("Manual Status Override")
        manual_layout = QVBoxLayout(manual_group)
        
        override_label = QLabel("Temporarily override your status without changing calendar settings:")
        override_label.setWordWrap(True)
        manual_layout.addWidget(override_label)
        
        # Manual status controls
        manual_controls = QHBoxLayout()
        
        self.manual_status_combo = QComboBox()
        status_options = ["Auto (from calendar)", "In Meeting", "Focus", "Available", "Lunch", "Offline"]
        self.manual_status_combo.addItems(status_options)
        manual_controls.addWidget(QLabel("Status:"))
        manual_controls.addWidget(self.manual_status_combo)
        
        # Minutes override
        self.manual_minutes_spin = QSpinBox()
        self.manual_minutes_spin.setMinimum(1)
        self.manual_minutes_spin.setMaximum(480)  # 8 hours max
        self.manual_minutes_spin.setValue(30)
        self.manual_minutes_spin.setSuffix(" minutes")
        manual_controls.addWidget(QLabel("Duration:"))
        manual_controls.addWidget(self.manual_minutes_spin)
        
        apply_btn = QPushButton("Apply Override")
        apply_btn.clicked.connect(self.apply_manual_override)
        manual_controls.addWidget(apply_btn)
        manual_controls.addStretch()
        
        manual_layout.addLayout(manual_controls)
        layout.addWidget(manual_group)
        
        layout.addStretch()
        return page

    def create_status_page(self):
        """Create the Status/Light settings page."""
        page, layout = self.create_scrollable_page("Status & Light Control")
        
        config = load_config()
        
        # Status Color Mapping
        color_group = QGroupBox("Status Color Mapping")
        color_layout = QVBoxLayout(color_group)
        
        color_layout.addWidget(QLabel("Configure colors and power settings for each calendar status:"))
        
        # Status table
        self.status_table = QTableWidget(0, 4)
        self.status_table.setHorizontalHeaderLabels(["Status", "Color (RGB)", "Power", "Actions"])
        self.status_table.horizontalHeader().setStretchLastSection(True)
        
        # Load existing status mappings
        color_map = config.get("STATUS_COLOR_MAP", {})
        if not color_map:
            # Provide sensible defaults
            color_map = {
                "in_meeting": {"color": "255,0,0", "power_off": False},
                "focus": {"color": "0,0,255", "power_off": False},
                "available": {"color": "0,255,0", "power_off": True},
                "lunch": {"color": "0,255,0", "power_off": True},
                "offline": {"color": "128,128,128", "power_off": False}
            }
        
        for status, entry in color_map.items():
            self.add_status_row(status, entry.get("color", ""), entry.get("power_off", False))
        
        color_layout.addWidget(self.status_table)
        
        # Table controls
        table_controls = QHBoxLayout()
        
        add_btn = QPushButton("Add Status")
        add_btn.clicked.connect(lambda: self.add_status_row())
        table_controls.addWidget(add_btn)
        
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_selected_status)
        table_controls.addWidget(remove_btn)
        
        table_controls.addStretch()
        color_layout.addLayout(table_controls)
        
        layout.addWidget(color_group)
        
        # Light Control Options
        light_group = QGroupBox("Light Control Options")
        light_layout = QFormLayout(light_group)
        
        # Disable light control
        self.disable_light_control_chk = QCheckBox("Disable automatic light control")
        self.disable_light_control_chk.setChecked(config.get("DISABLE_LIGHT_CONTROL", False))
        light_layout.addRow(self.disable_light_control_chk)
        
        # Power off options
        self.power_off_available_chk = QCheckBox("Turn light off when available")
        self.power_off_available_chk.setChecked(config.get("POWER_OFF_WHEN_AVAILABLE", True))
        light_layout.addRow(self.power_off_available_chk)
        
        self.power_off_unknown_chk = QCheckBox("Turn light off for unknown status")
        self.power_off_unknown_chk.setChecked(config.get("OFF_FOR_UNKNOWN_STATUS", True))
        light_layout.addRow(self.power_off_unknown_chk)
        
        layout.addWidget(light_group)
        layout.addStretch()
        
        # Connect table double-click to color picker
        self.status_table.cellDoubleClicked.connect(self.open_color_picker)
        
        return page

    def create_options_page(self):
        """Create the general Options page."""
        page, layout = self.create_scrollable_page("Options")
        
        config = load_config()
        
        # Tray Icon Settings
        tray_group = QGroupBox("Tray Icon")
        tray_layout = QFormLayout(tray_group)
        
        self.tray_icon_dropdown = QComboBox()
        img_dir = resource_path('img')
        if os.path.exists(img_dir):
            tray_icons = [f for f in os.listdir(img_dir) if "_tray_" in f]
            self.tray_icon_dropdown.addItems(tray_icons)
            if config.get("TRAY_ICON") in tray_icons:
                self.tray_icon_dropdown.setCurrentText(config.get("TRAY_ICON"))
        
        tray_layout.addRow("Icon Style:", self.tray_icon_dropdown)
        layout.addWidget(tray_group)
        
        # Application Behavior
        behavior_group = QGroupBox("Application Behavior")
        behavior_layout = QFormLayout(behavior_group)
        
        # Start with Windows/Login
        self.startup_chk = QCheckBox("Start with Windows/Login")
        self.startup_chk.setToolTip("Automatically start GlowStatus when you log in")
        behavior_layout.addRow(self.startup_chk)
        
        # Minimize to tray
        self.minimize_to_tray_chk = QCheckBox("Minimize to system tray")
        self.minimize_to_tray_chk.setChecked(True)  # Default behavior
        self.minimize_to_tray_chk.setToolTip("Hide window when minimized instead of showing in taskbar")
        behavior_layout.addRow(self.minimize_to_tray_chk)
        
        # Close to tray
        self.close_to_tray_chk = QCheckBox("Close to tray (don't exit)")
        self.close_to_tray_chk.setChecked(True)  # Default behavior
        self.close_to_tray_chk.setToolTip("Keep running in background when settings window is closed")
        behavior_layout.addRow(self.close_to_tray_chk)
        
        layout.addWidget(behavior_group)
        
        # Notifications
        notifications_group = QGroupBox("Notifications")
        notifications_layout = QFormLayout(notifications_group)
        
        self.status_change_notifications_chk = QCheckBox("Show status change notifications")
        self.status_change_notifications_chk.setChecked(True)
        notifications_layout.addRow(self.status_change_notifications_chk)
        
        self.connection_notifications_chk = QCheckBox("Show connection status notifications")
        self.connection_notifications_chk.setChecked(False)
        notifications_layout.addRow(self.connection_notifications_chk)
        
        layout.addWidget(notifications_group)
        
        # Advanced Settings
        advanced_group = QGroupBox("Advanced")
        advanced_layout = QFormLayout(advanced_group)
        
        # Debug logging
        self.debug_logging_chk = QCheckBox("Enable debug logging")
        self.debug_logging_chk.setToolTip("Logs detailed information for troubleshooting")
        advanced_layout.addRow(self.debug_logging_chk)
        
        # Reset settings button
        reset_btn = QPushButton("Reset All Settings")
        reset_btn.clicked.connect(self.reset_all_settings)
        reset_btn.setStyleSheet("QPushButton { background-color: #ea4335; color: white; font-weight: bold; }")
        advanced_layout.addRow("Danger Zone:", reset_btn)
        
        layout.addWidget(advanced_group)
        layout.addStretch()
        
        return page

    def create_accessibility_page(self):
        """Create the Accessibility page."""
        page, layout = self.create_scrollable_page("Accessibility")
        
        # Visual Accessibility
        visual_group = QGroupBox("Visual Accessibility")
        visual_layout = QFormLayout(visual_group)
        
        # High contrast mode
        self.high_contrast_chk = QCheckBox("High contrast mode")
        self.high_contrast_chk.setToolTip("Use high contrast colors for better visibility")
        visual_layout.addRow(self.high_contrast_chk)
        
        # Large UI elements
        self.large_ui_chk = QCheckBox("Large UI elements")
        self.large_ui_chk.setToolTip("Increase size of buttons and text")
        visual_layout.addRow(self.large_ui_chk)
        
        # Flash warnings
        self.flash_warning_chk = QCheckBox("Disable color flash effects")
        self.flash_warning_chk.setToolTip("Prevent rapid color changes that may trigger photosensitive reactions")
        visual_layout.addRow(self.flash_warning_chk)
        
        layout.addWidget(visual_group)
        
        # Motor Accessibility
        motor_group = QGroupBox("Motor Accessibility")
        motor_layout = QFormLayout(motor_group)
        
        # Larger click targets
        self.large_targets_chk = QCheckBox("Larger click targets")
        self.large_targets_chk.setToolTip("Increase button and control sizes for easier interaction")
        motor_layout.addRow(self.large_targets_chk)
        
        # Reduce motion
        self.reduce_motion_chk = QCheckBox("Reduce motion and animations")
        self.reduce_motion_chk.setToolTip("Minimize UI animations and transitions")
        motor_layout.addRow(self.reduce_motion_chk)
        
        layout.addWidget(motor_group)
        
        # Cognitive Accessibility
        cognitive_group = QGroupBox("Cognitive Accessibility")
        cognitive_layout = QFormLayout(cognitive_group)
        
        # Simple mode
        self.simple_mode_chk = QCheckBox("Simple interface mode")
        self.simple_mode_chk.setToolTip("Show only essential options and features")
        cognitive_layout.addRow(self.simple_mode_chk)
        
        # Confirmation dialogs
        self.confirm_actions_chk = QCheckBox("Confirm all actions")
        self.confirm_actions_chk.setToolTip("Show confirmation dialogs for all setting changes")
        cognitive_layout.addRow(self.confirm_actions_chk)
        
        layout.addWidget(cognitive_group)
        
        # Screen Reader Support
        screen_reader_group = QGroupBox("Screen Reader Support")
        screen_reader_layout = QVBoxLayout(screen_reader_group)
        
        screen_reader_info = QLabel(
            "GlowStatus is designed to work with screen readers. All controls have "
            "appropriate labels and descriptions. If you experience any accessibility "
            "issues, please contact our support team."
        )
        screen_reader_info.setWordWrap(True)
        screen_reader_info.setStyleSheet("padding: 10px; background-color: #f8f9fa; border-radius: 4px;")
        screen_reader_layout.addWidget(screen_reader_info)
        
        layout.addWidget(screen_reader_group)
        layout.addStretch()
        
        return page

    def create_bottom_bar(self, main_layout):
        """Create the bottom bar with save status and action buttons."""
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(20, 10, 20, 15)
        
        # Save status indicator
        self.save_status_label = QLabel("Ready")
        self.save_status_label.setStyleSheet("color: #666; font-size: 12px;")
        bottom_layout.addWidget(self.save_status_label)
        
        bottom_layout.addStretch()
        
        # Action buttons
        self.save_btn = QPushButton("Save Settings")
        self.save_btn.clicked.connect(self.save_settings)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4285f4;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border: none;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover { background-color: #3367d6; }
            QPushButton:pressed { background-color: #2d5aa0; }
        """)
        bottom_layout.addWidget(self.save_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close_settings)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #f8f9fa;
                border: 1px solid #dadce0;
                color: #3c4043;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover { background-color: #f1f3f4; }
            QPushButton:pressed { background-color: #e8eaed; }
        """)
        bottom_layout.addWidget(self.close_btn)
        
        # Create a separate widget for the bottom bar and add it to main layout
        main_widget = QWidget()
        content_layout = QVBoxLayout(main_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Create the main splitter content
        splitter_widget = QWidget()
        splitter_layout = QHBoxLayout(splitter_widget)
        splitter_layout.setContentsMargins(0, 0, 0, 0)
        splitter_layout.setSpacing(0)
        
        # Create splitter for resizable layout
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.content_stack)
        splitter.setSizes([200, 800])
        
        splitter_layout.addWidget(splitter)
        content_layout.addWidget(splitter_widget)
        content_layout.addWidget(bottom_widget)
        
        # Set the main widget as the layout
        main_layout.addWidget(main_widget)

    # === OAUTH METHODS (adapted from original config_ui.py) ===
    
    def apply_google_button_style(self, button):
        """Apply Google branding guidelines styling to OAuth button."""
        google_logo_path = resource_path('img/google_logo.png')
        
        if os.path.exists(google_logo_path):
            icon = QIcon(google_logo_path)
            button.setIcon(icon)
            size = button.fontMetrics().height()
            button.setIconSize(QSize(size, size))
        else:
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
            QPushButton:hover { background-color: #3367d6; }
            QPushButton:pressed { background-color: #2d5aa0; }
            QPushButton:disabled { background-color: #f8f9fa; color: #5f6368; }
        """)
    
    def create_google_g_icon(self, button):
        """Create a simple Google 'G' icon as fallback."""
        size = button.fontMetrics().height()
        pixmap = QPixmap(size, size)
        pixmap.fill(QColor(255, 255, 255, 0))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(QColor(220, 220, 220))
        painter.drawEllipse(1, 1, size-2, size-2)
        
        font = QFont("Arial", max(8, size//2), QFont.Bold)
        painter.setFont(font)
        painter.setPen(QColor(66, 133, 244))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "G")
        painter.end()
        
        icon = QIcon(pixmap)
        button.setIcon(icon)
        button.setIconSize(QSize(size, size))

    def update_oauth_status(self):
        """Update OAuth status display."""
        try:
            from constants import CLIENT_SECRET_PATH, TOKEN_PATH
            
            client_secret_exists = os.path.exists(CLIENT_SECRET_PATH)
            token_exists = os.path.exists(TOKEN_PATH)
            
            if not client_secret_exists:
                self.oauth_status_label.setText("⚠ OAuth credentials not found")
                self.oauth_status_label.setStyleSheet("color: red;")
                self.oauth_btn.setEnabled(False)
                self.disconnect_btn.setEnabled(False)
                return
                
            if token_exists:
                try:
                    import pickle
                    with open(TOKEN_PATH, "rb") as token:
                        creds = pickle.load(token)
                    if creds and getattr(creds, 'valid', False):
                        self.oauth_status_label.setText("✓ Connected and authenticated")
                        self.oauth_status_label.setStyleSheet("color: green;")
                        self.disconnect_btn.setEnabled(True)
                    elif creds and getattr(creds, 'expired', False):
                        self.oauth_status_label.setText("⚠ Token expired (will auto-refresh)")
                        self.oauth_status_label.setStyleSheet("color: orange;")
                    else:
                        self.oauth_status_label.setText("⚠ Authentication required")
                        self.oauth_status_label.setStyleSheet("color: orange;")
                        self.disconnect_btn.setEnabled(False)
                except Exception as e:
                    self.oauth_status_label.setText("⚠ Not authenticated")
                    self.oauth_status_label.setStyleSheet("color: orange;")
                    self.disconnect_btn.setEnabled(False)
            else:
                self.oauth_status_label.setText("⚠ Not authenticated")
                self.oauth_status_label.setStyleSheet("color: orange;")
                self.disconnect_btn.setEnabled(False)
                
        except ImportError:
            self.oauth_status_label.setText("⚠ OAuth not available")
            self.oauth_status_label.setStyleSheet("color: red;")
            self.oauth_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(False)

    def run_oauth_flow(self):
        """Run Google OAuth authentication flow."""
        if not self.oauth_btn.isEnabled():
            return
            
        self.oauth_btn.setEnabled(False)
        self.oauth_btn.setText("Connecting...")
        self.disconnect_btn.setEnabled(False)
        
        self.google_user_label.setText("Not authenticated")
        self.selected_calendar_dropdown.clear()
        self.selected_calendar_dropdown.addItem("Loading calendars...")
        self.update_oauth_status()
        
        # Start OAuth worker thread
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
        self.google_user_label.setText(user_email)
        config = load_config()
        config["SELECTED_CALENDAR_ID"] = user_email
        save_config(config)
        
        # Update calendar dropdown
        self.selected_calendar_dropdown.clear()
        for cal in calendars:
            summary = cal.get("summary", "")
            cal_id = cal.get("id", "")
            display = f"{summary} ({cal_id})"
            self.selected_calendar_dropdown.addItem(display, cal_id)
        
        self.update_oauth_status()
        QMessageBox.information(self, "Success", f"Successfully connected to Google Calendar as {user_email}")

    def on_oauth_error(self, error_message):
        """Handle OAuth authentication errors."""
        self.google_user_label.setText("Not authenticated")
        self.selected_calendar_dropdown.clear()
        
        if "invalid_grant" in error_message.lower() or "expired" in error_message.lower():
            self.selected_calendar_dropdown.addItem("Please re-authenticate (token expired)")
        else:
            self.selected_calendar_dropdown.addItem("Please authenticate first")
            
        self.update_oauth_status()
        QMessageBox.critical(self, "Authentication Error", f"Failed to connect Google account:\n\n{error_message}")

    def on_oauth_no_calendars(self):
        """Handle case where no calendars are found."""
        self.google_user_label.setText("No calendars found")
        self.selected_calendar_dropdown.clear()
        self.selected_calendar_dropdown.addItem("No calendars found")
        self.update_oauth_status()
        QMessageBox.information(self, "Connected", "Google account connected successfully, but no calendars were found.")

    def on_oauth_finished(self):
        """Re-enable UI after OAuth flow finishes."""
        self.oauth_btn.setEnabled(True)
        self.oauth_btn.setText("Sign in with Google")
        self.disconnect_btn.setEnabled(True)
        
        if hasattr(self, 'oauth_worker'):
            self.oauth_worker.deleteLater()
            self.oauth_worker = None

    def disconnect_oauth(self):
        """Disconnect Google OAuth."""
        from constants import TOKEN_PATH
        
        reply = QMessageBox.question(
            self, 
            "Disconnect Google Account", 
            "Are you sure you want to disconnect your Google account?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if os.path.exists(TOKEN_PATH):
                    os.remove(TOKEN_PATH)
                
                config = load_config()
                config["SELECTED_CALENDAR_ID"] = ""
                save_config(config)
                
                self.google_user_label.setText("Not authenticated")
                self.selected_calendar_dropdown.clear()
                self.selected_calendar_dropdown.addItem("Please authenticate first")
                self.update_oauth_status()
                
                QMessageBox.information(self, "Disconnected", "Google account disconnected successfully.")
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to disconnect: {e}")

    def load_calendars(self):
        """Load available calendars into dropdown."""
        from constants import TOKEN_PATH
        
        self.selected_calendar_dropdown.clear()
        
        if not os.path.exists(TOKEN_PATH):
            self.selected_calendar_dropdown.addItem("Please authenticate first")
            return
        
        try:
            from calendar_sync import CalendarSync
            cal_sync = CalendarSync("primary")
            service = cal_sync._get_service()
            
            if not service:
                self.selected_calendar_dropdown.addItem("Please authenticate first")
                return
                
            calendar_list = service.calendarList().list().execute()
            calendars = calendar_list.get("items", [])
            
            if calendars:
                for cal in calendars:
                    summary = cal.get("summary", "")
                    cal_id = cal.get("id", "")
                    display = f"{summary} ({cal_id})"
                    self.selected_calendar_dropdown.addItem(display, cal_id)
                
                # Set saved calendar if available
                config = load_config()
                saved_id = config.get("SELECTED_CALENDAR_ID", "")
                if saved_id:
                    idx = self.selected_calendar_dropdown.findData(saved_id)
                    if idx != -1:
                        self.selected_calendar_dropdown.setCurrentIndex(idx)
            else:
                self.selected_calendar_dropdown.addItem("No calendars found")
                
        except Exception as e:
            self.selected_calendar_dropdown.clear()
            if "invalid_grant" in str(e).lower():
                self.selected_calendar_dropdown.addItem("Please re-authenticate (token expired)")
            else:
                self.selected_calendar_dropdown.addItem("Please authenticate first")

    # === STATUS TABLE METHODS ===
    
    def add_status_row(self, status="", color="", power_off=False):
        """Add a row to the status table."""
        row = self.status_table.rowCount()
        self.status_table.insertRow(row)
        
        # Status name
        self.status_table.setItem(row, 0, QTableWidgetItem(status))
        
        # Color display
        color_item = QTableWidgetItem(color)
        color_item.setTextAlignment(Qt.AlignCenter)
        self.status_table.setItem(row, 1, color_item)
        
        # Power checkbox
        power_chk = QCheckBox()
        power_chk.setChecked(power_off)
        self.status_table.setCellWidget(row, 2, power_chk)
        
        # Actions (color picker button)
        pick_color_btn = QPushButton("Pick Color")
        pick_color_btn.clicked.connect(lambda: self.open_color_picker(row, 1))
        self.status_table.setCellWidget(row, 3, pick_color_btn)
        
        # Center align status text
        if self.status_table.item(row, 0):
            self.status_table.item(row, 0).setTextAlignment(Qt.AlignCenter)

    def remove_selected_status(self):
        """Remove selected row from status table."""
        row = self.status_table.currentRow()
        if row >= 0:
            self.status_table.removeRow(row)
            self.on_form_changed()

    def open_color_picker(self, row, col):
        """Open color picker for status row."""
        if col == 1:  # Color column
            current = self.status_table.item(row, col)
            color_str = current.text() if current else ""
            
            # Parse current color
            try:
                if color_str:
                    rgb_values = [int(x.strip()) for x in color_str.split(",")]
                    if len(rgb_values) == 3:
                        initial_color = QColor(rgb_values[0], rgb_values[1], rgb_values[2])
                    else:
                        initial_color = QColor(255, 255, 255)
                else:
                    initial_color = QColor(255, 255, 255)
            except ValueError:
                initial_color = QColor(255, 255, 255)
            
            color = QColorDialog.getColor(initial_color, self, "Choose Status Color")
            if color.isValid():
                rgb = f"{color.red()},{color.green()},{color.blue()}"
                self.status_table.setItem(row, col, QTableWidgetItem(rgb))
                self.on_form_changed()

    # === FORM HANDLING ===
    
    def setup_form_change_tracking(self):
        """Set up form change tracking for all controls."""
        config = load_config()
        
        # Store original values
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
            'disable_calendar_sync': config.get("DISABLE_CALENDAR_SYNC", False),
            'disable_light_control': config.get("DISABLE_LIGHT_CONTROL", False),
            'power_off_available': config.get("POWER_OFF_WHEN_AVAILABLE", True),
            'power_off_unknown': config.get("OFF_FOR_UNKNOWN_STATUS", True),
            'tray_icon': config.get("TRAY_ICON", "GlowStatus_tray_tp_tight.png")
        }
        
        # Connect change signals
        if hasattr(self, 'govee_api_key_edit'):
            self.govee_api_key_edit.textChanged.connect(self.on_form_changed)
        if hasattr(self, 'govee_device_id_edit'):
            self.govee_device_id_edit.textChanged.connect(self.on_form_changed)
        if hasattr(self, 'govee_device_model_edit'):
            self.govee_device_model_edit.textChanged.connect(self.on_form_changed)
        if hasattr(self, 'selected_calendar_dropdown'):
            self.selected_calendar_dropdown.currentTextChanged.connect(self.on_form_changed)
        if hasattr(self, 'refresh_interval_spin'):
            self.refresh_interval_spin.valueChanged.connect(self.on_form_changed)
        if hasattr(self, 'disable_calendar_sync_chk'):
            self.disable_calendar_sync_chk.toggled.connect(self.on_form_changed)
        if hasattr(self, 'disable_light_control_chk'):
            self.disable_light_control_chk.toggled.connect(self.on_form_changed)
        if hasattr(self, 'power_off_available_chk'):
            self.power_off_available_chk.toggled.connect(self.on_form_changed)
        if hasattr(self, 'power_off_unknown_chk'):
            self.power_off_unknown_chk.toggled.connect(self.on_form_changed)
        if hasattr(self, 'tray_icon_dropdown'):
            self.tray_icon_dropdown.currentTextChanged.connect(self.on_form_changed)
        if hasattr(self, 'status_table'):
            self.status_table.cellChanged.connect(self.on_form_changed)
        
        self.form_dirty = False
        self.update_save_status()

    def on_form_changed(self):
        """Mark form as dirty when any field changes."""
        self.form_dirty = True
        self.update_save_status()

    def update_save_status(self):
        """Update save status indicator."""
        if self.form_dirty:
            self.save_status_label.setText("Unsaved changes")
            self.save_status_label.setStyleSheet("color: #d93025; font-size: 12px; font-weight: bold;")
        else:
            self.save_status_label.setText("All changes saved")
            self.save_status_label.setStyleSheet("color: #137333; font-size: 12px;")

    def apply_manual_override(self):
        """Apply manual status override."""
        status = self.manual_status_combo.currentText()
        duration = self.manual_minutes_spin.value()
        
        if status == "Auto (from calendar)":
            # Clear any existing override
            QMessageBox.information(self, "Override Cleared", "Status is now automatic based on calendar.")
        else:
            QMessageBox.information(
                self, 
                "Status Override Applied", 
                f"Status set to '{status}' for {duration} minutes.\n"
                f"It will automatically return to calendar-based status afterward."
            )

    def reset_all_settings(self):
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset All Settings",
            "Are you sure you want to reset ALL settings to their default values?\n\n"
            "This will:\n"
            "• Clear all integration credentials\n"
            "• Reset all preferences\n"
            "• Disconnect OAuth connections\n"
            "• Remove custom status mappings\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Remove config file
                if os.path.exists(CONFIG_PATH):
                    os.remove(CONFIG_PATH)
                
                # Clear keyring credentials
                try:
                    keyring.delete_password("GlowStatus", "GOVEE_API_KEY")
                except:
                    pass
                
                # Remove OAuth token
                try:
                    from constants import TOKEN_PATH
                    if os.path.exists(TOKEN_PATH):
                        os.remove(TOKEN_PATH)
                except:
                    pass
                
                QMessageBox.information(
                    self, 
                    "Settings Reset", 
                    "All settings have been reset to defaults.\n"
                    "Please restart GlowStatus for changes to take effect."
                )
                
                # Close the settings window
                self.close()
                
            except Exception as e:
                QMessageBox.critical(self, "Reset Failed", f"Failed to reset settings: {e}")

    def save_settings(self):
        """Save all settings."""
        try:
            config = load_config()
            
            # Save Govee settings
            if hasattr(self, 'govee_api_key_edit'):
                api_key = self.govee_api_key_edit.text().strip()
                if api_key:
                    try:
                        keyring.set_password("GlowStatus", "GOVEE_API_KEY", api_key)
                    except Exception as e:
                        logger.error(f"Failed to save API key to keyring: {e}")
                        QMessageBox.warning(self, "Keyring Error", f"Failed to save API key securely: {e}")
                else:
                    try:
                        keyring.delete_password("GlowStatus", "GOVEE_API_KEY")
                    except:
                        pass
            
            if hasattr(self, 'govee_device_id_edit'):
                config["GOVEE_DEVICE_ID"] = self.govee_device_id_edit.text().strip()
            if hasattr(self, 'govee_device_model_edit'):
                config["GOVEE_DEVICE_MODEL"] = self.govee_device_model_edit.text().strip()
            
            # Save calendar settings
            if hasattr(self, 'selected_calendar_dropdown'):
                calendar_data = self.selected_calendar_dropdown.currentData()
                config["SELECTED_CALENDAR_ID"] = calendar_data if calendar_data else ""
            if hasattr(self, 'refresh_interval_spin'):
                config["REFRESH_INTERVAL"] = self.refresh_interval_spin.value()
            if hasattr(self, 'disable_calendar_sync_chk'):
                config["DISABLE_CALENDAR_SYNC"] = self.disable_calendar_sync_chk.isChecked()
            
            # Save light control settings
            if hasattr(self, 'disable_light_control_chk'):
                config["DISABLE_LIGHT_CONTROL"] = self.disable_light_control_chk.isChecked()
            if hasattr(self, 'power_off_available_chk'):
                config["POWER_OFF_WHEN_AVAILABLE"] = self.power_off_available_chk.isChecked()
            if hasattr(self, 'power_off_unknown_chk'):
                config["OFF_FOR_UNKNOWN_STATUS"] = self.power_off_unknown_chk.isChecked()
            
            # Save tray icon
            if hasattr(self, 'tray_icon_dropdown'):
                config["TRAY_ICON"] = self.tray_icon_dropdown.currentText()
            
            # Save status color mappings
            if hasattr(self, 'status_table'):
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
            
            # Save config
            save_config(config)
            
            # Update form status
            self.form_dirty = False
            self.update_save_status()
            
            QMessageBox.information(self, "Settings Saved", "All settings have been saved successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save settings: {e}")

    def close_settings(self):
        """Close settings window with unsaved changes check."""
        if self.form_dirty:
            reply = QMessageBox.question(
                self, 
                "Unsaved Changes", 
                "You have unsaved changes. Do you want to save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                self.save_settings()
                self.close()
            elif reply == QMessageBox.Discard:
                self.close()
            # Cancel: do nothing
        else:
            self.close()

    def closeEvent(self, event):
        """Handle window close event."""
        if self.form_dirty:
            reply = QMessageBox.question(
                self, 
                "Unsaved Changes", 
                "You have unsaved changes. Do you want to save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                self.save_settings()
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
