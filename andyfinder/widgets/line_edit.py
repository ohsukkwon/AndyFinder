# -*- coding: utf-8 -*-
from PySide6 import QtWidgets
from PySide6.QtCore import Qt, Signal, QTimer


# ------------------------------ Long Click LineEdit ------------------------------
class LongClickLineEdit(QtWidgets.QLineEdit):
    """Long Click을 감지하는 커스텀 LineEdit"""
    longClicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.press_timer = QTimer()
        self.press_timer.setSingleShot(True)
        self.press_timer.timeout.connect(self.on_long_press)
        self.long_press_duration = 500  # 500ms
        self.is_pressed = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_pressed = True
            self.press_timer.start(self.long_press_duration)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_pressed = False
            self.press_timer.stop()
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        # 마우스가 움직이면 long click 취소
        if self.is_pressed:
            self.press_timer.stop()
        super().mouseMoveEvent(event)

    def on_long_press(self):
        if self.is_pressed:
            self.longClicked.emit()


# ------------------------------ 커스텀 LineEdit (F5 단축키 지원) ------------------------------

class QueryLineEdit(LongClickLineEdit):
    """F5로 검색을 실행하는 LineEdit"""

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F5:
            # 부모에서 TabContent 찾기
            parent = self.parent()
            while parent:
                if hasattr(parent, 'do_search'):
                    parent.do_search()
                    event.accept()
                    return
                parent = parent.parent()
        super().keyPressEvent(event)


class ColorKeywordsLineEdit(LongClickLineEdit):
    """F5로 설정을 적용하는 LineEdit"""

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F5:
            # 부모에서 TabContent 찾기
            parent = self.parent()
            while parent:
                if hasattr(parent, 'on_color_settings_clicked'):
                    parent.on_color_settings_clicked()
                    event.accept()
                    return
                parent = parent.parent()
        super().keyPressEvent(event)


class ResultSearchLineEdit(LongClickLineEdit):
    """F3/F4로 결과 내 검색을 수행하는 LineEdit"""

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F3:
            parent = self.parent()
            while parent:
                if hasattr(parent, 'search_in_results_prev'):
                    parent.search_in_results_prev()
                    event.accept()
                    return
                parent = parent.parent()
        elif event.key() == Qt.Key_F4:
            parent = self.parent()
            while parent:
                if hasattr(parent, 'search_in_results_next'):
                    parent.search_in_results_next()
                    event.accept()
                    return
                parent = parent.parent()
        super().keyPressEvent(event)
