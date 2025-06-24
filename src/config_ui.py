import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QComboBox, QHBoxLayout, QColorDialog, QCheckBox, QFrame, QMessageBox
)
from PySide6.QtCore import Qt

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../config/glowstatus_config.json"))

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

class ConfigWindow(QWidget):
    def __init__(self):
        super().__init__()
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

        # Tray Icon Picker (unchanged)
        line_tray = QFrame()
        line_tray.setFrameShape(QFrame.HLine)
        line_tray.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line_tray)
        img_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../img"))
        tray_icons = [f for f in os.listdir(img_dir) if "_tray_" in f]
        self.tray_icon_dropdown = QComboBox()
        self.tray_icon_dropdown.addItems(tray_icons)
        layout.addWidget(QLabel("Tray Icon:"))
        layout.addWidget(self.tray_icon_dropdown)

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_config)
        layout.addWidget(self.save_btn)

        self.setLayout(layout)
        self.status_table.cellDoubleClicked.connect(self.open_color_picker)

    def add_status_row(self, status="", color="", power_off=False):
        row = self.status_table.rowCount()
        self.status_table.insertRow(row)
        self.status_table.setItem(row, 0, QTableWidgetItem(status))
        self.status_table.setItem(row, 1, QTableWidgetItem(color))
        chk = QCheckBox()
        chk.setChecked(power_off)
        chk.setAlignment(Qt.AlignCenter)
        self.status_table.setCellWidget(row, 2, chk)

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
        save_config(config)
        QMessageBox.information(self, "Saved", "Settings saved successfully.")