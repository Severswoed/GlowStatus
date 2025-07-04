#!/usr/bin/env python3
"""
Quick test to verify dropdown arrow visibility in QComboBox widgets
"""
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QComboBox, QLabel
from PyQt5.QtCore import Qt

def test_dropdown_visibility():
    app = QApplication(sys.argv)
    
    window = QWidget()
    window.setWindowTitle("Dropdown Arrow Test")
    window.setGeometry(100, 100, 400, 300)
    
    layout = QVBoxLayout()
    
    # Test label
    label = QLabel("Test Dropdown Arrow Visibility:")
    layout.addWidget(label)
    
    # Create test combo box with the same CSS as our settings UI
    combo = QComboBox()
    combo.addItems(["Option 1", "Option 2", "Option 3", "A Very Long Option Name"])
    
    # Apply the same CSS styling
    combo.setStyleSheet("""
        QComboBox {
            background-color: #3b3b3b;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: #ebebeb;
            font-size: 14px;
            padding: 12px 60px 12px 16px;
            min-height: 20px;
        }
        
        QComboBox:hover {
            border-color: rgba(255, 255, 255, 0.18);
        }
        
        QComboBox::drop-down {
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 50px;
            border-left: 1px solid rgba(255, 255, 255, 0.1);
            background-color: rgba(255, 255, 255, 0.08);
            border-top-right-radius: 10px;
            border-bottom-right-radius: 10px;
        }
        
        QComboBox::down-arrow {
            image: none;
            border-left: 8px solid transparent;
            border-right: 8px solid transparent;
            border-top: 10px solid #ebebeb;
            width: 0px;
            height: 0px;
            subcontrol-origin: content;
            subcontrol-position: center;
        }
        
        QComboBox::down-arrow:on {
            border-left: 8px solid transparent;
            border-right: 8px solid transparent;
            border-bottom: 10px solid #ebebeb;
            border-top: none;
        }
        
        QComboBox QAbstractItemView {
            background-color: #272727;
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            selection-background-color: #38bdf8;
            color: #ebebeb;
            outline: none;
            min-width: 200px;
        }
    """)
    
    layout.addWidget(combo)
    
    # Add another test combo with different background
    combo2 = QComboBox()
    combo2.addItems(["Dark Theme Test", "Medium Item", "Short"])
    combo2.setStyleSheet(combo.styleSheet())
    layout.addWidget(combo2)
    
    window.setLayout(layout)
    window.show()
    
    print("Dropdown visibility test window opened. Check if arrows are visible!")
    print("- Arrow should be clearly visible on the right side")
    print("- Arrow should change direction when dropdown is open")
    print("- Click on dropdowns to test functionality")
    
    return app.exec_()

if __name__ == "__main__":
    test_dropdown_visibility()
