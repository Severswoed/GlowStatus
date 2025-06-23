import sys
from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox
)
from PySide6.QtGui import QIcon
from config_ui import ConfigWindow, load_config, save_config

def main():
    app = QApplication(sys.argv)
    tray = QSystemTrayIcon(QIcon("img/GlowStatus.png"), parent=app)
    tray.setToolTip("GlowStatus")

    # Menu
    menu = QMenu()
    config_action = QAction("Open Settings")
    status_action = QAction("Show Status")
    manual_meeting = QAction("Set Status: In Meeting")
    manual_focus = QAction("Set Status: Focus")
    manual_available = QAction("Set Status: Available")
    clear_override = QAction("Clear Manual Override")
    quit_action = QAction("Quit")

    def show_config():
        config_window = ConfigWindow()
        config_window.show()
        app.config_window = config_window  # Prevent GC

    def show_status():
        config = load_config()
        status = config.get("CURRENT_STATUS", "unknown")
        QMessageBox.information(None, "Current Status", f"Current status: {status}")

    def set_manual_status(status):
        config = load_config()
        config["CURRENT_STATUS"] = status
        save_config(config)
        QMessageBox.information(None, "Manual Override", f"Status set to: {status}")

    def clear_manual_status():
        config = load_config()
        if "CURRENT_STATUS" in config:
            del config["CURRENT_STATUS"]
            save_config(config)
            QMessageBox.information(None, "Manual Override", "Manual override cleared.")

    config_action.triggered.connect(show_config)
    status_action.triggered.connect(show_status)
    manual_meeting.triggered.connect(lambda: set_manual_status("in_meeting"))
    manual_focus.triggered.connect(lambda: set_manual_status("focus"))
    manual_available.triggered.connect(lambda: set_manual_status("available"))
    clear_override.triggered.connect(clear_manual_status)
    quit_action.triggered.connect(app.quit)

    menu.addAction(config_action)
    menu.addAction(status_action)
    menu.addSeparator()
    menu.addAction(manual_meeting)
    menu.addAction(manual_focus)
    menu.addAction(manual_available)
    menu.addAction(clear_override)
    menu.addSeparator()
    menu.addAction(quit_action)
    tray.setContextMenu(menu)

    tray.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()