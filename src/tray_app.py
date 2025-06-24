import sys
from PySide6.QtWidgets import (
    QApplication, QSystemTrayIcon, QMenu, QMessageBox, QWidget, QVBoxLayout, QLabel, QComboBox, QPushButton
)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt

from config_ui import ConfigWindow, load_config, save_config
from glowstatus import GlowStatusController

def main():
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
        app.quit()

    # --- App Setup ---
    config = load_config()
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    tray_icon = config.get("TRAY_ICON", "GlowStatus_tray_tp_tight.png")
    tray = QSystemTrayIcon(QIcon(f"img/{tray_icon}"), parent=app)

    glowstatus = GlowStatusController()
    sync_enabled = [not config.get("DISABLE_CALENDAR_SYNC", False)]
    if sync_enabled[0]:
        glowstatus.start()

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