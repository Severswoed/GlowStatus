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
    
    # Internal developer toggle - set to True to enable experimental accessibility features
    ENABLE_ACCESSIBILITY_TAB = False
    
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
        # Apply GlowStatus dark theme
        self.apply_glowstatus_theme()
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)
        
        # Create horizontal layout for sidebar and content
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)
        
        # Create sidebar navigation
        self.sidebar = QListWidget()
        self.sidebar.setMaximumWidth(220)
        self.sidebar.setMinimumWidth(200)
        self.setup_sidebar()
        
        # Create content area with stacked widget wrapped in scroll area
        content_scroll = QScrollArea()
        content_scroll.setWidgetResizable(True)
        content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        content_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        content_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.content_stack = QStackedWidget()
        self.setup_content_pages()
        
        content_scroll.setWidget(self.content_stack)
        
        # Add widgets to content layout
        content_layout.addWidget(self.sidebar)
        content_layout.addWidget(content_scroll, 1)  # Content takes remaining space
        
        # Create content widget and add to main layout
        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget, 1)  # Takes most space
        
        # Add bottom bar with save status and buttons
        self.create_bottom_bar_horizontal(main_layout)
        
        self.setLayout(main_layout)
        
        # Connect sidebar selection to content switching
        self.sidebar.currentRowChanged.connect(self.content_stack.setCurrentIndex)
        
        # Set default selection
        self.sidebar.setCurrentRow(0)

    def apply_glowstatus_theme(self):
        """Apply GlowStatus color theme to the entire window."""
        # GlowStatus color palette
        glowstatus_style = """
        QWidget {
            background-color: #1a1a1a;
            color: #f8f9fa;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        QMainWindow {
            background-color: #1a1a1a;
        }
        
        QLabel {
            color: #f8f9fa;
            background-color: transparent;
        }
        
        QGroupBox {
            background-color: #2d2d2d;
            border: 2px solid #00d4ff;
            border-radius: 8px;
            font-weight: bold;
            color: #00d4ff;
            margin-top: 10px;
            padding-top: 10px;
        }
        
        QGroupBox::title {
            color: #00d4ff;
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px 0 8px;
        }
        
        QLineEdit, QTextEdit {
            background-color: #2d2d2d;
            border: 2px solid #0099cc;
            border-radius: 6px;
            padding: 8px;
            color: #f8f9fa;
            selection-background-color: #bf40ff;
        }
        
        QLineEdit:focus, QTextEdit:focus {
            border: 2px solid #00d4ff;
            background-color: #3d3d3d;
        }
        
        QComboBox {
            background-color: #2d2d2d;
            border: 2px solid #0099cc;
            border-radius: 6px;
            padding: 8px;
            color: #f8f9fa;
            min-width: 6em;
        }
        
        QComboBox:focus {
            border: 2px solid #00d4ff;
        }
        
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border-left: 1px solid #0099cc;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid #00d4ff;
            margin-right: 6px;
        }
        
        QComboBox QAbstractItemView {
            background-color: #2d2d2d;
            border: 2px solid #00d4ff;
            selection-background-color: #bf40ff;
            color: #f8f9fa;
        }
        
        QCheckBox {
            color: #f8f9fa;
            spacing: 8px;
        }
        
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 2px solid #0099cc;
            border-radius: 3px;
            background-color: #2d2d2d;
        }
        
        QCheckBox::indicator:checked {
            background-color: #00d4ff;
            border: 2px solid #00d4ff;
        }
        
        QSlider::groove:horizontal {
            background-color: #2d2d2d;
            height: 6px;
            border-radius: 3px;
        }
        
        QSlider::handle:horizontal {
            background-color: #00d4ff;
            border: 2px solid #00d4ff;
            width: 18px;
            margin: -6px 0;
            border-radius: 9px;
        }
        
        QSlider::handle:horizontal:hover {
            background-color: #bf40ff;
            border: 2px solid #bf40ff;
        }
        
        QSpinBox {
            background-color: #2d2d2d;
            border: 2px solid #0099cc;
            border-radius: 6px;
            padding: 6px;
            color: #f8f9fa;
        }
        
        QSpinBox:focus {
            border: 2px solid #00d4ff;
        }
        
        QTextBrowser {
            background-color: #2d2d2d;
            border: 2px solid #0099cc;
            border-radius: 6px;
            color: #f8f9fa;
            padding: 10px;
        }
        
        QScrollArea {
            background-color: transparent;
            border: none;
        }
        
        QScrollBar:vertical {
            background-color: #2d2d2d;
            width: 16px;
            border-radius: 8px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #00d4ff;
            border-radius: 6px;
            min-height: 20px;
            margin: 2px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #bf40ff;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QScrollBar:horizontal {
            background-color: #2d2d2d;
            height: 16px;
            border-radius: 8px;
        }
        
        QScrollBar::handle:horizontal {
            background-color: #00d4ff;
            border-radius: 6px;
            min-width: 20px;
            margin: 2px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background-color: #bf40ff;
        }
        
        QTabWidget::pane {
            border: 2px solid #0099cc;
            background-color: #2d2d2d;
            border-radius: 6px;
        }
        
        QTabBar::tab {
            background-color: #2d2d2d;
            border: 2px solid #0099cc;
            padding: 8px 16px;
            margin-right: 2px;
            border-radius: 6px 6px 0 0;
            color: #f8f9fa;
        }
        
        QTabBar::tab:selected {
            background-color: #00d4ff;
            color: #1a1a1a;
            border-bottom: 2px solid #00d4ff;
        }
        
        QTabBar::tab:hover {
            background-color: #bf40ff;
            color: #f8f9fa;
        }
        """
        self.setStyleSheet(glowstatus_style)

    def setup_sidebar(self):
        """Set up the sidebar navigation with GlowStatus theming."""
        self.sidebar.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                border: 2px solid #00d4ff;
                border-radius: 8px;
                outline: none;
                font-size: 14px;
                font-weight: 500;
            }
            QListWidget::item {
                padding: 15px 20px;
                border-bottom: 1px solid #3d3d3d;
                color: #f8f9fa;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #00d4ff, stop:1 #bf40ff);
                color: #1a1a1a;
                font-weight: bold;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
                color: #00d4ff;
            }
            QListWidget::item:selected:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #bf40ff, stop:1 #00d4ff);
                color: #1a1a1a;
            }
        """)
        
        # Add navigation items with better icons
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
        
        # Note: Accessibility section is hidden as it's not yet implemented
        
        for title, icon in nav_items:
            item = QListWidgetItem(f"{icon}  {title}")
            item.setData(Qt.UserRole, title.lower())
            self.sidebar.addItem(item)

    def setup_content_pages(self):
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
        
        # Note: Accessibility page is not implemented yet, so it's not included

    def create_scrollable_page(self, title):
        """Create a scrollable page with title using GlowStatus theme."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title with GlowStatus styling
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 28px; 
            font-weight: bold; 
            margin-bottom: 20px; 
            color: #00d4ff;
            text-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
        """)
        layout.addWidget(title_label)
        
        # Scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        
        return page, content_layout

    def create_simple_page(self, title):
        """Create a simple page with title - no individual scrolling."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title with GlowStatus styling
        title_label = QLabel(title)
        title_label.setStyleSheet("""
            font-size: 28px; 
            font-weight: bold; 
            margin-bottom: 20px; 
            color: #00d4ff;
            text-shadow: 0 0 10px rgba(0, 212, 255, 0.3);
        """)
        layout.addWidget(title_label)
        
        return page, layout

    def create_about_page(self):
        """Create the About page."""
        page, layout = self.create_simple_page("About GlowStatus")
        
        # Logo and basic info
        logo_label = QLabel()
        logo_path = resource_path("img/GlowStatus.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)
        
        # Version and description with GlowStatus styling
        version_label = QLabel("Version 2.0.0 - GlowStatus")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            margin: 15px 0;
            color: #bf40ff;
            text-shadow: 0 0 10px rgba(191, 64, 255, 0.4);
        """)
        layout.addWidget(version_label)
        
        description = QTextBrowser()
        description.setMaximumHeight(250)
        description.setStyleSheet("""
            QTextBrowser {
                background-color: #2d2d2d;
                border: 2px solid #00d4ff;
                border-radius: 8px;
                color: #f8f9fa;
                padding: 15px;
                font-size: 14px;
                line-height: 1.5;
            }
        """)
        description.setHtml("""
        <div style="color: #f8f9fa; line-height: 1.6;">
        <p style="color: #00d4ff; font-weight: bold; font-size: 16px;">🌟 Light up your availability with smart LED integration</p>
        
        <p><strong style="color: #bf40ff;">GlowStatus</strong> is an intelligent status light controller that automatically adjusts your smart lights based on your calendar status, perfect for remote workers and streamers.</p>
        
        <p style="color: #00d4ff; font-weight: bold;">✨ Key Features:</p>
        <ul style="margin-left: 20px;">
        <li style="margin-bottom: 8px;">🔗 <span style="color: #00ff7f;">Google Calendar integration</span> - Real-time meeting status</li>
        <li style="margin-bottom: 8px;">💡 <span style="color: #ff6b35;">Govee smart light control</span> - Professional lighting automation</li>
        <li style="margin-bottom: 8px;">🎨 <span style="color: #bf40ff;">Customizable status colors</span> - Match your workflow</li>
        <li style="margin-bottom: 8px;">⚙️ <span style="color: #00d4ff;">Flexible configuration</span> - Tailored to your needs</li>
        <li style="margin-bottom: 8px;">🔒 <span style="color: #00ff7f;">Secure credential storage</span> - Privacy-first design</li>
        </ul>
        
        <p style="color: #bf40ff; font-style: italic;">Transform your workspace with intelligent lighting that reflects your availability status!</p>
        </div>
        """)
        layout.addWidget(description)
        
        # Links section with GlowStatus styling
        links_group = QGroupBox("🔗 Links & Support")
        links_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                padding-top: 15px;
            }
        """)
        links_layout = QVBoxLayout(links_group)
        links_layout.setSpacing(12)
        
        link_style = """
            color: #00d4ff; 
            text-decoration: none; 
            margin: 8px 0; 
            font-size: 14px;
            font-weight: 500;
            padding: 8px;
            border-radius: 4px;
            background-color: rgba(0, 212, 255, 0.1);
        """
        
        website_link = QLabel('<a href="https://www.glowstatus.app" style="{}">🌐 Official Website - glowstatus.app</a>'.format(link_style))
        website_link.setOpenExternalLinks(True)
        links_layout.addWidget(website_link)
        
        github_link = QLabel('<a href="https://github.com/Severswoed/GlowStatus" style="{}">💻 GitHub Repository</a>'.format(link_style))
        github_link.setOpenExternalLinks(True)
        links_layout.addWidget(github_link)
        
        privacy_link = QLabel('<a href="https://www.glowstatus.app/privacy" style="{}">🔒 Privacy Policy</a>'.format(link_style))
        privacy_link.setOpenExternalLinks(True)
        links_layout.addWidget(privacy_link)
        
        terms_link = QLabel('<a href="https://www.glowstatus.app/terms" style="{}">📋 Terms of Service</a>'.format(link_style))
        terms_link.setOpenExternalLinks(True)
        links_layout.addWidget(terms_link)
        
        sponsor_link = QLabel('<a href="https://github.com/sponsors/Severswoed" style="{}">💝 Sponsor this Project</a>'.format(link_style))
        sponsor_link.setOpenExternalLinks(True)
        links_layout.addWidget(sponsor_link)
        
        layout.addWidget(links_group)
        layout.addStretch()
        
        return page

    def create_wall_of_glow_page(self):
        """Create the Wall of Glow page for sponsors and supporters."""
        page, layout = self.create_simple_page("Wall of Glow")
        
        # Sponsorship header
        sponsor_header = QLabel()
        sponsor_header.setAlignment(Qt.AlignCenter)
        sponsor_header.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            margin: 20px 0;
            color: #FFD700;
            text-shadow: 0 0 15px rgba(255, 215, 0, 0.5);
        """)
        sponsor_header.setText("✨ Thanks to these amazing sponsors who help keep GlowStatus glowing bright! ✨")
        layout.addWidget(sponsor_header)
        
        # Sponsor showcase area
        sponsor_showcase = QGroupBox("🌟 Current Sponsors")
        sponsor_showcase.setStyleSheet("""
            QGroupBox {
                font-size: 18px;
                font-weight: bold;
                padding-top: 20px;
                color: #FFD700;
                border: 2px solid #FFD700;
                border-radius: 10px;
                margin-top: 10px;
            }
        """)
        sponsor_layout = QVBoxLayout(sponsor_showcase)
        sponsor_layout.setSpacing(15)
        
        # Placeholder for sponsors (will be populated when sponsors exist)
        no_sponsors_yet = QLabel()
        no_sponsors_yet.setAlignment(Qt.AlignCenter)
        no_sponsors_yet.setStyleSheet("""
            color: #b0b0b0; 
            font-size: 16px; 
            font-style: italic; 
            padding: 40px; 
            background-color: rgba(176, 176, 176, 0.1); 
            border-radius: 8px;
            border: 2px dashed #444;
        """)
        no_sponsors_yet.setText("""
🌟 Be the first to join our Wall of Glow! 🌟

Your sponsorship helps fund development, server hosting, 
and makes GlowStatus free for everyone.

Every sponsor gets featured here with their name, 
logo, and a special thank you message!
        """)
        sponsor_layout.addWidget(no_sponsors_yet)
        
        layout.addWidget(sponsor_showcase)
        
        # Become a sponsor section
        become_sponsor_group = QGroupBox("💝 Become a Sponsor")
        become_sponsor_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                padding-top: 15px;
                color: #bf40ff;
            }
        """)
        become_sponsor_layout = QVBoxLayout(become_sponsor_group)
        
        sponsor_benefits = QLabel("""
<div style="color: #f8f9fa; line-height: 1.6;">
<p style="color: #bf40ff; font-weight: bold; font-size: 16px;">💜 Why sponsor GlowStatus?</p>

<p>Your sponsorship directly supports:</p>
<ul style="margin-left: 20px;">
<li style="margin-bottom: 8px;">🔧 <span style="color: #00ff7f;">Active development</span> - New features and bug fixes</li>
<li style="margin-bottom: 8px;">🌐 <span style="color: #00d4ff;">Free hosting</span> - Discord bot and community infrastructure</li>
<li style="margin-bottom: 8px;">📚 <span style="color: #ff6b35;">Documentation</span> - Guides and tutorials for users</li>
<li style="margin-bottom: 8px;">🎨 <span style="color: #bf40ff;">Design improvements</span> - Better UI and user experience</li>
<li style="margin-bottom: 8px;">🔗 <span style="color: #00ff7f;">New integrations</span> - Support for more smart light brands</li>
</ul>

<p style="color: #FFD700; font-weight: bold;">✨ Sponsor Benefits:</p>
<ul style="margin-left: 20px;">
<li style="margin-bottom: 6px;">🌟 Featured prominently on this Wall of Glow</li>
<li style="margin-bottom: 6px;">📢 Recognition in release notes and announcements</li>
<li style="margin-bottom: 6px;">💬 Special sponsor role in our Discord community</li>
<li style="margin-bottom: 6px;">🎯 Direct input on feature priorities</li>
<li style="margin-bottom: 6px;">🚀 Early access to beta features</li>
</ul>
</div>
        """)
        sponsor_benefits.setWordWrap(True)
        sponsor_benefits.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                border: 2px solid #bf40ff;
                border-radius: 8px;
                color: #f8f9fa;
                padding: 20px;
                font-size: 14px;
                line-height: 1.5;
            }
        """)
        become_sponsor_layout.addWidget(sponsor_benefits)
        
        # Sponsor button
        sponsor_button_container = QHBoxLayout()
        sponsor_button_container.addStretch()
        
        sponsor_link = QLabel('<a href="https://github.com/sponsors/Severswoed" style="color: #FFD700; text-decoration: none; font-size: 18px; font-weight: bold; padding: 15px 30px; border: 2px solid #FFD700; border-radius: 8px; background-color: rgba(255, 215, 0, 0.1); display: inline-block; margin: 15px 0;">💝 Become a GitHub Sponsor</a>')
        sponsor_link.setOpenExternalLinks(True)
        sponsor_link.setAlignment(Qt.AlignCenter)
        sponsor_link.setStyleSheet("margin: 20px 0; padding: 10px;")
        become_sponsor_layout.addWidget(sponsor_link)
        
        layout.addWidget(become_sponsor_group)
        
        # Community support section
        community_group = QGroupBox("💙 Community Support")
        community_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                padding-top: 15px;
                color: #00d4ff;
            }
        """)
        community_layout = QVBoxLayout(community_group)
        
        community_text = QLabel("""
Can't sponsor? No problem! Here are other ways to support GlowStatus:

• ⭐ Star the repository on GitHub
• 🐛 Report bugs and suggest improvements
• 💬 Help others in our Discord community
• 📝 Contribute documentation or code
• 📸 Share your GlowStatus setup on social media
• 🔗 Tell friends and colleagues about GlowStatus

Every bit of support helps make GlowStatus better for everyone! 🚀
        """)
        community_text.setWordWrap(True)
        community_text.setStyleSheet("""
            color: #f8f9fa; 
            font-size: 14px; 
            line-height: 1.5; 
            padding: 20px; 
            background-color: rgba(0, 212, 255, 0.1); 
            border: 1px solid #00d4ff;
            border-radius: 8px;
        """)
        community_layout.addWidget(community_text)
        
        layout.addWidget(community_group)
        layout.addStretch()
        
        return page

    def create_oauth_page(self):
        """Create the OAuth/Authentication page."""
        page, layout = self.create_simple_page("OAuth & Authentication")
        
        # Google OAuth Section
        google_group = QGroupBox("Google Account")
        google_layout = QFormLayout(google_group)
        
        # OAuth Status
        self.oauth_status_label = QLabel("Not configured")
        google_layout.addRow("Status:", self.oauth_status_label)
        
        # User info
        self.google_user_label = QLabel("Not authenticated")
        google_layout.addRow("Authenticated as:", self.google_user_label)
        
        # OAuth buttons with improved layout
        oauth_buttons = QHBoxLayout()
        
        self.oauth_btn = QPushButton("🔑 Sign in with Google")
        self.oauth_btn.clicked.connect(self.run_oauth_flow)
        self.oauth_btn.setMinimumHeight(45)
        self.oauth_btn.setMinimumWidth(200)
        self.apply_google_button_style(self.oauth_btn)
        oauth_buttons.addWidget(self.oauth_btn)
        
        self.disconnect_btn = QPushButton("🔌 Disconnect")
        self.disconnect_btn.clicked.connect(self.disconnect_oauth)
        self.disconnect_btn.setMinimumHeight(45)
        self.disconnect_btn.setMinimumWidth(150)
        self.disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: 2px solid #ff6b35;
                border-radius: 8px;
                color: #ff6b35;
                font-size: 14px;
                font-weight: 600;
                padding: 10px 20px;
            }
            QPushButton:hover { 
                background-color: #ff6b35; 
                color: #1a1a1a;
                box-shadow: 0 0 15px rgba(255, 107, 53, 0.5);
            }
            QPushButton:pressed { 
                background-color: #e55a2b; 
                border: 2px solid #e55a2b;
            }
            QPushButton:disabled { 
                background-color: #2d2d2d; 
                color: #666; 
                border: 2px solid #666;
            }
        """)
        oauth_buttons.addWidget(self.disconnect_btn)
        oauth_buttons.addStretch()
        
        google_layout.addRow("Actions:", oauth_buttons)
        
        # Privacy notice with GlowStatus styling
        privacy_notice = QLabel(
            '🔒 By connecting your Google account, you agree to GlowStatus accessing your calendar data '
            'in read-only mode to determine your meeting status. Your data remains secure and private.'
        )
        privacy_notice.setWordWrap(True)
        privacy_notice.setStyleSheet("""
            color: #f8f9fa; 
            font-size: 12px; 
            margin: 15px 0; 
            padding: 12px; 
            background-color: rgba(0, 212, 255, 0.1);
            border: 1px solid rgba(0, 212, 255, 0.3);
            border-radius: 6px;
            line-height: 1.4;
        """)
        google_layout.addRow(privacy_notice)
        
        layout.addWidget(google_group)
        
        # Update OAuth status
        self.update_oauth_status()
        
        layout.addStretch()
        return page

    def create_integrations_page(self):
        """Create the Integrations page for third-party services."""
        page, layout = self.create_simple_page("Integrations")
        
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
        page, layout = self.create_simple_page("Calendar Settings")
        
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
        page, layout = self.create_simple_page("Status & Light Control")
        
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
        page, layout = self.create_simple_page("Options")
        
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
        page, layout = self.create_simple_page("Accessibility")
        
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

    def create_discord_page(self):
        """Create the Discord Community page."""
        page, layout = self.create_simple_page("Discord Community")
        
        # Discord logo and welcome section
        welcome_group = QGroupBox("🎮 Join the GlowStatus Community")
        welcome_group.setStyleSheet("""
            QGroupBox {
                font-size: 18px;
                font-weight: bold;
                padding-top: 20px;
                color: #5865f2;
                border: 2px solid #5865f2;
                border-radius: 10px;
                margin-top: 10px;
            }
        """)
        welcome_layout = QVBoxLayout(welcome_group)
        welcome_layout.setSpacing(15)
        
        # Community description
        description = QTextBrowser()
        description.setMaximumHeight(200)
        description.setStyleSheet("""
            QTextBrowser {
                background-color: #2d2d2d;
                border: 2px solid #5865f2;
                border-radius: 8px;
                color: #f8f9fa;
                padding: 15px;
                font-size: 14px;
                line-height: 1.5;
            }
        """)
        description.setHtml("""
        <div style="color: #f8f9fa; line-height: 1.6;">
        <p style="color: #5865f2; font-weight: bold; font-size: 16px;">💬 Connect with fellow GlowStatus users!</p>
        
        <p>Join our vibrant Discord community to get help, share setups, discuss features, and connect with other smart lighting enthusiasts.</p>
        
        <p style="color: #5865f2; font-weight: bold;">What you'll find:</p>
        <ul style="margin-left: 20px;">
        <li style="margin-bottom: 8px;">💡 <span style="color: #00ff7f;">Setup assistance</span> - Get help with configuration and troubleshooting</li>
        <li style="margin-bottom: 8px;">🎨 <span style="color: #bf40ff;">Show off your setups</span> - Share your lighting configurations</li>
        <li style="margin-bottom: 8px;">🚀 <span style="color: #00d4ff;">Feature discussions</span> - Suggest and discuss new features</li>
        <li style="margin-bottom: 8px;">🔧 <span style="color: #ff6b35;">Beta testing</span> - Test new features before release</li>
        <li style="margin-bottom: 8px;">📢 <span style="color: #00ff7f;">Updates & announcements</span> - Stay informed about releases</li>
        </ul>
        </div>
        """)
        welcome_layout.addWidget(description)
        
        layout.addWidget(welcome_group)
        
        # Invite section
        invite_group = QGroupBox("🔗 Join Now")
        invite_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                padding-top: 15px;
                color: #00d4ff;
            }
        """)
        invite_layout = QVBoxLayout(invite_group)
        invite_layout.setSpacing(15)
        
        # Permanent invite link
        invite_label = QLabel("Click the link below to join our Discord server:")
        invite_label.setStyleSheet("color: #f8f9fa; font-size: 14px; margin-bottom: 10px;")
        invite_layout.addWidget(invite_label)
        
        discord_invite = QLabel('<a href="https://discord.gg/TcKVQkS274" style="color: #5865f2; text-decoration: none; font-size: 18px; font-weight: bold; padding: 12px 20px; border: 2px solid #5865f2; border-radius: 8px; background-color: rgba(88, 101, 242, 0.1); display: inline-block; margin: 10px 0;">🎮 Join GlowStatus Discord Server</a>')
        discord_invite.setOpenExternalLinks(True)
        discord_invite.setAlignment(Qt.AlignCenter)
        discord_invite.setStyleSheet("margin: 15px 0; padding: 10px;")
        invite_layout.addWidget(discord_invite)
        
        # Additional info
        info_text = QLabel("The invite link will open in your default browser. If you don't have Discord installed, you can use it in your web browser or download the Discord app.")
        info_text.setWordWrap(True)
        info_text.setStyleSheet("""
            color: #b0b0b0; 
            font-size: 12px; 
            font-style: italic; 
            padding: 10px; 
            background-color: rgba(176, 176, 176, 0.1); 
            border-radius: 6px;
            margin-top: 10px;
        """)
        invite_layout.addWidget(info_text)
        
        layout.addWidget(invite_group)
        
        # Community guidelines section
        guidelines_group = QGroupBox("📋 Community Guidelines")
        guidelines_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                padding-top: 15px;
                color: #00ff7f;
            }
        """)
        guidelines_layout = QVBoxLayout(guidelines_group)
        
        guidelines_text = QTextBrowser()
        guidelines_text.setMaximumHeight(150)
        guidelines_text.setStyleSheet("""
            QTextBrowser {
                background-color: #2d2d2d;
                border: 2px solid #00ff7f;
                border-radius: 8px;
                color: #f8f9fa;
                padding: 15px;
                font-size: 13px;
                line-height: 1.4;
            }
        """)
        guidelines_text.setHtml("""
        <div style="color: #f8f9fa; line-height: 1.5;">
        <p style="color: #00ff7f; font-weight: bold;">Please follow these guidelines to keep our community welcoming:</p>
        <ul style="margin-left: 15px;">
        <li style="margin-bottom: 6px;">✅ Be respectful and helpful to all members</li>
        <li style="margin-bottom: 6px;">✅ Use appropriate channels for your questions</li>
        <li style="margin-bottom: 6px;">✅ Search previous messages before asking duplicate questions</li>
        <li style="margin-bottom: 6px;">✅ Share screenshots/logs when asking for technical help</li>
        <li style="margin-bottom: 6px;">❌ No spam, self-promotion, or off-topic content</li>
        </ul>
        </div>
        """)
        guidelines_layout.addWidget(guidelines_text)
        
        layout.addWidget(guidelines_group)
        
        # Support section
        support_group = QGroupBox("🆘 Need Help?")
        support_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                padding-top: 15px;
                color: #bf40ff;
            }
        """)
        support_layout = QVBoxLayout(support_group)
        
        support_text = QLabel("""
If you're experiencing issues or need immediate help:

• Check the #help-and-support channel in Discord
• Browse the #frequently-asked-questions channel
• Use the search function to find previous discussions
• Create a GitHub issue for bug reports
• Tag @Moderators for urgent community issues
        """)
        support_text.setWordWrap(True)
        support_text.setStyleSheet("""
            color: #f8f9fa; 
            font-size: 13px; 
            line-height: 1.5; 
            padding: 15px; 
            background-color: rgba(191, 64, 255, 0.1); 
            border: 1px solid #bf40ff;
            border-radius: 6px;
        """)
        support_layout.addWidget(support_text)
        
        layout.addWidget(support_group)
        layout.addStretch()
        
        return page

    def create_bottom_bar_horizontal(self, main_layout):
        """Create a horizontal bottom bar with save status and buttons."""
        bottom_frame = QFrame()
        bottom_frame.setFixedHeight(60)
        bottom_frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border-top: 2px solid #00d4ff;
                border-radius: 0;
            }
        """)
        
        bottom_layout = QHBoxLayout(bottom_frame)
        bottom_layout.setContentsMargins(20, 10, 20, 10)
        
        # Save status on the left
        self.save_status_label = QLabel("✅ All changes saved")
        self.save_status_label.setStyleSheet("""
            color: #00ff7f;
            font-weight: 500;
            font-size: 14px;
        """)
        bottom_layout.addWidget(self.save_status_label)
        
        # Spacer
        bottom_layout.addStretch()
        
        # Action buttons on the right
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # Reset button
        self.reset_btn = QPushButton("🔄 Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: 2px solid #ff6b35;
                border-radius: 6px;
                color: #ff6b35;
                font-size: 13px;
                font-weight: 500;
                padding: 8px 16px;
                min-width: 120px;
            }
            QPushButton:hover { 
                background-color: #ff6b35; 
                color: #1a1a1a;
            }
            QPushButton:pressed { background-color: #e55a2b; }
        """)
        button_layout.addWidget(self.reset_btn)
        
        # Save button
        self.save_btn = QPushButton("💾 Save All Changes")
        self.save_btn.clicked.connect(self.save_all_settings)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #00d4ff, stop:1 #bf40ff);
                border: 2px solid #00d4ff;
                border-radius: 6px;
                color: #ffffff;
                font-size: 13px;
                font-weight: 600;
                padding: 8px 16px;
                min-width: 120px;
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #bf40ff, stop:1 #00d4ff);
                box-shadow: 0 0 15px rgba(191, 64, 255, 0.5);
            }
            QPushButton:pressed { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #9932cc, stop:1 #0099cc);
            }
            QPushButton:disabled { 
                background-color: #3d3d3d; 
                color: #666; 
                border: 2px solid #666;
            }
        """)
        button_layout.addWidget(self.save_btn)
        
        bottom_layout.addLayout(button_layout)
        main_layout.addWidget(bottom_frame)

    # === OAUTH METHODS (adapted from original config_ui.py) ===
    
    def apply_google_button_style(self, button):
        """Apply Google branding with GlowStatus theme styling to OAuth button."""
        google_logo_path = resource_path('img/google_logo.png')
        
        if os.path.exists(google_logo_path):
            icon = QIcon(google_logo_path)
            button.setIcon(icon)
            button.setIconSize(QSize(20, 20))
        else:
            self.create_google_g_icon(button)
        
        button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #4285f4, stop:1 #00d4ff);
                border: 2px solid #00d4ff;
                border-radius: 8px;
                color: #ffffff;
                font-family: 'Segoe UI', Roboto, Arial, sans-serif;
                font-size: 14px;
                font-weight: 600;
                padding: 12px 24px;
                text-align: center;
                box-shadow: 0 0 15px rgba(0, 212, 255, 0.3);
            }
            QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #3367d6, stop:1 #bf40ff);
                border: 2px solid #bf40ff;
                box-shadow: 0 0 20px rgba(191, 64, 255, 0.5);
                transform: translateY(-1px);
            }
            QPushButton:pressed { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #2d5aa0, stop:1 #9932cc);
                box-shadow: 0 0 10px rgba(153, 50, 204, 0.3);
            }
            QPushButton:disabled { 
                background-color: #2d2d2d; 
                color: #666; 
                border: 2px solid #666;
                box-shadow: none;
            }
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
        self.oauth_btn.setText("🔄 Connecting...")
        self.disconnect_btn.setEnabled(False)
        
        self.google_user_label.setText("Authenticating...")
        if hasattr(self, 'selected_calendar_dropdown'):
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
                
        try:
            self.oauth_worker = OAuthWorker()
            self.oauth_worker.oauth_success.connect(self.on_oauth_success)
            self.oauth_worker.oauth_error.connect(self.on_oauth_error)
            self.oauth_worker.oauth_no_calendars.connect(self.on_oauth_no_calendars)
            self.oauth_worker.finished.connect(self.on_oauth_finished)
            self.oauth_worker.start()
        except Exception as e:
            self.on_oauth_error(f"Failed to start OAuth: {str(e)}")

    def on_oauth_success(self, user_email, calendars):
        """Handle successful OAuth authentication."""
        if hasattr(self, 'google_user_label'):
            self.google_user_label.setText(user_email)
        
        config = load_config()
        config["SELECTED_CALENDAR_ID"] = user_email
        save_config(config)
        logger.info(f"OAuth Success: Google account connected as {user_email}.")
        
        # Update calendar dropdown if it exists
        if hasattr(self, 'selected_calendar_dropdown'):
            self.selected_calendar_dropdown.clear()
            for cal in calendars:
                summary = cal.get("summary", "")
                cal_id = cal.get("id", "")
                display = f"{summary} ({cal_id})"
                self.selected_calendar_dropdown.addItem(display, cal_id)
            
            # Set to saved value if present
            saved_id = config.get("SELECTED_CALENDAR_ID", "")
            if saved_id:
                idx = self.selected_calendar_dropdown.findData(saved_id)
                if idx != -1:
                    self.selected_calendar_dropdown.setCurrentIndex(idx)
        
        self.update_oauth_status()
        QMessageBox.information(self, "Success", f"Successfully connected to Google Calendar as {user_email}")

    def on_oauth_error(self, error_message):
        """Handle errors during OAuth authentication."""
        if hasattr(self, 'google_user_label'):
            self.google_user_label.setText("Not authenticated")
        if hasattr(self, 'selected_calendar_dropdown'):
            self.selected_calendar_dropdown.clear()
            if "invalid_grant" in error_message.lower() or "expired" in error_message.lower() or "revoked" in error_message.lower():
                self.selected_calendar_dropdown.addItem("Please re-authenticate (token expired)")
            else:
                self.selected_calendar_dropdown.addItem("Please authenticate first")
        self.update_oauth_status()
        
        logger.error(f"OAuth Error: {error_message}")
        QMessageBox.critical(self, "Authentication Error", f"Failed to connect Google account:\n\n{error_message}")

    def on_oauth_no_calendars(self):
        """Handle case where no calendars are found after OAuth authentication."""
        if hasattr(self, 'google_user_label'):
            self.google_user_label.setText("No calendars found")
        if hasattr(self, 'selected_calendar_dropdown'):
            self.selected_calendar_dropdown.clear()
            self.selected_calendar_dropdown.addItem("No calendars found")
        logger.info("OAuth Success: Google account connected, but no calendars found.")
        self.update_oauth_status()
        
        QMessageBox.information(self, "Connected", "Google account connected successfully, but no calendars were found.")

    def on_oauth_finished(self):
        """Called when the OAuth worker thread finishes (regardless of success/error)."""
        # Re-enable UI elements
        if hasattr(self, 'oauth_btn'):
            self.oauth_btn.setEnabled(True)
            self.oauth_btn.setText("🔑 Sign in with Google")
        if hasattr(self, 'disconnect_btn'):
            self.disconnect_btn.setEnabled(True)
        
        # Clean up worker reference
        if hasattr(self, 'oauth_worker'):
            self.oauth_worker.deleteLater()
            self.oauth_worker = None

    def disconnect_oauth(self):
        """Disconnect Google OAuth by removing stored tokens."""
        from constants import TOKEN_PATH
        
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
                if hasattr(self, 'google_user_label'):
                    self.google_user_label.setText("Not authenticated")
                if hasattr(self, 'selected_calendar_dropdown'):
                    self.selected_calendar_dropdown.clear()
                    self.selected_calendar_dropdown.addItem("Please authenticate first")
                self.update_oauth_status()
                
                QMessageBox.information(self, "Disconnected", "Google account disconnected successfully.")
                logger.info("Google OAuth disconnected by user")
                
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to disconnect: {e}")
                logger.error(f"Failed to disconnect OAuth: {e}")

    def load_calendars(self):
        """Populate the calendar dropdown with available calendars if authenticated."""
        if not hasattr(self, 'selected_calendar_dropdown'):
            return
            
        # Always clear and set a default first to prevent crashes
        self.selected_calendar_dropdown.clear()
        
        # Check if we have valid authentication first
        try:
            from constants import TOKEN_PATH
            if not os.path.exists(TOKEN_PATH):
                self.selected_calendar_dropdown.addItem("Please authenticate first")
                return
        except ImportError:
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
            
            # Only proceed if we successfully got calendars
            calendars = calendar_list.get("items", [])
            if calendars:
                for cal in calendars:
                    summary = cal.get("summary", "")
                    cal_id = cal.get("id", "")
                    display = f"{summary} ({cal_id})"
                    self.selected_calendar_dropdown.addItem(display, cal_id)
                
                # Set to saved value if present
                config = load_config()
                saved_id = config.get("SELECTED_CALENDAR_ID", "")
                if saved_id:
                    idx = self.selected_calendar_dropdown.findData(saved_id)
                    if idx != -1:
                        self.selected_calendar_dropdown.setCurrentIndex(idx)
            else:
                self.selected_calendar_dropdown.addItem("No calendars found")
                
        except Exception as e:
            # Silently fail and show appropriate message - dropdown already has fallback
            self.selected_calendar_dropdown.clear()
            if "invalid_grant" in str(e).lower() or "expired" in str(e).lower() or "revoked" in str(e).lower():
                self.selected_calendar_dropdown.addItem("Please re-authenticate (token expired)")
            else:
                self.selected_calendar_dropdown.addItem("Please authenticate first")
            logger.info(f"Calendar loading failed (likely authentication issue): {e}")

    def add_status_row(self, status="", color="", power_off=False):
        """Add a row to the status table."""
        if not hasattr(self, 'status_table'):
            return
            
        row = self.status_table.rowCount()
        self.status_table.insertRow(row)
        self.status_table.setItem(row, 0, QTableWidgetItem(status))
        self.status_table.setItem(row, 1, QTableWidgetItem(color))
        
        # Power off checkbox
        chk = QCheckBox()
        chk.setChecked(power_off)
        self.status_table.setCellWidget(row, 2, chk)
        
        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(lambda: self.remove_status_row(row))
        self.status_table.setCellWidget(row, 3, delete_btn)

    def remove_status_row(self, row):
        """Remove a row from the status table."""
        if hasattr(self, 'status_table'):
            self.status_table.removeRow(row)

    def remove_selected_status(self):
        """Remove the selected status row."""
        if hasattr(self, 'status_table'):
            current_row = self.status_table.currentRow()
            if current_row >= 0:
                self.status_table.removeRow(current_row)

    def open_color_picker(self, row, column):
        """Open color picker when color cell is double-clicked."""
        if column == 1 and hasattr(self, 'status_table'):  # Color column
            color = QColorDialog.getColor()
            if color.isValid():
                rgb_str = f"{color.red()},{color.green()},{color.blue()}"
                self.status_table.setItem(row, column, QTableWidgetItem(rgb_str))

    def apply_manual_override(self):
        """Apply manual status override."""
        # This would typically connect to the main app's manual override functionality
        # For now, just show a message
        if hasattr(self, 'manual_status_combo') and hasattr(self, 'manual_minutes_spin'):
            status = self.manual_status_combo.currentText()
            minutes = self.manual_minutes_spin.value()
            QMessageBox.information(
                self, 
                "Manual Override", 
                f"Manual override set: {status} for {minutes} minutes.\n\n"
                "Note: This feature requires integration with the main GlowStatus application."
            )

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
        
        # Connect change signals for widgets that exist
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
        if hasattr(self, 'power_off_available_chk'):
            self.power_off_available_chk.toggled.connect(self.on_form_changed)
        if hasattr(self, 'power_off_unknown_chk'):
            self.power_off_unknown_chk.toggled.connect(self.on_form_changed)
        if hasattr(self, 'disable_calendar_sync_chk'):
            self.disable_calendar_sync_chk.toggled.connect(self.on_form_changed)
        if hasattr(self, 'disable_light_control_chk'):
            self.disable_light_control_chk.toggled.connect(self.on_form_changed)
        if hasattr(self, 'tray_icon_dropdown'):
            self.tray_icon_dropdown.currentTextChanged.connect(self.on_form_changed)
        if hasattr(self, 'status_table'):
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
        if hasattr(self, 'save_status_label'):
            if self.form_dirty:
                self.save_status_label.setText("🔄 Unsaved changes")
                self.save_status_label.setStyleSheet("color: #ff6b35; font-weight: 500; font-size: 14px;")
            else:
                self.save_status_label.setText("✅ All changes saved")
                self.save_status_label.setStyleSheet("color: #00ff7f; font-weight: 500; font-size: 14px;")

    def save_all_settings(self):
        """Save all settings from the form."""
        try:
            config = load_config()
            
            # Save Govee API Key securely if it exists
            if hasattr(self, 'govee_api_key_edit'):
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
            
            # Save Govee device settings
            if hasattr(self, 'govee_device_id_edit'):
                config["GOVEE_DEVICE_ID"] = self.govee_device_id_edit.text().strip()
            if hasattr(self, 'govee_device_model_edit'):
                config["GOVEE_DEVICE_MODEL"] = self.govee_device_model_edit.text().strip()
            
            # Calendar selection
            if hasattr(self, 'selected_calendar_dropdown'):
                calendar_data = self.selected_calendar_dropdown.currentData()
                config["SELECTED_CALENDAR_ID"] = calendar_data if calendar_data else ""
            
            # Save other settings if they exist
            if hasattr(self, 'refresh_interval_spin'):
                config["REFRESH_INTERVAL"] = self.refresh_interval_spin.value()
            if hasattr(self, 'power_off_available_chk'):
                config["POWER_OFF_WHEN_AVAILABLE"] = self.power_off_available_chk.isChecked()
            if hasattr(self, 'power_off_unknown_chk'):
                config["OFF_FOR_UNKNOWN_STATUS"] = self.power_off_unknown_chk.isChecked()
            if hasattr(self, 'disable_calendar_sync_chk'):
                config["DISABLE_CALENDAR_SYNC"] = self.disable_calendar_sync_chk.isChecked()
            if hasattr(self, 'disable_light_control_chk'):
                config["DISABLE_LIGHT_CONTROL"] = self.disable_light_control_chk.isChecked()
            if hasattr(self, 'tray_icon_dropdown'):
                config["TRAY_ICON"] = self.tray_icon_dropdown.currentText()
            
            # Status/Color mappings
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
            
            save_config(config)
            
            # Update save status
            self.form_dirty = False
           
            if hasattr(self, 'save_status_label'):
                self.save_status_label.setText("✅ All changes saved")
                self.save_status_label.setStyleSheet("color: #00ff7f; font-weight: 500; font-size: 14px;")
            
            QMessageBox.information(self, "Settings Saved", "Configuration saved successfully!")
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.warning(self, "Save Error", f"Failed to save settings: {e}")

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

    def reset_to_defaults(self):
        """Reset all settings to default values."""
        reply = QMessageBox.question(
            self, 
            "Reset to Defaults", 
            "Are you sure you want to reset all settings to their default values?\n\n"
            "This will:\n"
            "• Clear all API keys and credentials\n"
            "• Reset device configurations\n"
            "• Remove OAuth connections\n"
            "• Restore default preferences\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Clear keyring credentials
                try:
                    keyring.delete_password("GlowStatus", "GOVEE_API_KEY")
                except:
                    pass
                
                # Reset form fields
                if hasattr(self, 'govee_api_key_edit'):
                    self.govee_api_key_edit.clear()
                if hasattr(self, 'govee_device_id_edit'):
                    self.govee_device_id_edit.clear()
                if hasattr(self, 'govee_device_model_edit'):
                    self.govee_device_model_edit.clear()
                
                # Reset OAuth status
                if hasattr(self, 'google_user_label'):
                    self.google_user_label.setText("Not authenticated")
                if hasattr(self, 'selected_calendar_dropdown'):
                    self.selected_calendar_dropdown.clear()
                
                # Load template config and save it
                if os.path.exists(TEMPLATE_CONFIG_PATH):
                    import shutil
                    shutil.copy2(TEMPLATE_CONFIG_PATH, CONFIG_PATH)
                    logger.info("Reset configuration to template defaults")
                
                # Update UI
                self.update_oauth_status()
                self.save_status_label.setText("🔄 Reset to defaults")
                self.save_status_label.setStyleSheet("color: #ff6b35; font-weight: 500; font-size: 14px;")
                
                QMessageBox.information(
                    self, 
                    "Reset Complete", 
                    "All settings have been reset to their default values."
                )
                
            except Exception as e:
                logger.error(f"Error resetting to defaults: {e}")
                QMessageBox.warning(
                    self, 
                    "Reset Error", 
                    f"Failed to reset settings: {e}"
                )
