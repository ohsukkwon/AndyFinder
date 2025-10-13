# -*- coding: utf-8 -*-
"""
LineNumberArea - 라인 번호 표시 및 북마크 관리 위젯
"""
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt


class LineNumberArea(QtWidgets.QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor
        self.setAcceptDrops(True)  # 드롭 허용

    def sizeHint(self):
        return QtCore.QSize(self.codeEditor.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self.codeEditor.lineNumberAreaPaintEvent(event)

    def mouseDoubleClickEvent(self, event):
        """라인 번호 영역 더블클릭 시 북마크 토글"""
        if event.button() == Qt.LeftButton:
            block = self.codeEditor.firstVisibleBlock()
            top = self.codeEditor.blockBoundingGeometry(block).translated(self.codeEditor.contentOffset()).top()
            bottom = top + self.codeEditor.blockBoundingRect(block).height()

            while block.isValid():
                if top <= event.position().y() <= bottom:
                    line_number = block.blockNumber() + 1
                    self.codeEditor.toggle_bookmark(line_number)
                    break

                block = block.next()
                top = bottom
                bottom = top + self.codeEditor.blockBoundingRect(block).height()

        super().mouseDoubleClickEvent(event)

    def dragEnterEvent(self, event):
        """드래그 진입 이벤트"""
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("LINENUMBER:"):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """드래그 이동 이벤트"""
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("LINENUMBER:"):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event):
        """드롭 이벤트 - tblResults의 LineNumber를 받아서 범위 복사"""
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if text.startswith("LINENUMBER:"):
                try:
                    # LineNumber 추출
                    source_line_number = int(text.replace("LINENUMBER:", ""))

                    # 드롭된 위치의 LineNumber 계산
                    block = self.codeEditor.firstVisibleBlock()
                    top = self.codeEditor.blockBoundingGeometry(block).translated(
                        self.codeEditor.contentOffset()).top()
                    bottom = top + self.codeEditor.blockBoundingRect(block).height()

                    target_line_number = -1
                    while block.isValid():
                        if top <= event.pos().y() <= bottom:
                            target_line_number = block.blockNumber() + 1
                            break

                        block = block.next()
                        top = bottom
                        bottom = top + self.codeEditor.blockBoundingRect(block).height()

                    if target_line_number > 0:
                        # TabContent의 복사 메서드 호출
                        tab_content = self.codeEditor.parent()
                        while tab_content and not hasattr(tab_content, '__class__') or \
                              (hasattr(tab_content, '__class__') and tab_content.__class__.__name__ != 'TabContent'):
                            tab_content = tab_content.parent()
                        if tab_content and hasattr(tab_content, 'copy_lines_between'):
                            tab_content.copy_lines_between(source_line_number, target_line_number)
                        event.acceptProposedAction()
                    else:
                        event.ignore()
                except ValueError:
                    event.ignore()
            else:
                event.ignore()
        else:
            event.ignore()
