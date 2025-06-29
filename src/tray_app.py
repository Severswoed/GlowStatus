import sys
import os
import tempfile
import atexit
from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QMessageBox, QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton
)
from PySide6.QtGui import QAction, QIcon, QCursor
from PySide6.QtCore import Qt, QTimer
from utils import resource_path
from config_ui import ConfigWindow, load_config, save_config
from glowstatus import GlowStatusController
from logger import get_logger

# Initialize logger
logger = get_logger("TrayApp")

# Global variable to hold the lock file handle
lock_file_handle = None

def check_single_instance():
    """
    Ensure only one instance of GlowStatus is running.
    Returns True if this is the only instance, False otherwise.
    """
    global lock_file_handle
    
    # Create a lock file in the temp directory
    lock_file_path = os.path.join(tempfile.gettempdir(), "glowstatus.lock")
    
    try:
        # Try to open the lock file exclusively
        if os.name == 'nt':  # Windows
            import msvcrt
            lock_file_handle = open(lock_file_path, 'w')
            msvcrt.locking(lock_file_handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:  # Unix/Linux/macOS
            import fcntl
            lock_file_handle = open(lock_file_path, 'w')
            fcntl.lockf(lock_file_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        
        # Write our PID to the lock file
        lock_file_handle.write(str(os.getpid()))
        lock_file_handle.flush()
        
        # Register cleanup function
        atexit.register(cleanup_lock_file)
        
        return True
        
    except (IOError, OSError):
        # Lock file is already locked by another process
        if lock_file_handle:
            lock_file_handle.close()
            lock_file_handle = None
        return False

def cleanup_lock_file():
    """Clean up the lock file when the application exits."""
    global lock_file_handle
    if lock_file_handle:
        try:
            lock_file_handle.close()
            # Try to remove the lock file
            lock_file_path = os.path.join(tempfile.gettempdir(), "glowstatus.lock")
            if os.path.exists(lock_file_path):
                os.remove(lock_file_path)
        except:
            pass  # Ignore errors during cleanup
        lock_file_handle = None

def main():
    try:
        # --- Single Instance Check ---
        if not check_single_instance():
            # Another instance is already running
            print("GlowStatus is already running. Only one instance is allowed.")
            # Try to show a message box if possible
            try:
                temp_app = QApplication(sys.argv)
                QMessageBox.warning(
                    None, 
                    "GlowStatus Already Running", 
                    "GlowStatus is already running.\nOnly one instance is allowed at a time."
                )
                temp_app.quit()
            except:
                pass  # If GUI can't be created, just exit silently
            sys.exit(1)
        
        print("Starting GlowStatus...")
        
        # --- App Setup ---
        config = load_config()
        print("Config loaded successfully")
        
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)
        print("Qt Application created")

        # Set the application icon for the taskbar/dock
        icon_path = resource_path(f"img/GlowStatus_tray_tp_tight.png")
        app.setWindowIcon(QIcon(icon_path))

        # Set up system tray icon with fallback
        tray_icon = config.get("TRAY_ICON", "GlowStatus_tray_tp_tight.png")
        tray_icon_path = resource_path(f"img/{tray_icon}")
        
        print(f"ICON DEBUG: Tray icon config: {tray_icon}")
        print(f"ICON DEBUG: Trying icon path: {tray_icon_path}")
        print(f"ICON DEBUG: Icon file exists: {os.path.exists(tray_icon_path)}")
        
        # Check if the icon file exists, fallback to default if not
        if not os.path.exists(tray_icon_path):
            print(f"ICON DEBUG: Primary icon not found: {tray_icon_path}")
            logger.warning(f"Tray icon not found: {tray_icon_path}")
            # Try a few fallback icons
            fallback_icons = [
                "GlowStatus.png",
                "GlowStatus_tray_tp.png", 
                "GlowStatus_tray_bk.png",
                "GlowStatus-Small.png"
            ]
            tray_icon_path = None
            for fallback in fallback_icons:
                fallback_path = resource_path(f"img/{fallback}")
                print(f"ICON DEBUG: Trying fallback: {fallback_path}")
                if os.path.exists(fallback_path):
                    tray_icon_path = fallback_path
                    print(f"ICON DEBUG: Using fallback tray icon: {fallback}")
                    logger.info(f"Using fallback tray icon: {fallback}")
                    break
            
            if not tray_icon_path:
                logger.error("No tray icon files found in img/ directory")
                # Create a simple colored icon as last resort
                from PySide6.QtGui import QPixmap, QPainter, QBrush
                pixmap = QPixmap(16, 16)
                pixmap.fill(Qt.blue)  # Simple blue square as fallback
                tray_icon_path = pixmap
        
        # Create the system tray icon
        if isinstance(tray_icon_path, str):
            tray = QSystemTrayIcon(QIcon(tray_icon_path), parent=app)
        else:
            tray = QSystemTrayIcon(QIcon(tray_icon_path), parent=app)  # pixmap fallback
        
        logger.info(f"System tray icon initialized with: {tray_icon_path}")
        
        # Check if system tray is available
        if not QSystemTrayIcon.isSystemTrayAvailable():
            QMessageBox.critical(None, "System Tray", "System tray is not available on this system.")
            sys.exit(1)
        
        # Ensure the tray icon is visible
        if not tray.icon().isNull():
            logger.info("Tray icon successfully loaded")
        else:
            logger.error("Tray icon failed to load - icon is null")

        # --- Show tooltip if setup is incomplete ---
        missing = []
        
        # Check for light controller configuration
        govee_configured = bool(config.get("GOVEE_DEVICE_ID") and config.get("GOVEE_DEVICE_MODEL"))
        
        # Auto-disable light control if no device is configured
        # This prepares for future Hue/LIFX/Nanoleaf support
        if not govee_configured and "DISABLE_LIGHT_CONTROL" not in config:
            config["DISABLE_LIGHT_CONTROL"] = True
            save_config(config)
            logger.info("Auto-disabled light control: no device configuration found")
        
        # Only show missing device warnings if light control is enabled
        if not config.get("DISABLE_LIGHT_CONTROL", False):
            if not config.get("GOVEE_DEVICE_ID"):
                missing.append("Smart Light Device ID")
            if not config.get("GOVEE_DEVICE_MODEL"):
                missing.append("Smart Light Device Model")
        
        # Check for calendar configuration
        if not config.get("SELECTED_CALENDAR_ID"):
            missing.append("Google Calendar")
        client_secret_path = resource_path('resources/client_secret.json')
        if not os.path.exists(client_secret_path):
            missing.append("Google client_secret.json")

        # Auto-disable calendar sync if no OAuth is configured
        # This prepares for future Apple/Microsoft calendar support
        if not os.path.exists(client_secret_path) and "DISABLE_CALENDAR_SYNC" not in config:
            config["DISABLE_CALENDAR_SYNC"] = True
            save_config(config)
            logger.info("Auto-disabled calendar sync: no OAuth configuration found")

        if missing:
            tray.show()
            tray.showMessage(
                "GlowStatus Setup Required",
                "Please complete setup in the Settings window:\n" + ", ".join(missing),
                QSystemTrayIcon.Information,
                10000  # duration in ms (10 seconds)
            )

        glowstatus = GlowStatusController()
        sync_enabled = [not config.get("DISABLE_CALENDAR_SYNC", False)]
        if sync_enabled[0]:
            glowstatus.start()

        # --- Helper Functions ---
        def update_tray_tooltip():
            config = load_config()
            status = config.get("CURRENT_STATUS", "unknown")
            cal_id = config.get("SELECTED_CALENDAR_ID", "primary")
            tray.setToolTip(f"GlowStatus - {status} ({cal_id})")

        def show_config():
            config_window = ConfigWindow()
            config_window.setAttribute(Qt.WA_DeleteOnClose)
            config_window.show()
            config_window.raise_()           # Bring window to front
            config_window.activateWindow()   # Give it focus
            app.config_window = config_window

            def on_config_closed():
                # Reload config and update tray icon
                config = load_config()
                tray_icon = config.get("TRAY_ICON", "GlowStatus_tray_tp_tight.png")
                tray.setIcon(QIcon(f"img/{tray_icon}"))
                update_tray_tooltip()

            config_window.destroyed.connect(on_config_closed)

        def show_status():
            config = load_config()
            status = config.get("CURRENT_STATUS", "unknown")
            cal_id = config.get("SELECTED_CALENDAR_ID", "primary")
            QMessageBox.information(None, "Current Status", f"Current status: {status}\nCalendar: {cal_id}")

        def set_manual_status(status):
            config = load_config()
            import time
            
            # Store manual status with timestamp for expiration logic
            config["CURRENT_STATUS"] = status
            config["MANUAL_STATUS_TIMESTAMP"] = time.time()
            
            # Manual overrides expire after 2 hours to prevent missing meetings
            config["MANUAL_STATUS_EXPIRY"] = 2 * 60 * 60  # 2 hours in seconds
            
            save_config(config)
            update_tray_tooltip()
            glowstatus.update_now()
            update_tray_tooltip()

        def set_end_meeting():
            config = load_config()
            config["CURRENT_STATUS"] = "meeting_ended_early"
            save_config(config)
            update_tray_tooltip()
            glowstatus.update_now()
            update_tray_tooltip()

        def reset_state():
            config = load_config()
            # Clear all manual override data
            manual_cleared = False
            if "CURRENT_STATUS" in config:
                del config["CURRENT_STATUS"]
                manual_cleared = True
            if "MANUAL_STATUS_TIMESTAMP" in config:
                del config["MANUAL_STATUS_TIMESTAMP"]
                manual_cleared = True
            if "MANUAL_STATUS_EXPIRY" in config:
                del config["MANUAL_STATUS_EXPIRY"]
            
            if manual_cleared:
                save_config(config)
                update_tray_tooltip()
                glowstatus.update_now()
                update_tray_tooltip()
                logger.info("Manual status override cleared by user")

        def toggle_sync():
            config = load_config()
            if not sync_enabled[0]:
                config["DISABLE_CALENDAR_SYNC"] = False
                save_config(config)
                glowstatus.start()
                sync_toggle.setText("Disable Sync")
                sync_enabled[0] = True
            else:
                config["DISABLE_CALENDAR_SYNC"] = True
                save_config(config)
                glowstatus.stop()
                sync_toggle.setText("Enable Sync")
                sync_enabled[0] = False

        def quit_app():
            glowstatus.stop()
            cleanup_lock_file()  # Ensure lock file is cleaned up
            app.quit()

        update_tray_tooltip()
        glowstatus.update_now()

        # --- Menu Setup (Dynamic) ---
        def create_context_menu():
            """Create context menu with current status displayed"""
            print("DEBUG: Creating context menu...")
            config = load_config()
            current_status = config.get("CURRENT_STATUS", "unknown")
            
            # Create menu with tray as parent for proper Windows behavior
            menu = QMenu(tray)
            config_action = QAction("Open Settings", menu)
            manual_meeting = QAction("Set Status: In Meeting", menu)
            manual_focus = QAction("Set Status: Focus", menu)
            manual_available = QAction("Set Status: Available", menu)
            manual_end_meeting = QAction("End Meeting Early", menu)
            reset_override = QAction(f"Clear Manual Override (Current: {current_status})", menu)
            sync_toggle = QAction("Disable Sync" if sync_enabled[0] else "Enable Sync", menu)
            quit_action = QAction("Quit", menu)

            config_action.triggered.connect(show_config)
            manual_meeting.triggered.connect(lambda: set_manual_status("in_meeting"))
            manual_focus.triggered.connect(lambda: set_manual_status("focus"))
            manual_available.triggered.connect(lambda: set_manual_status("available"))
            manual_end_meeting.triggered.connect(set_end_meeting)
            reset_override.triggered.connect(reset_state)
            sync_toggle.triggered.connect(toggle_sync)
            quit_action.triggered.connect(quit_app)

            menu.addAction(config_action)
            menu.addSeparator()
            menu.addAction(manual_meeting)
            menu.addAction(manual_focus)
            menu.addAction(manual_available)
            menu.addSeparator()
            menu.addAction(manual_end_meeting)
            menu.addAction(reset_override)
            menu.addSeparator()
            menu.addAction(sync_toggle)
            menu.addSeparator()
            menu.addAction(quit_action)
            
            print(f"DEBUG: Context menu created with {len(menu.actions())} actions")
            return menu
        
        # Update context menu dynamically when right-clicked
        def on_tray_activated(reason):
            print(f"DEBUG: Tray activated with reason: {reason}")
            if reason == QSystemTrayIcon.Context:
                print("DEBUG: Right-click detected, showing context menu manually")
                # Create and show context menu manually at cursor position
                menu = create_context_menu()
                # Get cursor position and show menu there
                from PySide6.QtGui import QCursor
                cursor_pos = QCursor.pos()
                print(f"DEBUG: Showing menu at cursor position: {cursor_pos}")
                menu.exec(cursor_pos)
            elif reason == QSystemTrayIcon.DoubleClick:
                print("DEBUG: Double-click detected, opening settings")
                # Double-click opens settings
                show_config()
            elif reason == QSystemTrayIcon.Trigger:
                print("DEBUG: Left-click detected, opening settings")
                # Left-click also opens settings as fallback
                show_config()
            elif reason == QSystemTrayIcon.MiddleClick:
                print("DEBUG: Middle-click detected")
        
        # Set up tray icon event handling
        tray.activated.connect(on_tray_activated)
        
        # Note: We don't set a context menu via setContextMenu() because
        # we handle it manually in on_tray_activated() for better Windows compatibility

        print("Tray icon setup complete, showing tray...")
        tray.show()
        print("Starting Qt event loop...")
        sys.exit(app.exec())

    except Exception as e:
        error_msg = f"GlowStatus startup error: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        
        # Try to show error dialog
        try:
            if 'app' not in locals():
                app = QApplication(sys.argv)
            QMessageBox.critical(
                None,
                "GlowStatus Startup Error", 
                f"Failed to start GlowStatus:\n\n{error_msg}\n\nCheck console for details."
            )
        except:
            pass  # If we can't show the dialog, at least we printed the error
        
        sys.exit(1)

if __name__ == "__main__":
    main()