#!/usr/bin/env python3
"""
Quick UI test to verify spinbox minimum value
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QSpinBox, QLabel
from PyQt5.QtCore import Qt

def test_spinbox_minimum():
    app = QApplication(sys.argv)
    
    window = QWidget()
    window.setWindowTitle("Refresh Interval Minimum Test")
    window.setGeometry(100, 100, 300, 150)
    
    layout = QVBoxLayout()
    
    label = QLabel("Test Refresh Interval Spinbox (min: 15 seconds):")
    layout.addWidget(label)
    
    spinbox = QSpinBox()
    spinbox.setRange(15, 3600)  # Same as our settings UI
    spinbox.setSuffix(" seconds")
    spinbox.setValue(15)
    layout.addWidget(spinbox)
    
    def on_value_changed(value):
        print(f"Spinbox value changed to: {value}")
    
    spinbox.valueChanged.connect(on_value_changed)
    
    info_label = QLabel("Try to decrease below 15 - it should stop at 15")
    layout.addWidget(info_label)
    
    window.setLayout(layout)
    window.show()
    
    print("Spinbox test window opened.")
    print("Try using arrow keys or typing to go below 15 - it should be prevented.")
    
    return app.exec_()

if __name__ == "__main__":
    test_spinbox_minimum()
