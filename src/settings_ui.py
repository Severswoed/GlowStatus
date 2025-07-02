import os
import json
import pickle
import keyring
import webbrowser
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
        "DISABLE_LIGHT_CONTROL": True,  # Default to disabled until credentials are set
        "REFRESH_INTERVAL": 15,
        "POWER_OFF_WHEN_AVAILABLE": True,
        "OFF_FOR_UNKNOWN_STATUS": True,
        "GOVEE_DEVICE_ID": "",
        "GOVEE_DEVICE_MODEL": "",
        "SELECTED_CALENDAR_ID": "",
        "TRAY_ICON": "GlowStatus_tray_tp.png",  # Fixed tray icon
        "STATUS_COLOR_MAP": {
            "in_meeting": {"color": "255,0,0", "power_off": False},
            "focus": {"color": "0,0,255", "power_off": False},
            "available": {"color": "0,255,0", "power_off": True},
            "lunch": {"color": "0,255,0", "power_off": True},
            "offline": {"color": "128,128,128", "power_off": False}
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
        self._govee_test_active = False  # Track test state
        self.form_dirty = False  # Track unsaved changes
        self.original_values = {}  # Store original form values
        self.setup_ui()
        self.load_settings()
        self.setup_form_change_tracking()
        
    def setup_ui(self):
        """Set up the main UI."""
        self.setWindowTitle("GlowStatus Settings")
        self.setMinimumSize(900, 700)
        self.resize(1000, 800)
        
        # Set application branding for notifications
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.setApplicationName("GlowStatus")
            app.setApplicationDisplayName("GlowStatus")
            try:
                from version import get_version_string
                app.setApplicationVersion(get_version_string())
            except ImportError:
                app.setApplicationVersion("2.1.0")
            app.setOrganizationName("GlowStatus")
            app.setOrganizationDomain("glowstatus.com")
        
        # Try to set window icon
        try:
            icon_path = resource_path("img/GlowStatus_tray_tp.png")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                # Also set as application icon
                if app:
                    app.setWindowIcon(QIcon(icon_path))
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
        
        # Connect sidebar selection to content switching (after content_stack is created)
        self.sidebar.currentRowChanged.connect(self.change_page)
        
        # Select first item by default
        self.sidebar.setCurrentRow(0)
        
        # Apply GlowStatus theme
        self.apply_theme()
        
        # Force enable all widgets to ensure interactivity
        self.setEnabled(True)
        for widget in self.findChildren(QCheckBox):
            widget.setEnabled(True)
            widget.setCheckable(True)
            # Add debug info
            logger.info(f"Enabled checkbox: {widget.text()}, enabled={widget.isEnabled()}, checkable={widget.isCheckable()}")
        
        # Also ensure all spinboxes are enabled
        for widget in self.findChildren(QSpinBox):
            widget.setEnabled(True)
            logger.info(f"Enabled spinbox: enabled={widget.isEnabled()}")
        
    def setup_sidebar(self):
        """Set up the navigation sidebar."""
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(250)
        self.sidebar.setObjectName("sidebar")
        
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
        
        # Note: Signal connection moved to setup_ui after content area is created
        
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
        
        # Save status label
        self.save_status_label = QLabel("Ready")
        self.save_status_label.setAlignment(Qt.AlignCenter)
        self.save_status_label.setStyleSheet("color: #666; font-size: 12px; margin: 5px 0;")
        layout.addWidget(self.save_status_label)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self.reset_all_settings)
        button_layout.addWidget(self.reset_button)
        
        self.save_button = QPushButton("Save & Close")
        self.save_button.clicked.connect(self.save_and_close)
        button_layout.addWidget(self.save_button)
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
        
    def setup_form_change_tracking(self):
        """Set up form change tracking for unsaved changes detection."""
        # Store original values for comparison
        self.original_values = {}
        
        # This method is called after load_settings() so we can capture initial state
        # The actual tracking is handled by connecting signals in individual form elements
        # which call self.on_form_changed() when values change
        
        # Initialize save status
        self.form_dirty = False
        if hasattr(self, 'save_status_label'):
            self.update_save_status()
    
    def create_scrollable_page(self):
        """Create a scrollable page container."""
        page = QWidget()
        page.setEnabled(True)  # Explicitly enable the page widget
        scroll = QScrollArea()
        scroll.setWidget(page)
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setEnabled(True)  # Explicitly enable the scroll area
        return scroll, page
        
    def create_about_page(self):
        """Create the About page."""
        scroll, page = self.create_scrollable_page()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(32)
        
        # Add some top spacing for visual balance
        layout.addSpacing(20)
        
        # GlowStatus logo and title - more elegant and smaller
        try:
            logo_path = resource_path("img/GlowStatus_TagLine_tight.png")
            if os.path.exists(logo_path):
                logo_label = QLabel()
                pixmap = QPixmap(logo_path)
                # Scale to smaller, more elegant size for better visual balance
                scaled_pixmap = pixmap.scaledToWidth(280, Qt.SmoothTransformation)
                logo_label.setPixmap(scaled_pixmap)
                logo_label.setAlignment(Qt.AlignCenter)
                # Add elegant styling with subtle shadow effect
                logo_label.setStyleSheet("""
                    QLabel {
                        background-color: rgba(255, 255, 255, 0.01);
                        border: 1px solid rgba(255, 255, 255, 0.03);
                        border-radius: 12px;
                        padding: 20px 24px;
                        margin: 8px 0;
                    }
                """)
                layout.addWidget(logo_label)
                layout.addSpacing(12)
        except Exception as e:
            logger.warning(f"Could not load logo: {e}")
            title = QLabel("GlowStatus")
            title.setAlignment(Qt.AlignCenter)
            title.setObjectName("aboutTitle")
            layout.addWidget(title)
            layout.addSpacing(20)
        
        # Description with emojis
        description = QLabel(
            "🚀 GlowStatus is an intelligent status indicator that synchronizes your calendar "
            "with smart lighting to automatically show your availability. ✨ Stay in the flow "
            "while keeping your team informed of your status! 💡\n\n"
            "🎯 Perfect for remote workers, streamers, and anyone who wants to communicate "
            "their availability without interruption. Transform your workspace into a visual "
            "status dashboard that works seamlessly with your daily routine! 🏠💼"
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        description.setObjectName("aboutDescription")
        layout.addWidget(description)
        
        layout.addSpacing(20)
        
        # Fun stats section
        stats_frame = QFrame()
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setSpacing(24)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_layout.addStretch()
        
        meetings_stat = QLabel("📅\n0+\nMeetings\nSynced")
        meetings_stat.setAlignment(Qt.AlignCenter)
        meetings_stat.setStyleSheet("font-size: 12px; font-weight: 500; color: #38bdf8; line-height: 1.4;")
        stats_layout.addWidget(meetings_stat)
        
        users_stat = QLabel("👥\n0+\nHappy\nUsers")
        users_stat.setAlignment(Qt.AlignCenter)
        users_stat.setStyleSheet("font-size: 12px; font-weight: 500; color: #10b981; line-height: 1.4;")
        stats_layout.addWidget(users_stat)
        
        lights_stat = QLabel("💡\n0+\nLights\nControlled")
        lights_stat.setAlignment(Qt.AlignCenter)
        lights_stat.setStyleSheet("font-size: 12px; font-weight: 500; color: #f59e0b; line-height: 1.4;")
        stats_layout.addWidget(lights_stat)
        
        stats_layout.addStretch()
        layout.addWidget(stats_frame)
        
        layout.addSpacing(20)
        
        # Version info with fun emoji
        try:
            from version import get_version_display
            version_text = f"🏷️ {get_version_display()} - The Glow Revolution Begins! ✨"
        except ImportError:
            version_text = "🏷️ Version 2.1.0 - The Glow Revolution Begins! ✨"
        
        version_info = QLabel(version_text)
        version_info.setAlignment(Qt.AlignCenter)
        version_info.setObjectName("versionInfo")
        layout.addWidget(version_info)
        
        layout.addSpacing(32)
        
        # Links section with enhanced buttons
        links_frame = QFrame()
        links_layout = QHBoxLayout(links_frame)
        links_layout.setSpacing(16)
        links_layout.setContentsMargins(0, 0, 0, 0)
        
        # Center the buttons
        links_layout.addStretch()
        
        website_btn = QPushButton("🌐 Visit Website")
        website_btn.setToolTip("Check out our awesome website! 🚀")
        website_btn.clicked.connect(lambda: self.open_url("https://glowstatus.com"))
        links_layout.addWidget(website_btn)
        
        github_btn = QPushButton("🐙 Star on GitHub")
        github_btn.setToolTip("Give us a star and contribute! ⭐")
        github_btn.clicked.connect(lambda: self.open_url("https://github.com/your-repo/glowstatus"))
        links_layout.addWidget(github_btn)
        
        discord_btn = QPushButton("💬 Join Discord")
        discord_btn.setToolTip("Chat with our amazing community! 🎉")
        discord_btn.clicked.connect(lambda: self.open_url("https://discord.gg/xtNevM3WuV"))
        links_layout.addWidget(discord_btn)
        
        links_layout.addStretch()
        
        layout.addWidget(links_frame)
        layout.addStretch()
        
        return scroll
    
    def create_wall_of_glow_page(self):
        """Create the Wall of Glow page."""
        scroll, page = self.create_scrollable_page()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("✨ Wall of Glow - Our Amazing Community! ✨")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        
        description = QLabel(
            "🙏 Thank you to our incredible supporters who make GlowStatus shine brighter every day! "
            "🌟 Your contributions, feedback, and enthusiasm help us build better tools for remote teams "
            "around the world. Together, we're revolutionizing how people communicate their status! 🚀💫"
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Hall of Fame section
        hall_of_fame_group = QGroupBox("� Hall of Fame - Legendary Contributors")
        hall_of_fame_layout = QVBoxLayout(hall_of_fame_group)
        
        hall_of_fame_text = QLabel(
            "🥇 **Beta Testing Champions** - Our fearless early adopters who found all the bugs! 🐛➡️✨\n"
            "🥈 **Feature Wizards** - Brilliant minds who suggested game-changing features 🧙‍♂️💡\n"
            "🥉 **Documentation Heroes** - The unsung heroes who made our docs crystal clear 📚⭐\n"
            "🎖️ **Bug Hunters** - Sharp-eyed users who helped us squash pesky bugs 🔍🎯\n"
            "🌟 **Community Ambassadors** - Awesome people spreading the GlowStatus love! 💖📢"
        )
        hall_of_fame_text.setWordWrap(True)
        hall_of_fame_layout.addWidget(hall_of_fame_text)
        
        layout.addWidget(hall_of_fame_group)
        
        # Active community stats
        community_stats_group = QGroupBox("📊 Community Glow Stats")
        community_stats_layout = QHBoxLayout(community_stats_group)
        
        discord_stat = QLabel("💬\n0+\nDiscord\nMembers")
        discord_stat.setAlignment(Qt.AlignCenter)
        discord_stat.setStyleSheet("font-size: 12px; font-weight: 600; color: #8b5cf6; line-height: 1.4;")
        community_stats_layout.addWidget(discord_stat)
        
        github_stat = QLabel("⭐\n0+\nGitHub\nStars")
        github_stat.setAlignment(Qt.AlignCenter)
        github_stat.setStyleSheet("font-size: 12px; font-weight: 600; color: #fbbf24; line-height: 1.4;")
        community_stats_layout.addWidget(github_stat)
        
        downloads_stat = QLabel("📥\n0+\nTotal\nDownloads")
        downloads_stat.setAlignment(Qt.AlignCenter)
        downloads_stat.setStyleSheet("font-size: 12px; font-weight: 600; color: #06b6d4; line-height: 1.4;")
        community_stats_layout.addWidget(downloads_stat)
        
        contributions_stat = QLabel("🎁\n0+\nCode\nContributions")
        contributions_stat.setAlignment(Qt.AlignCenter)
        contributions_stat.setStyleSheet("font-size: 12px; font-weight: 600; color: #10b981; line-height: 1.4;")
        community_stats_layout.addWidget(contributions_stat)
        
        layout.addWidget(community_stats_group)
        
        # Become a supporter
        support_group = QGroupBox("💝 Join the Glow Movement!")
        support_layout = QVBoxLayout(support_group)
        
        support_text = QLabel(
            "🚀 Ready to make GlowStatus even more awesome? Here's how you can help:\n\n"
            "💡 **Share Ideas** - Got a brilliant feature idea? We want to hear it!\n"
            "🐛 **Report Bugs** - Help us squash those pesky issues (we'll credit you!)\n"
            "📢 **Spread the Word** - Tell your team, friends, and the world about GlowStatus!\n"
            "🔧 **Contribute Code** - Developers welcome! Check out our GitHub repo\n"
            "❤️ **Be Part of the Community** - Join our Discord for fun chats and support\n"
            "⭐ **Star Us** - A simple GitHub star means the world to us!"
        )
        support_text.setWordWrap(True)
        support_layout.addWidget(support_text)
        
        # Action buttons
        action_buttons_layout = QHBoxLayout()
        action_buttons_layout.addStretch()
        
        join_btn = QPushButton("🎉 Join Discord Community")
        join_btn.setToolTip("Come chat with us! We have cookies! 🍪")
        join_btn.clicked.connect(lambda: self.open_url("https://discord.gg/xtNevM3WuV"))
        action_buttons_layout.addWidget(join_btn)
        
        github_btn = QPushButton("⭐ Star on GitHub")
        github_btn.setToolTip("Give us a star and make our day! ✨")
        github_btn.clicked.connect(lambda: self.open_url("https://github.com/your-repo/glowstatus"))
        action_buttons_layout.addWidget(github_btn)
        
        action_buttons_layout.addStretch()
        support_layout.addLayout(action_buttons_layout)
        
        layout.addWidget(support_group)
        layout.addStretch()
        
        return scroll
    
    def create_oauth_page(self):
        """Create the OAuth configuration page."""
        scroll, page = self.create_scrollable_page()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title = QLabel("🔐 Google Calendar Setup")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        
        # Privacy notice (required for OAuth compliance) - matching original
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
        privacy_notice.setMinimumHeight(50)
        layout.addWidget(privacy_notice)
        
        # OAuth Status
        form_layout = QFormLayout()
        self.oauth_status_label = QLabel("Not configured")
        form_layout.addRow("OAuth Status:", self.oauth_status_label)
        
        # Verification status info - matching original
        verification_info = QLabel(
            'ℹ️ This app uses Google\'s Limited Use policy for calendar data. '
            'Your data is processed securely and never shared with third parties.'
        )
        verification_info.setWordWrap(True)
        verification_info.setStyleSheet("color: #5f6368; font-size: 10px; font-style: italic; margin: 2px 0;")
        form_layout.addRow(verification_info)
        
        # OAuth buttons layout (side by side, centered) - matching original
        oauth_buttons_layout = QHBoxLayout()
        oauth_buttons_layout.addStretch()
        
        # Google Sign-in Button (following Google branding guidelines) - matching original
        self.oauth_btn = QPushButton("Sign in with Google")
        self.oauth_btn.clicked.connect(self.run_oauth_flow)
        
        # Apply Google branding styles
        self.apply_google_button_style(self.oauth_btn)
        oauth_buttons_layout.addWidget(self.oauth_btn)
        
        # Add small spacing between buttons
        oauth_buttons_layout.addSpacing(10)
        
        # Disconnect Button - matching Google's Material Design
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self.disconnect_oauth)
        
        # Style disconnect button to match Google's secondary button design
        self.disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                border: 1px solid #dadce0;
                border-radius: 4px;
                color: #3c4043;
                font-family: 'Roboto', -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 14px;
                font-weight: 500;
                padding: 9px 16px;
                min-height: 36px;
                min-width: 64px;
                outline: none;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
                border-color: #dadce0;
            }
            QPushButton:focus {
                background-color: #ffffff;
                border-color: #4285f4;
                outline: 2px solid #4285f4;
                outline-offset: 2px;
            }
            QPushButton:pressed {
                background-color: #f1f3f4;
            }
            QPushButton:disabled {
                background-color: #f8f9fa;
                color: #9aa0a6;
                border-color: #f8f9fa;
            }
        """)
        oauth_buttons_layout.addWidget(self.disconnect_btn)
        oauth_buttons_layout.addStretch()
        
        form_layout.addRow(oauth_buttons_layout)
        
        # Google Calendar ID (display only) - matching original
        self.google_calendar_id_label = QLabel("Not authenticated")
        form_layout.addRow("Authenticated as:", self.google_calendar_id_label)

        layout.addLayout(form_layout)
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
        
        # Device Model (from original config_ui.py)
        self.govee_device_model_edit = QLineEdit()
        self.govee_device_model_edit.setPlaceholderText("Enter your device model (e.g., H6159)")
        govee_layout.addRow("Device Model:", self.govee_device_model_edit)
        
        # Test connection button
        self.test_govee_btn = QPushButton("🔍 Test Connection")
        self.test_govee_btn.clicked.connect(self.test_govee_connection)
        govee_layout.addRow("", self.test_govee_btn)
        
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
        
        self.calendar_dropdown = QComboBox()
        calendar_layout.addRow("Primary Calendar:", self.calendar_dropdown)
        
        refresh_btn = QPushButton("🔄 Refresh Calendars")
        refresh_btn.clicked.connect(self.refresh_calendars)
        calendar_layout.addRow("", refresh_btn)
        
        layout.addWidget(calendar_group)
        
        # Sync settings
        sync_group = QGroupBox("Synchronization")
        sync_layout = QFormLayout(sync_group)
        
        self.disable_sync_checkbox = QCheckBox("Disable calendar synchronization")
        self.disable_sync_checkbox.setEnabled(True)
        self.disable_sync_checkbox.setCheckable(True)
        self.disable_sync_checkbox.setFocusPolicy(Qt.StrongFocus)
        self.disable_sync_checkbox.setMouseTracking(True)
        self.disable_sync_checkbox.stateChanged.connect(self.on_form_changed)
        sync_layout.addRow(self.disable_sync_checkbox)
        
        self.sync_interval_spinbox = QSpinBox()
        self.sync_interval_spinbox.setRange(10, 3600)
        self.sync_interval_spinbox.setSuffix(" seconds")
        self.sync_interval_spinbox.setEnabled(True)
        self.sync_interval_spinbox.valueChanged.connect(self.on_form_changed)
        sync_layout.addRow("Refresh Interval:", self.sync_interval_spinbox)
        
        layout.addWidget(sync_group)
        
        # Additional settings
        additional_group = QGroupBox("Additional Settings")
        additional_layout = QVBoxLayout(additional_group)
        
        self.power_off_available_checkbox = QCheckBox("Turn light off when available")
        self.power_off_available_checkbox.setEnabled(True)
        self.power_off_available_checkbox.setCheckable(True)
        self.power_off_available_checkbox.setFocusPolicy(Qt.StrongFocus)
        self.power_off_available_checkbox.setMouseTracking(True)
        self.power_off_available_checkbox.stateChanged.connect(self.on_form_changed)
        additional_layout.addWidget(self.power_off_available_checkbox)
        
        self.off_for_unknown_checkbox = QCheckBox("Turn light off for unknown status")
        self.off_for_unknown_checkbox.setEnabled(True)
        self.off_for_unknown_checkbox.setCheckable(True)
        self.off_for_unknown_checkbox.setFocusPolicy(Qt.StrongFocus)
        self.off_for_unknown_checkbox.setMouseTracking(True)
        self.off_for_unknown_checkbox.stateChanged.connect(self.on_form_changed)
        additional_layout.addWidget(self.off_for_unknown_checkbox)
        
        self.disable_light_control_checkbox = QCheckBox("Disable light control")
        self.disable_light_control_checkbox.setEnabled(True)
        self.disable_light_control_checkbox.setCheckable(True)
        self.disable_light_control_checkbox.setFocusPolicy(Qt.StrongFocus)
        self.disable_light_control_checkbox.setMouseTracking(True)
        self.disable_light_control_checkbox.stateChanged.connect(self.on_form_changed)
        additional_layout.addWidget(self.disable_light_control_checkbox)
        
        layout.addWidget(additional_group)
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
        self.status_colors_table.setHorizontalHeaderLabels(["Status", "Color (R,G,B)", "Power Off"])
        self.status_colors_table.horizontalHeader().setStretchLastSection(True)
        
        # Set minimum height to accommodate 15-20 rows without scrolling
        # Row height is typically ~30px + header ~40px + some padding
        self.status_colors_table.setMinimumHeight(550)  # Enough for ~16-17 rows
        
        # Configure table behavior
        self.status_colors_table.setAlternatingRowColors(True)
        self.status_colors_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.status_colors_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.status_colors_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
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
        
        # Advanced options
        advanced_group = QGroupBox("Advanced")
        advanced_layout = QVBoxLayout(advanced_group)
        
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
        
        title = QLabel("💬 Discord Community - Where the Magic Happens! ✨")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)
        
        # Welcome section with fun intro
        welcome_group = QGroupBox("🎉 Welcome to the GlowStatus Family!")
        welcome_layout = QVBoxLayout(welcome_group)
        
        welcome_description = QLabel(
            "🚀 Ready to join the most awesome status-lighting community on the internet? "
            "Our Discord server is buzzing with friendly developers, creative users, and lighting enthusiasts "
            "who are all passionate about making remote work more visual and fun! 🌈💡\n\n"
            "🎯 Whether you're a coding wizard, a lighting newbie, or somewhere in between, "
            "you'll find your tribe here. We're all about helping each other glow brighter! ✨"
        )
        welcome_description.setWordWrap(True)
        welcome_layout.addWidget(welcome_description)
        
        # Big Discord invite button
        big_discord_btn = QPushButton("🎊 JOIN THE DISCORD PARTY! 🎊")
        big_discord_btn.setToolTip("Click to join our GlowStatus community! 🚀")
        big_discord_btn.clicked.connect(lambda: self.open_url("https://discord.gg/xtNevM3WuV"))
        big_discord_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #8b5cf6, stop:0.5 #06b6d4, stop:1 #10b981);
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 16px 32px;
                border-radius: 12px;
                border: none;
                min-height: 24px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #7c3aed, stop:0.5 #0891b2, stop:1 #059669);
            }
        """)
        welcome_layout.addWidget(big_discord_btn)
        
        layout.addWidget(welcome_group)
        
        # What you'll find section
        channels_group = QGroupBox("🏠 What You'll Find in Our Server")
        channels_layout = QVBoxLayout(channels_group)
        
        channels_text = QLabel(
            "📋 **#welcome** - Get started and see project links 🌟\n"
            "📜 **#rules** - Community code of conduct and guidelines �\n"
            "📢 **#announcements** - Latest releases and roadmap updates 🗞️\n"
            "🆘 **#setup-help** - Troubleshooting and installation questions 🛠️\n"
            "💡 **#feature-requests** - Share your brilliant ideas with the team 🧠⚡\n"
            "� **#integration-requests** - Request support for new device brands �\n"
            "⚙️ **#dev-updates** - Automatic updates from our GitHub repositories 🤖\n"
            "🖥️ **#cli-version-v1** - Support for the CLI version �\n"
            "� **#app-version-v2** - Support for the GUI installer version 🎨\n"
            "🔌 **#api-dev** - API endpoint discussions for developers �\n"
            "� **#general** - Casual conversations and community chit-chat �\n"
            "📸 **#show-your-glow** - Show off your amazing lighting setups! �✨"
        )
        channels_text.setWordWrap(True)
        channels_layout.addWidget(channels_text)
        
        layout.addWidget(channels_group)
        
        # Community perks
        perks_group = QGroupBox("🎁 Community Perks & Benefits")
        perks_layout = QVBoxLayout(perks_group)
        
        perks_text = QLabel(
            "⚡ **Lightning-fast support** - Get help from real humans, not bots! 🏃‍♂️💨\n"
            "🎯 **Direct access to developers** - Chat with the people building GlowStatus! 👨‍💻\n"
            "🔮 **Early access to features** - Be the first to try cool new stuff! 🚀\n"
            "🏆 **Special contributor roles** - Get recognized for your awesome contributions! 🌟\n"
            "🎉 **Fun events and contests** - Win prizes and show off your creativity! 🏅\n"
            "📚 **Exclusive tips and tricks** - Learn pro-level GlowStatus techniques! 🎓\n"
            "💖 **Make lasting friendships** - Connect with like-minded remote workers! 👥"
        )
        perks_text.setWordWrap(True)
        perks_layout.addWidget(perks_text)
        
        layout.addWidget(perks_group)
        
        # Bottom action section
        action_group = QGroupBox("🚀 Ready to Glow with Us?")
        action_layout = QVBoxLayout(action_group)
        
        action_text = QLabel(
            "🌟 Don't just take our word for it - come see what all the excitement is about! "
            "Our community is growing every day, and we'd love to have you as part of the family. "
            "Click that shiny button below and let's start glowing together! 💫🎊"
        )
        action_text.setWordWrap(True)
        action_text.setAlignment(Qt.AlignCenter)
        action_layout.addWidget(action_text)
        
        # Final call-to-action button
        final_btn = QPushButton("💬 Join Discord Now - Let's Glow! ✨")
        final_btn.setToolTip("Your lighting journey starts here! 🌈")
        final_btn.clicked.connect(lambda: self.open_url("https://discord.gg/xtNevM3WuV"))
        action_layout.addWidget(final_btn)
        
        layout.addWidget(action_group)
        layout.addStretch()
        
        return scroll
    
    def show_message(self, message_type, title, text, buttons=QMessageBox.Ok):
        """Show a properly branded message box."""
        msg = QMessageBox(self)
        msg.setWindowTitle(f"GlowStatus - {title}")
        msg.setText(text)
        msg.setStandardButtons(buttons)
        
        # Set icon based on message type
        if message_type == "information":
            msg.setIcon(QMessageBox.Information)
        elif message_type == "warning":
            msg.setIcon(QMessageBox.Warning)
        elif message_type == "error":
            msg.setIcon(QMessageBox.Critical)
        elif message_type == "question":
            msg.setIcon(QMessageBox.Question)
        
        # Try to set window icon
        try:
            icon_path = resource_path("img/GlowStatus.png")
            if os.path.exists(icon_path):
                msg.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass
        
        return msg.exec()
    
    def change_page(self, index):
        """Change the current page based on sidebar selection."""
        if index >= 0 and hasattr(self, 'content_stack'):
            self.content_stack.setCurrentIndex(index)
            
            # Update page title
            if hasattr(self, 'page_title'):
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
                api_key = keyring.get_password("GlowStatus", "GOVEE_API_KEY")
                if api_key:
                    self.govee_api_key_edit.setText(api_key)
            except (NoKeyringError, Exception):
                pass
            
            self.govee_device_id_edit.setText(self.config.get("GOVEE_DEVICE_ID", ""))
            self.govee_device_model_edit.setText(self.config.get("GOVEE_DEVICE_MODEL", ""))
        
        # Load calendar settings
        if hasattr(self, 'disable_sync_checkbox'):
            self.disable_sync_checkbox.setChecked(self.config.get("DISABLE_CALENDAR_SYNC", False))
            self.sync_interval_spinbox.setValue(self.config.get("REFRESH_INTERVAL", 15))
            
        # Load additional settings
        if hasattr(self, 'power_off_available_checkbox'):
            self.power_off_available_checkbox.setChecked(self.config.get("POWER_OFF_WHEN_AVAILABLE", True))
            
        if hasattr(self, 'off_for_unknown_checkbox'):
            self.off_for_unknown_checkbox.setChecked(self.config.get("OFF_FOR_UNKNOWN_STATUS", True))
            
        if hasattr(self, 'disable_light_control_checkbox'):
            self.disable_light_control_checkbox.setChecked(self.config.get("DISABLE_LIGHT_CONTROL", False))
        
        # Load status colors
        self.populate_status_colors_table()
        
        # Load calendars if OAuth is connected
        self.refresh_calendars()
        
        # Ensure calendar checkboxes are interactive
        self.ensure_calendar_checkboxes_interactive()
    
    def update_oauth_status(self):
        """Update OAuth connection status display."""
        if hasattr(self, 'oauth_status_label'):
            if os.path.exists(TOKEN_PATH):
                self.oauth_status_label.setText("✅ Connected to Google Calendar")
                self.oauth_status_label.setStyleSheet("color: green;")
                self.oauth_btn.setText("🔄 Reconnect")
                self.disconnect_btn.setEnabled(True)
                
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
                                    self.google_calendar_id_label.setText(f"Account: {email}")
                                    break
                except Exception:
                    self.google_calendar_id_label.setText("Account: Connected")
            else:
                self.oauth_status_label.setText("❌ Not connected")
                self.oauth_status_label.setStyleSheet("color: red;")
                self.oauth_btn.setText("🔑 Connect with Google")
                self.disconnect_btn.setEnabled(False)
                self.google_calendar_id_label.setText("")
    
    def run_oauth_flow(self):
        """Start the OAuth authentication flow."""
        if self.oauth_worker and self.oauth_worker.isRunning():
            QMessageBox.information(self, "GlowStatus", "OAuth process is already running.")
            return
        
        # Show progress and disable button
        if hasattr(self, 'oauth_progress'):
            self.oauth_progress.setVisible(True)
            self.oauth_progress.setRange(0, 0)  # Indeterminate progress
        self.oauth_btn.setEnabled(False)
        self.oauth_btn.setText("Connecting...")
        
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
        if hasattr(self, 'calendar_dropdown'):
            self.calendar_dropdown.clear()
            for cal in calendars:
                summary = cal.get("summary", "")
                cal_id = cal.get("id", "")
                display = f"{summary} ({cal_id})" if summary else cal_id
                self.calendar_dropdown.addItem(display, cal_id)
        
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
        if hasattr(self, 'oauth_progress'):
            self.oauth_progress.setVisible(False)
        self.oauth_btn.setEnabled(True)
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
                if hasattr(self, 'calendar_dropdown'):
                    self.calendar_dropdown.clear()
                
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
                
                if hasattr(self, 'calendar_dropdown'):
                    current_selection = self.calendar_dropdown.currentData()
                    self.calendar_dropdown.clear()
                    
                    for cal in calendars:
                        summary = cal.get("summary", "")
                        cal_id = cal.get("id", "")
                        display = f"{summary} ({cal_id})" if summary else cal_id
                        self.calendar_dropdown.addItem(display, cal_id)
                    
                    # Restore previous selection if possible
                    if current_selection:
                        index = self.calendar_dropdown.findData(current_selection)
                        if index >= 0:
                            self.calendar_dropdown.setCurrentIndex(index)
                            
        except Exception as e:
            logger.warning(f"Failed to refresh calendars: {e}")
    
    def test_govee_connection(self):
        """Test Govee API connection with toggle behavior."""
        if self._govee_test_active:
            # End the test - turn off light and reset button
            self._end_govee_test()
            return
        
        # Start the test
        api_key = self.govee_api_key_edit.text().strip()
        device_id = self.govee_device_id_edit.text().strip()
        device_model = self.govee_device_model_edit.text().strip() or "H6001"
        
        if not api_key or not device_id:
            QMessageBox.warning(
                self, 
                "GlowStatus", 
                "Please enter both API key and device ID."
            )
            return
        
        # Test connection by attempting to turn on light
        try:
            from govee_controller import GoveeController
            
            # Create a temporary controller for testing
            controller = GoveeController(api_key, device_id, device_model)
            
            # Turn on green light to indicate test is active
            controller.set_color(0, 255, 0)  # Green
            
            # Store the controller as an instance variable to prevent garbage collection
            self._test_controller = controller
            self._govee_test_active = True
            
            # Update button to show "End Test" option
            self.test_govee_btn.setText("🛑 End Test")
            
        except Exception as e:
            QMessageBox.warning(
                self, 
                "GlowStatus - Connection Test Failed", 
                f"❌ Failed to connect to Govee device:\n{str(e)}\n\n"
                "Please check:\n"
                "• API key is correct\n"
                "• Device ID is correct\n"
                "• Device model is correct\n"
                "• Device is online and connected to WiFi"
            )
    
    def _end_govee_test(self):
        """End the Govee test and turn off the light."""
        try:
            if hasattr(self, '_test_controller') and self._test_controller:
                self._test_controller.set_power("off")
                # Clean up the reference
                self._test_controller = None
        except Exception as e:
            logger.warning(f"Failed to turn off test light: {e}")
        finally:
            # Reset test state and button text
            self._govee_test_active = False
            self.test_govee_btn.setText("🔍 Test Connection")

    
    def populate_status_colors_table(self):
        """Populate the status colors table with current settings."""
        if not hasattr(self, 'status_colors_table'):
            return
        
        status_color_map = self.config.get("STATUS_COLOR_MAP", {})
        
        # If the status color map is empty, initialize with defaults
        if not status_color_map:
            status_color_map = {
                "in_meeting": {"color": "255,0,0", "power_off": False},
                "focus": {"color": "0,0,255", "power_off": False}, 
                "available": {"color": "0,255,0", "power_off": True},
                "lunch": {"color": "0,255,0", "power_off": True},
                "offline": {"color": "128,128,128", "power_off": False}
            }
            self.config["STATUS_COLOR_MAP"] = status_color_map
        
        self.status_colors_table.setRowCount(len(status_color_map))
        
        for row, (status, entry) in enumerate(status_color_map.items()):
            # Status name
            status_item = QTableWidgetItem(status)
            status_item.setTextAlignment(Qt.AlignCenter)
            self.status_colors_table.setItem(row, 0, status_item)
            
            # Color (R,G,B format)
            color = entry.get("color", "255,255,255")
            color_item = QTableWidgetItem(color)
            color_item.setTextAlignment(Qt.AlignCenter)
            self.status_colors_table.setItem(row, 1, color_item)
            
            # Power off checkbox
            power_off_checkbox = QCheckBox()
            power_off_checkbox.setChecked(entry.get("power_off", False))
            power_off_checkbox.stateChanged.connect(self.on_form_changed)
            self.status_colors_table.setCellWidget(row, 2, power_off_checkbox)
            
        # Connect double-click to color picker
        self.status_colors_table.cellDoubleClicked.connect(self.open_color_picker)
    
    def on_form_changed(self):
        """Called when any form field changes."""
        self.form_dirty = True
        self.update_save_status()
    
    def update_save_status(self):
        """Update the save status label."""
        if self.form_dirty:
            self.save_status_label.setText("Unsaved Changes")
            self.save_status_label.setStyleSheet("color: #d93025; font-size: 12px; font-weight: bold; margin: 5px 0;")
        else:
            self.save_status_label.setText("All Changes Saved")
            self.save_status_label.setStyleSheet("color: #137333; font-size: 12px; font-weight: bold; margin: 5px 0;")
    
    def open_color_picker(self, row, col):
        """Open color picker when double-clicking on color column."""
        if col == 1:  # Color column
            current_item = self.status_colors_table.item(row, col)
            current_color = current_item.text() if current_item else "255,255,255"
            
            # Convert R,G,B to QColor
            try:
                r, g, b = map(int, current_color.split(","))
                initial_color = QColor(r, g, b)
            except:
                initial_color = QColor(255, 255, 255)
            
            color = QColorDialog.getColor(initial_color, self, "Choose Color")
            if color.isValid():
                rgb_str = f"{color.red()},{color.green()},{color.blue()}"
                self.status_colors_table.setItem(row, col, QTableWidgetItem(rgb_str))
                self.on_form_changed()
    
    def change_status_color(self, row):
        """Change the color for a status (legacy method for compatibility)."""
        self.open_color_picker(row, 1)
    
    def add_status_row(self, status="", color="255,255,255", power_off=False):
        """Add a new status row to the table."""
        row = self.status_colors_table.rowCount()
        self.status_colors_table.insertRow(row)
        
        # Status name
        status_item = QTableWidgetItem(status)
        status_item.setTextAlignment(Qt.AlignCenter)
        self.status_colors_table.setItem(row, 0, status_item)
        
        # Color (R,G,B)
        color_item = QTableWidgetItem(color)
        color_item.setTextAlignment(Qt.AlignCenter)
        self.status_colors_table.setItem(row, 1, color_item)
        
        # Power off checkbox
        power_off_checkbox = QCheckBox()
        power_off_checkbox.setChecked(power_off)
        power_off_checkbox.stateChanged.connect(self.on_form_changed)
        self.status_colors_table.setCellWidget(row, 2, power_off_checkbox)
    
    def add_custom_status(self):
        """Add a custom status."""
        # Add a new empty row for user to fill in
        self.add_status_row("new_status", "255,255,255", False)
        
        # Select the new row for editing
        new_row = self.status_colors_table.rowCount() - 1
        self.status_colors_table.setCurrentCell(new_row, 0)
        self.status_colors_table.editItem(self.status_colors_table.item(new_row, 0))
    
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
                    self.status_colors_table.removeRow(current_row)
                    self.on_form_changed()
    
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
            self.config["STATUS_COLOR_MAP"] = {
                "in_meeting": {"color": "255,0,0", "power_off": False},
                "focus": {"color": "0,0,255", "power_off": False},
                "available": {"color": "0,255,0", "power_off": True},
                "lunch": {"color": "0,255,0", "power_off": True},
                "offline": {"color": "128,128,128", "power_off": False}
            }
            self.populate_status_colors_table()
    
    def view_logs(self):
        """Placeholder for log viewer - not implemented in original."""
        QMessageBox.information(
            self, 
            "GlowStatus", 
            "Log viewing functionality was not implemented in the original config_ui.py"
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
                keyring.delete_password("GlowStatus", "GOVEE_API_KEY")
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
        self.form_dirty = False
        self.update_save_status()
        self.accept()
    
    def save_all_settings(self):
        """Save all settings from UI to configuration."""
        # Save Govee settings
        if hasattr(self, 'govee_api_key_edit'):
            api_key = self.govee_api_key_edit.text().strip()
            if api_key:
                try:
                    keyring.set_password("GlowStatus", "GOVEE_API_KEY", api_key)
                except Exception as e:
                    logger.warning(f"Failed to save Govee API key: {e}")
            
            self.config["GOVEE_DEVICE_ID"] = self.govee_device_id_edit.text().strip()
            self.config["GOVEE_DEVICE_MODEL"] = self.govee_device_model_edit.text().strip()
        
        # Save calendar settings
        if hasattr(self, 'disable_sync_checkbox'):
            self.config["DISABLE_CALENDAR_SYNC"] = self.disable_sync_checkbox.isChecked()
            self.config["REFRESH_INTERVAL"] = self.sync_interval_spinbox.value()
            
        # Save additional settings
        if hasattr(self, 'power_off_available_checkbox'):
            self.config["POWER_OFF_WHEN_AVAILABLE"] = self.power_off_available_checkbox.isChecked()
            
        if hasattr(self, 'off_for_unknown_checkbox'):
            self.config["OFF_FOR_UNKNOWN_STATUS"] = self.off_for_unknown_checkbox.isChecked()
            
        if hasattr(self, 'disable_light_control_checkbox'):
            self.config["DISABLE_LIGHT_CONTROL"] = self.disable_light_control_checkbox.isChecked()
        
        # Save selected calendar
        if hasattr(self, 'calendar_dropdown'):
            selected_cal = self.calendar_dropdown.currentData()
            if selected_cal:
                self.config["SELECTED_CALENDAR_ID"] = selected_cal
        
        # Save status color map
        if hasattr(self, 'status_colors_table'):
            status_color_map = {}
            for row in range(self.status_colors_table.rowCount()):
                status_item = self.status_colors_table.item(row, 0)
                color_item = self.status_colors_table.item(row, 1)
                power_widget = self.status_colors_table.cellWidget(row, 2)
                
                if status_item and color_item and power_widget:
                    status = status_item.text()
                    color = color_item.text()
                    power_off = power_widget.isChecked()
                    status_color_map[status] = {"color": color, "power_off": power_off}
            
            self.config["STATUS_COLOR_MAP"] = status_color_map
        
        # Ensure fixed tray icon is set
        self.config["TRAY_ICON"] = "GlowStatus_tray_tp.png"
        
        # Save general options (only ones that actually exist)
        # Note: These were not in the original config_ui.py, so we don't save them
        
        # Save configuration
        save_config(self.config)
        logger.info("All settings saved successfully")
        
        # Update form status
        self.form_dirty = False
        self.update_save_status()
        
        # Show success message to user
        QMessageBox.information(
            self, 
            "GlowStatus", 
            "✅ Settings saved successfully!\n\n"
            "Your settings have been saved and will take effect immediately."
        )
    
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
        """Apply a subtle and elegant dark theme to the window."""
        self.setStyleSheet("""
            /* Main window and dialog styling */
            QDialog {
                background-color: #181818;
                color: #ebebeb;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                font-size: 13px;
            }
            
            QWidget {
                background-color: #181818;
                color: #ebebeb;
            }
            
            /* Sidebar navigation */
            QListWidget#sidebar {
                background-color: #1f1f1f;
                color: #ebebeb;
                border: none;
                border-radius: 16px;
                font-size: 14px;
                padding: 16px 12px;
                outline: none;
                font-weight: 500;
            }
            
            QListWidget#sidebar::item {
                padding: 18px 24px;
                border-radius: 12px;
                margin: 3px 6px;
                color: #b5b5b5;
                border: none;
                background-color: transparent;
            }
            
            QListWidget#sidebar::item:selected {
                background-color: rgba(56, 189, 248, 0.1);
                color: #38bdf8;
                font-weight: 600;
                border: 1px solid rgba(56, 189, 248, 0.2);
            }
            
            QListWidget#sidebar::item:hover:!selected {
                background-color: rgba(255, 255, 255, 0.03);
                color: #ebebeb;
            }
            
            /* Page and section titles */
            QLabel#pageTitle {
                font-size: 28px;
                font-weight: 300;
                color: #ffffff;
                padding: 36px 40px 24px 40px;
                background-color: transparent;
                border: none;
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            }
            
            QLabel#sectionTitle {
                font-size: 18px;
                font-weight: 600;
                color: #38bdf8;
                margin-bottom: 24px;
                background-color: transparent;
            }
            
            /* About page specific styling */
            QLabel#aboutTitle {
                font-size: 36px;
                font-weight: 200;
                color: #ffffff;
                margin: 28px 0;
                background-color: transparent;
            }
            
            QLabel#aboutDescription {
                font-size: 15px;
                color: #cccccc;
                line-height: 1.7;
                margin: 28px 0;
                background-color: rgba(255, 255, 255, 0.015);
                padding: 32px;
                border: 1px solid rgba(255, 255, 255, 0.04);
                border-radius: 16px;
            }
            
            QLabel#versionInfo {
                font-size: 13px;
                color: #909090;
                margin: 20px 0;
                background-color: transparent;
                font-weight: 500;
            }
            
            /* Group boxes for organizing content */
            QGroupBox {
                font-weight: 500;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 16px;
                margin-top: 20px;
                padding-top: 24px;
                background-color: rgba(255, 255, 255, 0.015);
                color: #ffffff;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                padding: 6px 16px;
                color: #38bdf8;
                background-color: #181818;
                font-weight: 600;
                border-radius: 8px;
            }
            
            /* Button styling */
            QPushButton {
                background-color: rgba(255, 255, 255, 0.05);
                color: #ebebeb;
                border: 1px solid rgba(255, 255, 255, 0.1);
                padding: 12px 24px;
                border-radius: 10px;
                font-weight: 500;
                min-width: 100px;
                font-size: 13px;
            }
            
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.08);
                border-color: rgba(255, 255, 255, 0.18);
            }
            
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.03);
                border-color: rgba(255, 255, 255, 0.06);
            }
            
            QPushButton:disabled {
                background-color: rgba(255, 255, 255, 0.015);
                color: #666666;
                border-color: rgba(255, 255, 255, 0.03);
            }
            
            /* Primary action buttons */
            QPushButton#saveButton {
                background-color: #38bdf8;
                color: #181818;
                border: none;
                font-weight: 600;
            }
            
            QPushButton#saveButton:hover {
                background-color: #0ea5e9;
            }
            
            QPushButton#saveButton:pressed {
                background-color: #0284c7;
            }
            
            /* Input fields */
            QLineEdit, QSpinBox {
                padding: 14px 18px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                background-color: rgba(255, 255, 255, 0.03);
                color: #ebebeb;
                font-size: 13px;
                selection-background-color: #38bdf8;
                min-height: 18px;
            }
            
            QLineEdit:focus, QSpinBox:focus {
                border-color: #38bdf8;
                background-color: rgba(56, 189, 248, 0.05);
            }
            
            QLineEdit:hover, QSpinBox:hover {
                border-color: rgba(255, 255, 255, 0.18);
            }
            
            /* Dropdown menus */
            QComboBox {
                padding: 14px 18px;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
                background-color: rgba(255, 255, 255, 0.03);
                color: #ebebeb;
                font-size: 13px;
                min-width: 150px;
                min-height: 18px;
            }
            
            QComboBox:focus {
                border-color: #38bdf8;
                background-color: rgba(56, 189, 248, 0.05);
            }
            
            QComboBox:hover {
                border-color: rgba(255, 255, 255, 0.18);
            }
            
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 28px;
                border-left: 1px solid rgba(255, 255, 255, 0.1);
                background-color: rgba(255, 255, 255, 0.03);
                border-top-right-radius: 10px;
                border-bottom-right-radius: 10px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #b5b5b5;
                margin-right: 10px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #272727;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                selection-background-color: #38bdf8;
                color: #ebebeb;
                outline: none;
                padding: 6px;
            }
            
            QComboBox QAbstractItemView::item {
                padding: 10px 14px;
                border-radius: 6px;
                margin: 2px;
            }
            
            /* Tables */
                       QTableWidget {
                gridline-color: rgba(255, 255, 255, 0.04);
                background-color: rgba(255, 255, 255, 0.015);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 16px;
                color: #ebebeb;
                selection-background-color: rgba(56, 189, 248, 0.15);
                font-size: 13px;
            }
            
            QTableWidget::item {
                padding: 14px 10px;
                border-bottom: 1px solid rgba(255, 255, 255,  0.03);
                background-color: transparent;
            }
            
            QTableWidget::item:selected {
                background-color: rgba(56, 189, 248, 0.12);
                color: #38bdf8;
            }
            
            QTableWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.03);
            }
            
            QHeaderView::section {
                background-color: rgba(255, 255, 255, 0.03);
                color: #cccccc;
                padding: 18px 10px;
                border: none;
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
                font-weight: 600;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.8px;
            }
            
            /* Checkboxes */
            QCheckBox {
                color: #ebebeb;
                font-size: 13px;
                spacing: 14px;
                font-weight: 500;
            }
            
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.18);
                background-color: rgba(255, 255, 255, 0.03);
            }
            
            QCheckBox::indicator:checked {
                background-color: #38bdf8;
                border-color: #38bdf8;
                image: url(data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Cpath fill='%23ffffff' d='M13.854 3.646a.5.5 0 0 1 0 .708l-7 7a.5.5 0 0 1-.708 0l-3.5-3.5a.5.5 0 1 1 .708-.708L6.5 10.293l6.646-6.647a.5.5 0 0 1 .708 0z'/%3E%3C/svg%3E);
            }
            
            QCheckBox::indicator:hover {
                border-color: #38bdf8;
                background-color: rgba(56, 189, 248, 0.06);
            }
            
            /* Scroll areas and scrollbars */
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            
            QScrollBar:vertical {
                background-color: transparent;
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background-color: rgba(255, 255, 255, 0.12);
                border-radius: 6px;
                min-height: 40px;
                margin: 3px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
            
            /* Progress bars */
            QProgressBar {
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                text-align: center;
                background-color: rgba(255, 255, 255, 0.03);
                color: #ebebeb;
                font-weight: 500;
                font-size: 12px;
            }
            
            QProgressBar::chunk {
                background-color: #38bdf8;
                border-radius: 7px;
            }
            
            /* Labels and text */
            QLabel {
                color: #ebebeb;
                background-color: transparent;
            }
            
            QFrame {
                background-color: transparent;
                border: none;
            }
            
            /* Form layout styling */
            QFormLayout QLabel {
                color: #cccccc;
                font-weight: 500;
                margin-bottom: 6px;
            }
            
            /* Button layout spacing */
            QHBoxLayout QPushButton {
                margin: 0px 8px;
            }
            
            /* Splitter handle */
            QSplitter::handle {
                background-color: rgba(255, 255, 255, 0.04);
                width: 1px;
            }
            
            QSplitter::handle:hover {
                background-color: rgba(56, 189, 248, 0.3);
            }
        """)

    def apply_google_button_style(self, button):
        """Apply strict Google branding guidelines to OAuth button."""
        try:
            google_logo_path = resource_path("img/google_logo.png")
            if os.path.exists(google_logo_path):
                button.setIcon(QIcon(google_logo_path))
                button.setIconSize(QSize(18, 18))
        except Exception:
            pass
        
        # Following Google's Identity Branding Guidelines exactly
        # Reference: https://developers.google.com/identity/branding-guidelines
        button.setStyleSheet("""
            QPushButton {
                background-color: #4285f4;
                border: none;
                border-radius: 4px;
                color: #ffffff;
                font-family: 'Roboto', -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 14px;
                font-weight: 500;
                padding: 10px 12px;
                min-height: 36px;
                min-width: 120px;
                text-align: left;
                outline: none;
            }
            QPushButton:hover {
                background-color: #357ae8;
            }
            QPushButton:focus {
                background-color: #4285f4;
                outline: 2px solid #4285f4;
                outline-offset: 2px;
            }
            QPushButton:pressed {
                background-color: #1a73e8;
            }
            QPushButton:disabled {
                background-color: rgba(255, 255, 255, 0.12);
                color: rgba(255, 255, 255, 0.38);
            }
        """)
    
    def closeEvent(self, event):
        """Handle window close event - check for unsaved changes and clean up any active Govee test."""
        if self.form_dirty:
            reply = QMessageBox.question(
                self,
                "GlowStatus - Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                self.save_all_settings()
                self.form_dirty = False
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
                return
        
        # Clean up active Govee test
        if self._govee_test_active:
            self._end_govee_test()
        
        event.accept()

    def ensure_calendar_checkboxes_interactive(self):
        """Ensure all calendar page checkboxes are interactive and properly connected."""
        calendar_checkboxes = [
            ('disable_sync_checkbox', "Disable calendar synchronization"),
            ('power_off_available_checkbox', "Turn light off when available"),
            ('off_for_unknown_checkbox', "Turn light off for unknown status"),
            ('disable_light_control_checkbox', "Disable light control")
        ]
        
        for checkbox_attr, expected_text in calendar_checkboxes:
            if hasattr(self, checkbox_attr):
                checkbox = getattr(self, checkbox_attr)
                # Force enable and ensure properties are set
                checkbox.setEnabled(True)
                checkbox.setCheckable(True)
                checkbox.setFocusPolicy(Qt.StrongFocus)
                checkbox.setMouseTracking(True)
                
                # Disconnect and reconnect signal to ensure it's connected
                try:
                    checkbox.stateChanged.disconnect()
                except:
                    pass  # No existing connections
                checkbox.stateChanged.connect(self.on_form_changed)
                
                logger.info(f"Calendar checkbox '{expected_text}': enabled={checkbox.isEnabled()}, checkable={checkbox.isCheckable()}")
            else:
                logger.warning(f"Calendar checkbox attribute '{checkbox_attr}' not found")
    
    def on_checkbox_debug_click(self):
        """Debug method to test if checkboxes receive click events."""
        sender = self.sender()
        logger.info(f"DEBUG: Checkbox clicked - {sender.text()}, checked={sender.isChecked()}")
        print(f"DEBUG: Checkbox clicked - {sender.text()}, checked={sender.isChecked()}")
        self.on_form_changed()
    

# Main function for testing
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = SettingsWindow()
    window.show()
    sys.exit(app.exec())
