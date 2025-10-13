# -*- coding: utf-8 -*-
from PySide6 import QtWidgets
from PySide6.QtCore import Qt


# ------------------------------ 커스텀 ComboBox (F5로 즐겨찾기 로딩) ------------------------------

class FavoriteComboBox(QtWidgets.QComboBox):
    """F5로 선택된 즐겨찾기를 로딩하는 ComboBox"""

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F5:
            parent = self.parent()
            while parent:
                if hasattr(parent, 'load_favorite_from_combobox'):
                    parent.load_favorite_from_combobox()
                    event.accept()
                    return
                parent = parent.parent()
        super().keyPressEvent(event)
