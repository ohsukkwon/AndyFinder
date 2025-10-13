# -*- coding: utf-8 -*-
"""애플리케이션 테마 설정"""

from PySide6 import QtGui, QtWidgets


def apply_light_theme(app: QtWidgets.QApplication):
    """Linux 느낌의 Light Theme 적용"""
    QtWidgets.QApplication.setStyle('Fusion')

    palette = QtGui.QPalette()

    white = QtGui.QColor(255, 255, 255)
    light_gray = QtGui.QColor(240, 240, 240)
    gray = QtGui.QColor(200, 200, 200)
    dark_gray = QtGui.QColor(100, 100, 100)
    black = QtGui.QColor(0, 0, 0)
    blue = QtGui.QColor(0, 120, 215)
    light_blue = QtGui.QColor(232, 242, 254)

    palette.setColor(QtGui.QPalette.Window, light_gray)
    palette.setColor(QtGui.QPalette.WindowText, black)
    palette.setColor(QtGui.QPalette.Base, white)
    palette.setColor(QtGui.QPalette.AlternateBase, light_gray)
    palette.setColor(QtGui.QPalette.ToolTipBase, light_blue)
    palette.setColor(QtGui.QPalette.ToolTipText, black)
    palette.setColor(QtGui.QPalette.Text, black)
    palette.setColor(QtGui.QPalette.Button, light_gray)
    palette.setColor(QtGui.QPalette.ButtonText, black)
    palette.setColor(QtGui.QPalette.BrightText, blue)
    palette.setColor(QtGui.QPalette.Highlight, blue)
    palette.setColor(QtGui.QPalette.HighlightedText, white)
    palette.setColor(QtGui.QPalette.Link, blue)
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text, dark_gray)
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, dark_gray)

    app.setPalette(palette)

    app.setStyleSheet("""
        QMenuBar {
            background-color: #F0F0F0;
            border-bottom: 1px solid #C0C0C0;
        }
        QMenuBar::item {
            background-color: transparent;
            padding: 4px 8px;
        }
        QMenuBar::item:selected {
            background-color: #0078D7;
            color: white;
        }
        QMenu {
            background-color: white;
            border: 1px solid #C0C0C0;
        }
        QMenu::item:selected {
            background-color: #0078D7;
            color: white;
        }
        QPushButton {
            background-color: #E0E0E0;
            border: 1px solid #A0A0A0;
            padding: 5px 15px;
            border-radius: 3px;
        }
        QPushButton:hover {
            background-color: #D0D0D0;
            border: 1px solid #0078D7;
        }
        QPushButton:pressed {
            background-color: #C0C0C0;
        }
        QPushButton:disabled {
            background-color: #F0F0F0;
            color: #A0A0A0;
        }
        QLineEdit {
            background-color: white;
            border: 1px solid #A0A0A0;
            padding: 4px;
            border-radius: 2px;
        }
        QLineEdit:focus {
            border: 2px solid #0078D7;
        }
        QComboBox {
            background-color: white;
            border: 1px solid #A0A0A0;
            padding: 4px;
            border-radius: 2px;
        }
        QComboBox:hover {
            border: 1px solid #0078D7;
        }
        QProgressBar {
            border: 1px solid #A0A0A0;
            border-radius: 3px;
            text-align: center;
            background-color: white;
        }
        QProgressBar::chunk {
            background-color: #0078D7;
            border-radius: 2px;
        }
        QStatusBar {
            background-color: #F0F0F0;
            border-top: 1px solid #C0C0C0;
        }
    """)
