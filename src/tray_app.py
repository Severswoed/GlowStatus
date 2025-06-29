import sys
import os
import tempfile
import atexit
from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QMessageBox, QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton
)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt
from utils import resource_path
from config_ui import ConfigWindow, load_config, save_config
from glowstatus import GlowStatusController

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
    
    # --- App Setup ---
    config = load_config()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Set the application icon for the taskbar/dock
    icon_path = resource_path(f"img/GlowStatus_tray_tp_tight.png")
    app.setWindowIcon(QIcon(icon_path))

    tray_icon = config.get("TRAY_ICON", "GlowStatus_tray_tp_tight.png")
    tray_icon_path = resource_path(f"img/{tray_icon}")
    tray = QSystemTrayIcon(QIcon(tray_icon_path), parent=app)

    # --- Show tooltip if setup is incomplete ---
    missing = []
    if not config.get("GOVEE_DEVICE_ID"):
        missing.append("Govee Device ID")
    if not config.get("GOVEE_DEVICE_MODEL"):
        missing.append("Govee Device Model")
    if not config.get("SELECTED_CALENDAR_ID"):
        missing.append("Google Calendar")
    client_secret_path = resource_path('resources/client_secret.json')
    if not os.path.exists(client_secret_path):
        missing.append("Google client_secret.json")

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
        config["CURRENT_STATUS"] = status
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
        if "CURRENT_STATUS" in config:
            del config["CURRENT_STATUS"]
            save_config(config)
            update_tray_tooltip()
            glowstatus.update_now()
            update_tray_tooltip()

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

    # --- Menu Setup ---
    menu = QMenu()
    config_action = QAction("Open Settings")
    manual_meeting = QAction("Set Status: In Meeting")
    manual_focus = QAction("Set Status: Focus")
    manual_available = QAction("Set Status: Available")
    manual_end_meeting = QAction("End Meeting Early")
    reset_override = QAction("Reset State")
    sync_toggle = QAction("Disable Sync" if sync_enabled[0] else "Enable Sync")
    quit_action = QAction("Quit")

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
    tray.setContextMenu(menu)

    tray.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()