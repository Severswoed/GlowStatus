import os
import json
import keyring
from keyring.errors import NoKeyringError
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, 
    QPushButton, QComboBox, QColorDialog, QCheckBox, QFrame, QSpinBox, 
    QFormLayout, QLineEdit, QDialog, QTextEdit, QMessageBox, QFileDialog, 
    QScrollArea, QListWidget, QListWidgetItem, QStackedWidget, QSplitter,
    QGroupBox, QProgressBar, QSlider, QTabWidget, QSizePolicy
)
from PySide6.QtCore import Qt, QThread, Signal, QSize, QTimer
from PySide6.QtGui import QIcon, QPixmap, QFont, QColor, QPalette
from logger import get_logger
from utils import resource_path
from constants import TOKEN_PATH, CLIENT_SECRET_PATH, SCOPES, CONFIG_PATH

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
            import pickle
            from google.auth.transport.requests import Request
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            
            # Check for client_secret.json
            if not os.path.exists(CLIENT_SECRET_PATH):
                self.oauth_error.emit("Google OAuth credentials not found. Please set up OAuth in Settings.")
                return
            
            creds = None
            # Load existing token if available
            if os.path.exists(TOKEN_PATH):
                try:
                    with open(TOKEN_PATH, "rb") as token:
                        creds = pickle.load(token)
                except Exception as token_error:
                    logger.warning(f"Failed to load token file: {token_error}")
                    creds = None
            
            # Always run OAuth flow for explicit authentication
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
                # Configure for better compatibility and cancellation handling
                try:
                    creds = flow.run_local_server(port=0, open_browser=True, host='localhost', timeout_seconds=120)
                except Exception as oauth_error:
                    if "timeout" in str(oauth_error).lower() or "cancelled" in str(oauth_error).lower():
                        self.oauth_error.emit("OAuth authentication was cancelled or timed out.")
                        return
                    else:
                        # Fallback to console flow
                        logger.warning(f"Local server OAuth failed, trying console: {oauth_error}")
                        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_PATH, SCOPES)
                        creds = flow.run_console()
                        
            except Exception as flow_error:
                self.oauth_error.emit(f"OAuth authentication failed: {str(flow_error)}")
                return
            
            if not creds:
                self.oauth_error.emit("Failed to obtain valid credentials")
                return
            
            # Save the credentials
            try:
                with open(TOKEN_PATH, "wb") as token:
                    pickle.dump(creds, token)
            except Exception as save_error:
                logger.warning(f"Failed to save credentials: {save_error}")
            
            # Test the credentials by fetching calendars
            try:
                service = build("calendar", "v3", credentials=creds)
                calendar_list = service.calendarList().list().execute()
                calendars = calendar_list.get("items", [])
                
                user_email = None
                for cal in calendars:
                    if cal.get("primary"):
                        user_email = cal.get("id")
                        break
                        
                if not user_email and calendars:
                    user_email = calendars[0].get("id", "Unknown")
                    
                if user_email and calendars:
                    self.oauth_success.emit(user_email, calendars)
                else:
                    self.oauth_no_calendars.emit()
                    
            except Exception as api_error:
                self.oauth_error.emit(f"Failed to access Google Calendar API: {str(api_error)}")
                
        except Exception as e:
            self.oauth_error.emit(f"OAuth process failed: {str(e)}")

def load_config():
    """Load configuration from file with sensible defaults."""
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
    defaults = {
        "DISABLE_CALENDAR_SYNC": False,
        "SYNC_INTERVAL": 30,
        "DEFAULT_STATUS": "Available",
        "GOVEE_DEVICE_ID": "",
        "STATUS_COLORS": {
            "Available": "#00FF00",
            "Busy": "#FF0000",
            "Away": "#FFFF00",
            "Do Not Disturb": "#800080",
            "Offline": "#808080",
            "Meeting": "#FF4500",
            "Presenting": "#FF69B4",
            "Tentative": "#FFA500",
            "Out of Office": "#000080"
        }
    }
    
    for key, value in defaults.items():
        if key not in config:
            config[key] = value
    
    return config

def save_config(config):
    """Save configuration to file."""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
        logger.info(f"Configuration saved to {CONFIG_PATH}")
    except Exception as e:
        logger.error(f"Error saving config file: {e}")

class SettingsWindow(QDialog):
    """Modern settings window for GlowStatus with tabbed interface."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = load_config()
        self.oauth_worker = None
        self.setup_ui()
        self.load_settings()
        
    def setup_ui(self):
        """Set up the main UI."""
        self.setWindowTitle("GlowStatus Settings")
        self.setMinimumSize(900, 700)
        self.resize(1000, 800)
        
        # Try to set window icon
        try:
            icon_path = resource_path("img/GlowStatus.png")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass
        
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create splitter for resizable layout
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left sidebar
        self.setup_sidebar()
        splitter.addWidget(self.sidebar)
        
        # Right content area
        self.setup_content_area()
        splitter.addWidget(self.content_area)
        
        # Set splitter proportions
        splitter.setSizes([250, 750])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)
        
        # Apply GlowStatus theme
        self.apply_theme()
        
    def setup_sidebar(self):
        """Set up the navigation sidebar."""
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(250)
        self.sidebar.setObjectName("sidebar")
        
        # Connect selection change
        self.sidebar.currentRowChanged.connect(self.change_page)
        
        # Add navigation items
        nav_items = [
            ("About", "ℹ️"),
            ("Wall of Glow", "✨"),
            ("OAuth", "🔐"),
            ("Integrations", "🔗"),
            ("Calendar", "📅"),
            ("Status", "💡"),
            ("Options", "⚙️"),
            ("Discord", "💬")
        ]
        
        for title, icon in nav_items:
            item = QListWidgetItem(f"{icon}  {title}")
            item.setData(Qt.UserRole, title.lower())
            self.sidebar.addItem(item)
        
        # Select first item by default
        self.sidebar.setCurrentRow(0)
        
    def setup_content_area(self):
        """Set up the content area with pages."""
        self.content_area = QWidget()
        layout = QVBoxLayout(self.content_area)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Page title
        self.page_title = QLabel()
        self.page_title.setObjectName("pageTitle")
        layout.addWidget(self.page_title)
        
        # Stacked widget for pages
        self.content_stack = QStackedWidget()
        layout.addWidget(self.content_stack)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self.reset_all_settings)
        button_layout.addWidget(self.reset_button)
        
        self.save_button = QPushButton("Save & Close")
        self.save_button.clicked.connect(self.save_and_close)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
        
        # Create all pages
        self.setup_pages()
        
    def setup_pages(self):
        """Set up all content pages."""
        # Create pages
        self.about_page = self.create_about_page()
        self.wall_of_glow_page = self.create_wall_of_glow_page()
        self.oauth_page = self.create_oauth_page()
        self.integrations_page = self.create_integrations_page()
        self.calendar_page = self.create_calendar_page()
        self.status_page = self.create_status_page()
        self.options_page = self.create_options_page()
        self.discord_page = self.create_discord_page()
        
        # Add pages to stack
        self.content_stack.addWidget(self.about_page)
        self.content_stack.addWidget(self.wall_of_glow_page)
        self.content_stack.addWidget(self.oauth_page)
        self.content_stack.addWidget(self.integrations_page)
        self.content_stack.addWidget(self.calendar_page)
        self.content_stack.addWidget(self.status_page)
        self.content_stack.addWidget(self.options_page)
        self.content_stack.addWidget(self.discord_page)
        
    def create_scrollable_page(self):
        """Create a scrollable page container."""
        page = QWidget()
        scroll = QScrollArea()
        scroll.setWidget(page)
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarNever)
        return scroll, page
        
    def create_about_page(self):
        """Create the About page."""
        scroll, page = self.create_scrollable_page()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # GlowStatus logo and title
        try:
            logo_path = resource_path("img/GlowStatus_TagLine_tight.png")
            if os.path.exists(logo_path):
                logo_label = QLabel()
                pixmap = QPixmap(logo_path)
                # Scale to reasonable size while maintaining aspect ratio
                scaled_pixmap = pixmap.scaledToWidth(400, Qt.SmoothTransformation)
                logo_label.setPixmap(scaled_pixmap)
                logo_label.setAlignment(Qt.AlignCenter)
                layout.addWidget(logo_label)
        except Exception as e:
            logger.warning(f"Could not load logo: {e}")
            title = QLabel("GlowStatus")
            title.setAlignment(Qt.AlignCenter)
            title.setObjectName("aboutTitle")
            layout.addWidget(title)
        
        # Description
        description = QLabel(
            "GlowStatus is an intelligent status indicator that synchronizes your calendar "
            "with smart lighting to automatically show your availability. Stay in the flow "
            "while keeping your team informed of your status."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        description.setObjectName("aboutDescription")
        layout.addWidget(description)
        
        # Version info
        version_info = QLabel("Version 1.0.0")
        version_info.setAlignment(Qt.AlignCenter)
        version_info.setObjectName("versionInfo")
        layout.addWidget(version_info)
        
        # Links
        links_frame = QFrame()
        links_layout = QHBoxLayout(links_frame)
        
        website_btn = QPushButton("🌐 Website")
        website_btn.clicked.connect(lambda: self.open_url("https://glowstatus.com"))
        links_layout.addWidget(website_btn)
        
        github_btn = QPushButton("🐙 GitHub")
        github_btn.clicked.connect(lambda: self.open_url("https://github.com/your-repo/glowstatus"))
        links_layout.addWidget(github_btn)
        
        discord_btn = QPushButton("💬 Discord")
        discord_btn.clicked.connect(lambda: self.open_url("https://discord.gg/3HAqNPSjng"))
        links_layout.addWidget(discord_btn)
        
        layout.addWidget(links_frame)
        layout.addStretch()
        
        return scroll
    
    def create_wall_of_glow_page(self):
        """Create the Wall of Glow page."""
        scroll, page = self.create_scrollable_page()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("✨ Wall of Glow")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        
        description = QLabel(
            "Thank you to our amazing supporters who make GlowStatus possible! "
            "Your contributions help us build better tools for remote teams."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Supporters section
        supporters_group = QGroupBox("🌟 Supporters")
        supporters_layout = QVBoxLayout(supporters_group)
        
        supporters_text = QLabel(
            "• Early adopters and beta testers\n"
            "• Community contributors\n"
            "• Feature requesters and bug reporters\n"
            "• Documentation helpers"
        )
        supporters_layout.addWidget(supporters_text)
        
        layout.addWidget(supporters_group)
        
        # Become a supporter
        support_group = QGroupBox("💝 Become a Supporter")
        support_layout = QVBoxLayout(support_group)
        
        support_text = QLabel(
            "Help us improve GlowStatus by:\n"
            "• Providing feedback and suggestions\n"
            "• Reporting bugs and issues\n"
            "• Sharing with your team\n"
            "• Contributing to the codebase"
        )
        support_layout.addWidget(support_text)
        
        support_btn = QPushButton("🚀 Join Our Community")
        support_btn.clicked.connect(lambda: self.open_url("https://discord.gg/3HAqNPSjng"))
        support_layout.addWidget(support_btn)
        
        layout.addWidget(support_group)
        layout.addStretch()
        
        return scroll
    
    def create_oauth_page(self):
        """Create the OAuth configuration page."""
        scroll, page = self.create_scrollable_page()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("🔐 Google Calendar OAuth")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        
        # OAuth status section
        status_group = QGroupBox("Connection Status")
        status_layout = QVBoxLayout(status_group)
        
        self.oauth_status_label = QLabel("Not connected")
        status_layout.addWidget(self.oauth_status_label)
        
        self.oauth_email_label = QLabel("")
        status_layout.addWidget(self.oauth_email_label)
        
        layout.addWidget(status_group)
        
        # OAuth controls
        controls_group = QGroupBox("Authentication")
        controls_layout = QVBoxLayout(controls_group)
        
        # Add Google logo button
        oauth_button_layout = QHBoxLayout()
        
        try:
            google_logo_path = resource_path("img/google_logo.png")
            if os.path.exists(google_logo_path):
                self.oauth_button = QPushButton()
                self.oauth_button.setText("  Connect with Google")
                self.oauth_button.setIcon(QIcon(google_logo_path))
                self.oauth_button.setIconSize(QSize(24, 24))
            else:
                self.oauth_button = QPushButton("🔑 Connect with Google")
        except Exception:
            self.oauth_button = QPushButton("🔑 Connect with Google")
        
        self.oauth_button.clicked.connect(self.run_oauth_flow)
        oauth_button_layout.addWidget(self.oauth_button)
        
        self.disconnect_button = QPushButton("🔓 Disconnect")
        self.disconnect_button.clicked.connect(self.disconnect_oauth)
        oauth_button_layout.addWidget(self.disconnect_button)
        
        controls_layout.addLayout(oauth_button_layout)
        
        # Progress bar for OAuth process
        self.oauth_progress = QProgressBar()
        self.oauth_progress.setVisible(False)
        controls_layout.addWidget(self.oauth_progress)
        
        # Instructions
        instructions = QLabel(
            "To connect to Google Calendar:\n\n"
            "1. Click 'Connect with Google'\n"
            "2. Sign in to your Google account\n"
            "3. Grant calendar access permissions\n"
            "4. Return to this app\n\n"
            "Your credentials are stored securely on your device."
        )
        instructions.setWordWrap(True)
        controls_layout.addWidget(instructions)
        
        layout.addWidget(controls_group)
        layout.addStretch()
        
        return scroll
    
    def create_integrations_page(self):
        """Create the Integrations page."""
        scroll, page = self.create_scrollable_page()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("🔗 Integrations")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        
        # Govee Integration
        govee_group = QGroupBox("💡 Govee Smart Lights")
        govee_layout = QFormLayout(govee_group)
        
        # API Key
        self.govee_api_key_edit = QLineEdit()
        self.govee_api_key_edit.setEchoMode(QLineEdit.Password)
        self.govee_api_key_edit.setPlaceholderText("Enter your Govee API key")
        govee_layout.addRow("API Key:", self.govee_api_key_edit)
        
        # Device ID
        self.govee_device_id_edit = QLineEdit()
        self.govee_device_id_edit.setPlaceholderText("Enter your device ID")
        govee_layout.addRow("Device ID:", self.govee_device_id_edit)
        
        # Test connection button
        test_govee_btn = QPushButton("🔍 Test Connection")
        test_govee_btn.clicked.connect(self.test_govee_connection)
        govee_layout.addRow("", test_govee_btn)
        
        # Instructions
        govee_instructions = QLabel(
            "Get your Govee API key and device ID from the Govee Home app:\n"
            "1. Open Govee Home app\n"
            "2. Go to Settings → About Us → Apply for API Key\n"
            "3. For Device ID: Settings → Device Settings → Device Info"
        )
        govee_instructions.setWordWrap(True)
        govee_layout.addRow("Instructions:", govee_instructions)
        
        layout.addWidget(govee_group)
        
        # Future integrations placeholder
        future_group = QGroupBox("🚀 Coming Soon")
        future_layout = QVBoxLayout(future_group)
        
        future_text = QLabel(
            "• Philips Hue lights\n"
            "• LIFX bulbs\n"
            "• Microsoft Teams status\n"
            "• Slack integration\n"
            "• Zoom status sync"
        )
        future_layout.addWidget(future_text)
        
        layout.addWidget(future_group)
        layout.addStretch()
        
        return scroll
    
    def create_calendar_page(self):
        """Create the Calendar settings page."""
        scroll, page = self.create_scrollable_page()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("📅 Calendar Settings")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        
        # Calendar selection
        calendar_group = QGroupBox("Calendar Selection")
        calendar_layout = QFormLayout(calendar_group)
        
        self.selected_calendar_dropdown = QComboBox()
        calendar_layout.addRow("Primary Calendar:", self.selected_calendar_dropdown)
        
        refresh_btn = QPushButton("🔄 Refresh Calendars")
        refresh_btn.clicked.connect(self.refresh_calendars)
        calendar_layout.addRow("", refresh_btn)
        
        layout.addWidget(calendar_group)
        
        # Sync settings
        sync_group = QGroupBox("Synchronization")
        sync_layout = QFormLayout(sync_group)
        
        self.disable_sync_checkbox = QCheckBox("Disable calendar synchronization")
        sync_layout.addRow(self.disable_sync_checkbox)
        
        self.sync_interval_spinbox = QSpinBox()
        self.sync_interval_spinbox.setRange(5, 300)
        self.sync_interval_spinbox.setSuffix(" seconds")
        sync_layout.addRow("Sync Interval:", self.sync_interval_spinbox)
        
        layout.addWidget(sync_group)
        
        # Meeting detection
        detection_group = QGroupBox("Meeting Detection")
        detection_layout = QVBoxLayout(detection_group)
        
        self.detect_all_day_checkbox = QCheckBox("Include all-day events")
        detection_layout.addWidget(self.detect_all_day_checkbox)
        
        self.detect_declined_checkbox = QCheckBox("Include declined meetings")
        detection_layout.addWidget(self.detect_declined_checkbox)
        
        layout.addWidget(detection_group)
        layout.addStretch()
        
        return scroll
    
    def create_status_page(self):
        """Create the Status configuration page."""
        scroll, page = self.create_scrollable_page()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("💡 Status Colors")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        
        # Status colors table
        colors_group = QGroupBox("Status Color Mapping")
        colors_layout = QVBoxLayout(colors_group)
        
        # Create table for status colors
        self.status_colors_table = QTableWidget()
        self.status_colors_table.setColumnCount(3)
        self.status_colors_table.setHorizontalHeaderLabels(["Status", "Color", "Actions"])
        self.status_colors_table.horizontalHeader().setStretchLastSection(True)
        
        # Populate table with default statuses
        self.populate_status_colors_table()
        
        colors_layout.addWidget(self.status_colors_table)
        
        # Add/remove buttons
        table_buttons = QHBoxLayout()
        
        add_status_btn = QPushButton("➕ Add Status")
        add_status_btn.clicked.connect(self.add_custom_status)
        table_buttons.addWidget(add_status_btn)
        
        remove_status_btn = QPushButton("➖ Remove Selected")
        remove_status_btn.clicked.connect(self.remove_selected_status)
        table_buttons.addWidget(remove_status_btn)
        
        table_buttons.addStretch()
        
        reset_colors_btn = QPushButton("🔄 Reset to Defaults")
        reset_colors_btn.clicked.connect(self.reset_status_colors)
        table_buttons.addWidget(reset_colors_btn)
        
        colors_layout.addLayout(table_buttons)
        
        layout.addWidget(colors_group)
        
        # Default status
        default_group = QGroupBox("Default Settings")
        default_layout = QFormLayout(default_group)
        
        self.default_status_combo = QComboBox()
        default_layout.addRow("Default Status:", self.default_status_combo)
        
        layout.addWidget(default_group)
        layout.addStretch()
        
        return scroll
    
    def create_options_page(self):
        """Create the Options page."""
        scroll, page = self.create_scrollable_page()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("⚙️ Options")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        
        # General options
        general_group = QGroupBox("General")
        general_layout = QVBoxLayout(general_group)
        
        self.start_with_system_checkbox = QCheckBox("Start with system")
        general_layout.addWidget(self.start_with_system_checkbox)
        
        self.minimize_to_tray_checkbox = QCheckBox("Minimize to system tray")
        general_layout.addWidget(self.minimize_to_tray_checkbox)
        
        self.show_notifications_checkbox = QCheckBox("Show notifications")
        general_layout.addWidget(self.show_notifications_checkbox)
        
        layout.addWidget(general_group)
        
        # Logging
        logging_group = QGroupBox("Logging")
        logging_layout = QFormLayout(logging_group)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        logging_layout.addRow("Log Level:", self.log_level_combo)
        
        view_logs_btn = QPushButton("📄 View Logs")
        view_logs_btn.clicked.connect(self.view_logs)
        logging_layout.addRow("", view_logs_btn)
        
        layout.addWidget(logging_group)
        
        # Advanced options
        advanced_group = QGroupBox("Advanced")
        advanced_layout = QVBoxLayout(advanced_group)
        
        self.debug_mode_checkbox = QCheckBox("Enable debug mode")
        advanced_layout.addWidget(self.debug_mode_checkbox)
        
        export_config_btn = QPushButton("💾 Export Configuration")
        export_config_btn.clicked.connect(self.export_configuration)
        advanced_layout.addWidget(export_config_btn)
        
        import_config_btn = QPushButton("📁 Import Configuration")
        import_config_btn.clicked.connect(self.import_configuration)
        advanced_layout.addWidget(import_config_btn)
        
        layout.addWidget(advanced_group)
        layout.addStretch()
        
        return scroll
    
    def create_discord_page(self):
        """Create the Discord information page."""
        scroll, page = self.create_scrollable_page()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("💬 Discord Community")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        
        # Community info
        community_group = QGroupBox("Join Our Community")
        community_layout = QVBoxLayout(community_group)
        
        description = QLabel(
            "Connect with other GlowStatus users, get support, share tips, "
            "and stay updated on the latest features!"
        )
        description.setWordWrap(True)
        community_layout.addWidget(description)
        
        # Discord invite button
        discord_btn = QPushButton("💬 Join Discord Server")
        discord_btn.clicked.connect(lambda: self.open_url("https://discord.gg/3HAqNPSjng"))
        community_layout.addWidget(discord_btn)
        
        layout.addWidget(community_group)
        
        # Support info
        support_group = QGroupBox("Get Support")
        support_layout = QVBoxLayout(support_group)
        
        support_text = QLabel(
            "Need help? Our Discord community is the best place to:\n\n"
            "• Get quick answers to questions\n"
            "• Report bugs and issues\n"
            "• Request new features\n"
            "• Share your setup and configurations\n"
            "• Connect with the development team"
        )
        support_layout.addWidget(support_text)
        
        layout.addWidget(support_group)
        layout.addStretch()
        
        return scroll
    
    def change_page(self, index):
        """Change the current page based on sidebar selection."""
        if index >= 0:
            self.content_stack.setCurrentIndex(index)
            
            # Update page title
            item = self.sidebar.item(index)
            if item:
                title = item.data(Qt.UserRole)
                display_titles = {
                    "about": "About GlowStatus",
                    "wall of glow": "Wall of Glow",
                    "oauth": "Google Calendar OAuth",
                    "integrations": "Integrations",
                    "calendar": "Calendar Settings", 
                    "status": "Status Configuration",
                    "options": "Options",
                    "discord": "Discord Community"
                }
                self.page_title.setText(display_titles.get(title, title.title()))
    
    def load_settings(self):
        """Load settings from configuration into UI elements."""
        # Update OAuth status
        self.update_oauth_status()
        
        # Load Govee settings
        if hasattr(self, 'govee_api_key_edit'):
            try:
                api_key = keyring.get_password("GlowStatus", "govee_api_key")
                if api_key:
                    self.govee_api_key_edit.setText(api_key)
            except (NoKeyringError, Exception):
                pass
            
            self.govee_device_id_edit.setText(self.config.get("GOVEE_DEVICE_ID", ""))
        
        # Load calendar settings
        if hasattr(self, 'disable_sync_checkbox'):
            self.disable_sync_checkbox.setChecked(self.config.get("DISABLE_CALENDAR_SYNC", False))
            self.sync_interval_spinbox.setValue(self.config.get("SYNC_INTERVAL", 30))
        
        # Load status colors
        self.populate_status_colors_table()
        
        # Load default status
        if hasattr(self, 'default_status_combo'):
            self.default_status_combo.clear()
            statuses = list(self.config.get("STATUS_COLORS", {}).keys())
            self.default_status_combo.addItems(statuses)
            default_status = self.config.get("DEFAULT_STATUS", "Available")
            index = self.default_status_combo.findText(default_status)
            if index >= 0:
                self.default_status_combo.setCurrentIndex(index)
        
        # Load calendars if OAuth is connected
        self.refresh_calendars()
    
    def update_oauth_status(self):
        """Update OAuth connection status display."""
        if hasattr(self, 'oauth_status_label'):
            if os.path.exists(TOKEN_PATH):
                self.oauth_status_label.setText("✅ Connected to Google Calendar")
                self.oauth_status_label.setStyleSheet("color: green;")
                self.oauth_button.setText("🔄 Reconnect")
                self.disconnect_button.setEnabled(True)
                
                # Try to get user email
                try:
                    import pickle
                    with open(TOKEN_PATH, "rb") as token:
                        creds = pickle.load(token)
                        if hasattr(creds, 'token') and creds.valid:
                            # Try to get email from calendar service
                            from googleapiclient.discovery import build
                            service = build("calendar", "v3", credentials=creds)
                            calendar_list = service.calendarList().list().execute()
                            calendars = calendar_list.get("items", [])
                            
                            for cal in calendars:
                                if cal.get("primary"):
                                    email = cal.get("id", "")
                                    self.oauth_email_label.setText(f"Account: {email}")
                                    break
                except Exception:
                    self.oauth_email_label.setText("Account: Connected")
            else:
                self.oauth_status_label.setText("❌ Not connected")
                self.oauth_status_label.setStyleSheet("color: red;")
                self.oauth_button.setText("🔑 Connect with Google")
                self.disconnect_button.setEnabled(False)
                self.oauth_email_label.setText("")
    
    def run_oauth_flow(self):
        """Start the OAuth authentication flow."""
        if self.oauth_worker and self.oauth_worker.isRunning():
            QMessageBox.information(self, "GlowStatus", "OAuth process is already running.")
            return
        
        # Show progress and disable button
        self.oauth_progress.setVisible(True)
        self.oauth_progress.setRange(0, 0)  # Indeterminate progress
        self.oauth_button.setEnabled(False)
        self.oauth_button.setText("Connecting...")
        
        # Create and start worker thread
        self.oauth_worker = OAuthWorker()
        self.oauth_worker.oauth_success.connect(self.on_oauth_success)
        self.oauth_worker.oauth_error.connect(self.on_oauth_error)
        self.oauth_worker.oauth_no_calendars.connect(self.on_oauth_no_calendars)
        self.oauth_worker.finished.connect(self.on_oauth_finished)
        self.oauth_worker.start()
    
    def on_oauth_success(self, user_email, calendars):
        """Handle successful OAuth authentication."""
        QMessageBox.information(
            self, 
            "GlowStatus - OAuth Success", 
            f"Successfully connected to Google Calendar!\nAccount: {user_email}"
        )
        
        # Update config with user email if not already set
        if user_email and "GOOGLE_USER_EMAIL" not in self.config:
            self.config["GOOGLE_USER_EMAIL"] = user_email
            save_config(self.config)
        
        # Update calendar dropdown
        if hasattr(self, 'selected_calendar_dropdown'):
            self.selected_calendar_dropdown.clear()
            for cal in calendars:
                summary = cal.get("summary", "")
                cal_id = cal.get("id", "")
                display = f"{summary} ({cal_id})" if summary else cal_id
                self.selected_calendar_dropdown.addItem(display, cal_id)
        
        self.update_oauth_status()
    
    def on_oauth_error(self, error_message):
        """Handle OAuth authentication error."""
        QMessageBox.warning(
            self, 
            "GlowStatus - OAuth Error", 
            f"OAuth authentication failed:\n{error_message}"
        )
    
    def on_oauth_no_calendars(self):
        """Handle case where OAuth succeeds but no calendars are found."""
        QMessageBox.warning(
            self, 
            "GlowStatus - No Calendars", 
            "OAuth successful, but no calendars were found in your account."
        )
        self.update_oauth_status()
    
    def on_oauth_finished(self):
        """Handle OAuth process completion."""
        self.oauth_progress.setVisible(False)
        self.oauth_button.setEnabled(True)
        self.update_oauth_status()
    
    def disconnect_oauth(self):
        """Disconnect OAuth and remove stored credentials."""
        reply = QMessageBox.question(
            self,
            "GlowStatus - Disconnect OAuth",
            "Are you sure you want to disconnect from Google Calendar?\n"
            "You will need to re-authenticate to sync calendar events.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                if os.path.exists(TOKEN_PATH):
                    os.remove(TOKEN_PATH)
                
                # Clear calendar dropdown
                if hasattr(self, 'selected_calendar_dropdown'):
                    self.selected_calendar_dropdown.clear()
                
                self.update_oauth_status()
                QMessageBox.information(
                    self, 
                    "GlowStatus", 
                    "Successfully disconnected from Google Calendar."
                )
                
            except Exception as e:
                QMessageBox.warning(
                    self, 
                    "GlowStatus - Error", 
                    f"Failed to disconnect: {str(e)}"
                )
    
    def refresh_calendars(self):
        """Refresh the calendar list."""
        if not os.path.exists(TOKEN_PATH):
            return
        
        try:
            import pickle
            from googleapiclient.discovery import build
            
            with open(TOKEN_PATH, "rb") as token:
                creds = pickle.load(token)
            
            if creds and creds.valid:
                service = build("calendar", "v3", credentials=creds)
                calendar_list = service.calendarList().list().execute()
                calendars = calendar_list.get("items", [])
                
                if hasattr(self, 'selected_calendar_dropdown'):
                    current_selection = self.selected_calendar_dropdown.currentData()
                    self.selected_calendar_dropdown.clear()
                    
                    for cal in calendars:
                        summary = cal.get("summary", "")
                        cal_id = cal.get("id", "")
                        display = f"{summary} ({cal_id})" if summary else cal_id
                        self.selected_calendar_dropdown.addItem(display, cal_id)
                    
                    # Restore previous selection if possible
                    if current_selection:
                        index = self.selected_calendar_dropdown.findData(current_selection)
                        if index >= 0:
                            self.selected_calendar_dropdown.setCurrentIndex(index)
                            
        except Exception as e:
            logger.warning(f"Failed to refresh calendars: {e}")
    
    def test_govee_connection(self):
        """Test Govee API connection."""
        api_key = self.govee_api_key_edit.text().strip()
        device_id = self.govee_device_id_edit.text().strip()
        
        if not api_key or not device_id:
            QMessageBox.warning(
                self, 
                "GlowStatus", 
                "Please enter both API key and device ID."
            )
            return
        
        # Test connection logic would go here
        QMessageBox.information(
            self, 
            "GlowStatus", 
            "Govee connection test feature coming soon!"
        )
    
    def populate_status_colors_table(self):
        """Populate the status colors table with current settings."""
        if not hasattr(self, 'status_colors_table'):
            return
        
        status_colors = self.config.get("STATUS_COLORS", {})
        self.status_colors_table.setRowCount(len(status_colors))
        
        for row, (status, color) in enumerate(status_colors.items()):
            # Status name
            status_item = QTableWidgetItem(status)
            self.status_colors_table.setItem(row, 0, status_item)
            
            # Color display
            color_item = QTableWidgetItem(color)
            color_item.setBackground(QColor(color))
            self.status_colors_table.setItem(row, 1, color_item)
            
            # Change color button
            change_btn = QPushButton("🎨 Change")
            change_btn.clicked.connect(lambda checked, r=row: self.change_status_color(r))
            self.status_colors_table.setCellWidget(row, 2, change_btn)
    
    def change_status_color(self, row):
        """Change the color for a status."""
        status_item = self.status_colors_table.item(row, 0)
        if not status_item:
            return
        
        status = status_item.text()
        current_color = self.config.get("STATUS_COLORS", {}).get(status, "#FFFFFF")
        
        color = QColorDialog.getColor(QColor(current_color), self, f"Choose color for {status}")
        if color.isValid():
            color_hex = color.name()
            
            # Update config
            if "STATUS_COLORS" not in self.config:
                self.config["STATUS_COLORS"] = {}
            self.config["STATUS_COLORS"][status] = color_hex
            
            # Update table
            color_item = self.status_colors_table.item(row, 1)
            color_item.setText(color_hex)
            color_item.setBackground(color)
    
    def add_custom_status(self):
        """Add a custom status."""
        # This would open a dialog to add a new status
        QMessageBox.information(
            self, 
            "GlowStatus", 
            "Custom status feature coming soon!"
        )
    
    def remove_selected_status(self):
        """Remove the selected status."""
        current_row = self.status_colors_table.currentRow()
        if current_row >= 0:
            status_item = self.status_colors_table.item(current_row, 0)
            if status_item:
                status = status_item.text()
                reply = QMessageBox.question(
                    self,
                    "GlowStatus",
                    f"Remove status '{status}'?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    if "STATUS_COLORS" in self.config and status in self.config["STATUS_COLORS"]:
                        del self.config["STATUS_COLORS"][status]
                        self.populate_status_colors_table()
    
    def reset_status_colors(self):
        """Reset status colors to defaults."""
        reply = QMessageBox.question(
            self,
            "GlowStatus",
            "Reset all status colors to defaults?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Reset to defaults
            self.config["STATUS_COLORS"] = {
                "Available": "#00FF00",
                "Busy": "#FF0000", 
                "Away": "#FFFF00",
                "Do Not Disturb": "#800080",
                "Offline": "#808080",
                "Meeting": "#FF4500",
                "Presenting": "#FF69B4",
                "Tentative": "#FFA500",
                "Out of Office": "#000080"
            }
            self.populate_status_colors_table()
    
    def view_logs(self):
        """Open log viewer."""
        QMessageBox.information(
            self, 
            "GlowStatus", 
            "Log viewer feature coming soon!"
        )
    
    def export_configuration(self):
        """Export current configuration to file."""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export GlowStatus Configuration",
            "glowstatus_config.json",
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.config, f, indent=2)
                QMessageBox.information(
                    self, 
                    "GlowStatus", 
                    f"Configuration exported to {filename}"
                )
            except Exception as e:
                QMessageBox.warning(
                    self, 
                    "GlowStatus - Export Error", 
                    f"Failed to export configuration: {str(e)}"
                )
    
    def import_configuration(self):
        """Import configuration from file."""
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Import GlowStatus Configuration",
            "",
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    imported_config = json.load(f)
                
                reply = QMessageBox.question(
                    self,
                    "GlowStatus",
                    "Import configuration? This will overwrite current settings.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    self.config.update(imported_config)
                    self.load_settings()
                    QMessageBox.information(
                        self, 
                        "GlowStatus", 
                        "Configuration imported successfully!"
                    )
                    
            except Exception as e:
                QMessageBox.warning(
                    self, 
                    "GlowStatus - Import Error", 
                    f"Failed to import configuration: {str(e)}"
                )
    
    def reset_all_settings(self):
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self,
            "GlowStatus - Reset Settings",
            "Are you sure you want to reset all settings to defaults?\n"
            "This cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Reset config to defaults
            self.config = load_config()  # This will load defaults
            
            # Clear keyring entries
            try:
                keyring.delete_password("GlowStatus", "govee_api_key")
            except Exception:
                pass
            
            # Reload UI
            self.load_settings()
            
            QMessageBox.information(
                self, 
                "GlowStatus", 
                "Settings have been reset to defaults."
            )
    
    def save_and_close(self):
        """Save all settings and close the window."""
        self.save_all_settings()
        self.accept()
    
    def save_all_settings(self):
        """Save all settings from UI to configuration."""
        # Save Govee settings
        if hasattr(self, 'govee_api_key_edit'):
            api_key = self.govee_api_key_edit.text().strip()
            if api_key:
                try:
                    keyring.set_password("GlowStatus", "govee_api_key", api_key)
                except Exception as e:
                    logger.warning(f"Failed to save Govee API key: {e}")
            
            self.config["GOVEE_DEVICE_ID"] = self.govee_device_id_edit.text().strip()
        
        # Save calendar settings
        if hasattr(self, 'disable_sync_checkbox'):
            self.config["DISABLE_CALENDAR_SYNC"] = self.disable_sync_checkbox.isChecked()
            self.config["SYNC_INTERVAL"] = self.sync_interval_spinbox.value()
        
        # Save selected calendar
        if hasattr(self, 'selected_calendar_dropdown'):
            selected_cal = self.selected_calendar_dropdown.currentData()
            if selected_cal:
                self.config["SELECTED_CALENDAR_ID"] = selected_cal
        
        # Save default status
        if hasattr(self, 'default_status_combo'):
            self.config["DEFAULT_STATUS"] = self.default_status_combo.currentText()
        
        # Save general options
        if hasattr(self, 'start_with_system_checkbox'):
            self.config["START_WITH_SYSTEM"] = self.start_with_system_checkbox.isChecked()
        
        if hasattr(self, 'minimize_to_tray_checkbox'):
            self.config["MINIMIZE_TO_TRAY"] = self.minimize_to_tray_checkbox.isChecked()
        
        if hasattr(self, 'show_notifications_checkbox'):
            self.config["SHOW_NOTIFICATIONS"] = self.show_notifications_checkbox.isChecked()
        
        # Save logging level
        if hasattr(self, 'log_level_combo'):
            self.config["LOG_LEVEL"] = self.log_level_combo.currentText()
        
        if hasattr(self, 'debug_mode_checkbox'):
            self.config["DEBUG_MODE"] = self.debug_mode_checkbox.isChecked()
        
        # Save configuration
        save_config(self.config)
        logger.info("All settings saved successfully")
    
    def open_url(self, url):
        """Open URL in default browser."""
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception as e:
            logger.warning(f"Failed to open URL: {e}")
            QMessageBox.information(
                self, 
                "GlowStatus", 
                f"Please visit: {url}"
            )
    
    def apply_theme(self):
        """Apply GlowStatus theme to the window."""
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            
            QListWidget#sidebar {
                background-color: #2d3748;
                color: white;
                border: none;
                font-size: 14px;
                padding: 5px;
            }
            
            QListWidget#sidebar::item {
                padding: 12px;
                border-radius: 6px;
                margin: 2px;
            }
            
            QListWidget#sidebar::item:selected {
                background-color: #4a90e2;
            }
            
            QListWidget#sidebar::item:hover {
                background-color: #4a5568;
            }
            
            QLabel#pageTitle {
                font-size: 24px;
                font-weight: bold;
                color: #2d3748;
                padding: 20px;
                background-color: white;
                border-bottom: 1px solid #e2e8f0;
            }
            
            QLabel#sectionTitle {
                font-size: 18px;
                font-weight: bold;
                color: #2d3748;
                margin-bottom: 10px;
            }
            
            QLabel#aboutTitle {
                font-size: 28px;
                font-weight: bold;
                color: #4a90e2;
                margin: 20px 0;
            }
            
            QLabel#aboutDescription {
                font-size: 14px;
                color: #4a5568;
                line-height: 1.5;
                margin: 20px 0;
            }
            
            QLabel#versionInfo {
                font-size: 12px;
                color: #a0aec0;
                margin: 10px 0;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: white;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: #4a90e2;
            }
            
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 100px;
            }
            
            QPushButton:hover {
                background-color: #357abd;
            }
            
            QPushButton:pressed {
                background-color: #2c5aa0;
            }
            
            QPushButton:disabled {
                background-color: #a0aec0;
                color: #e2e8f0;
            }
            
            QLineEdit, QSpinBox, QComboBox {
                padding: 8px;
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                background-color: white;
                font-size: 13px;
            }
            
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border-color: #4a90e2;
            }
            
            QTableWidget {
                gridline-color: #e2e8f0;
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
            }
            
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #e2e8f0;
            }
            
            QTableWidget::item:selected {
                background-color: #ebf8ff;
                color: #2d3748;
            }
            
            QCheckBox {
                color: #2d3748;
                font-size: 13px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 2px solid #e2e8f0;
                background-color: white;
            }
            
            QCheckBox::indicator:checked {
                background-color: #4a90e2;
                border-color: #4a90e2;
            }
            
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            
            QProgressBar {
                border: 2px solid #e2e8f0;
                border-radius: 6px;
                text-align: center;
                background-color: #f7fafc;
            }
            
            QProgressBar::chunk {
                background-color: #4a90e2;
                border-radius: 4px;
            }
        """)

# Main function for testing
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = SettingsWindow()
    window.show()
    sys.exit(app.exec())
