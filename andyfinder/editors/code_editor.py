# -*- coding: utf-8 -*-
"""
CodeEditor - 라인 번호와 북마크를 지원하는 코드 편집기
"""
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, Signal

from andyfinder.editors.line_number_area import LineNumberArea

# 전역 설정값
g_MIN_FONT_SIZE = 1
g_MAX_FONT_SIZE = 70


class CodeEditor(QtWidgets.QPlainTextEdit):
    fontSizeChanged = Signal(int)

    def __init__(self):
        super().__init__()
        self.lineNumberArea = LineNumberArea(self)
        self.color_highlight_selections = []
        self.bookmarks = set()

        # 가로/세로 스크롤바 항상 표시
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # 자동 줄바꿈 비활성화: 긴 한 줄은 한 줄로 보여주고 가로 스크롤로 이동
        self.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        try:
            # 일부 플랫폼에서 추가로 필요할 수 있음
            self.setWordWrapMode(QtGui.QTextOption.NoWrap)
        except Exception:
            pass

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

        # 초기 테두리 설정
        self.setStyleSheet("QPlainTextEdit { border: 1px solid black; }")

    # 폰트 설정 오버라이드: 에디터/라인넘버 동기화
    def setFont(self, font: QtGui.QFont):
        super().setFont(font)
        try:
            # 라인넘버 영역 폰트도 동일하게 적용
            if hasattr(self, 'lineNumberArea') and self.lineNumberArea:
                self.lineNumberArea.setFont(font)
            # 라인넘버 영역 폭 재계산 및 리프레시
            self.updateLineNumberAreaWidth(0)
            if hasattr(self, 'lineNumberArea') and self.lineNumberArea:
                self.lineNumberArea.update()
        except Exception:
            pass

    def focusInEvent(self, event):
        """포커스를 얻으면 빨간색 2px 테두리"""
        super().focusInEvent(event)
        self.setStyleSheet("QPlainTextEdit { border: 2px solid red; }")

    def focusOutEvent(self, event):
        """포커스를 잃으면 검은색 2px 테두리"""
        super().focusOutEvent(event)
        self.setStyleSheet("QPlainTextEdit { border: 2px solid black; }")

    def toggle_bookmark(self, line_number):
        """북마크 토글 (1-based) - 변경 시 부모에 알림"""
        if line_number in self.bookmarks:
            self.bookmarks.remove(line_number)
        else:
            self.bookmarks.add(line_number)
        self.lineNumberArea.update()

        # 부모(TabContent)에 북마크 변경 알림
        parent = self.parent()
        while parent:
            if hasattr(parent, '__class__') and parent.__class__.__name__ == 'TabContent':
                parent.update_bookmark_labels()
                break
            parent = parent.parent()

    def goto_next_bookmark(self):
        """다음 북마크로 이동"""
        if not self.bookmarks:
            return
        current_line = self.textCursor().blockNumber() + 1
        next_bookmarks = sorted([b for b in self.bookmarks if b > current_line])
        if next_bookmarks:
            self.gotoLine(next_bookmarks[0])

    def goto_previous_bookmark(self):
        """이전 북마크로 이동"""
        if not self.bookmarks:
            return
        current_line = self.textCursor().blockNumber() + 1
        prev_bookmarks = sorted([b for b in self.bookmarks if b < current_line], reverse=True)
        if prev_bookmarks:
            self.gotoLine(prev_bookmarks[0])

    def lineNumberAreaWidth(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value //= 10
            digits += 1
        space = 3 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def updateLineNumberAreaWidth(self, _):
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def updateLineNumberArea(self, rect, dy):
        if dy:
            self.lineNumberArea.scroll(0, dy)
        else:
            self.lineNumberArea.update(0, rect.y(), self.lineNumberArea.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.lineNumberArea.setGeometry(QtCore.QRect(cr.left(), cr.top(), self.lineNumberAreaWidth(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QtGui.QPainter(self.lineNumberArea)
        painter.fillRect(event.rect(), QtGui.QColor(230, 230, 230))

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(blockNumber + 1)
                line_number = blockNumber + 1

                if line_number in self.bookmarks:
                    painter.fillRect(0, int(top), self.lineNumberArea.width(),
                                     self.fontMetrics().height(), QtGui.QColor(255, 255, 0))
                    font = painter.font()
                    font.setBold(True)
                    painter.setFont(font)
                    painter.setPen(QtCore.Qt.red)
                else:
                    painter.setPen(QtCore.Qt.black)

                painter.drawText(0, int(top), self.lineNumberArea.width(),
                                 self.fontMetrics().height(), QtCore.Qt.AlignRight, number)

                if line_number in self.bookmarks:
                    font = painter.font()
                    font.setBold(False)
                    painter.setFont(font)

            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            blockNumber += 1

    def highlightCurrentLine(self):
        """요청사항 4: lineView_clone에도 current active line에 light blue 배경 표시"""
        extraSelections = []
        extraSelections.extend(self.color_highlight_selections)

        if not self.isReadOnly():
            selection = QtWidgets.QTextEdit.ExtraSelection()
            # 연한 yellow 배경색 설정
            lineColor = QtGui.QColor(255, 255, 200)  # 연한 yellow
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        else:
            selection = QtWidgets.QTextEdit.ExtraSelection()
            # 연한 green 배경색 설정
            lineColor = QtGui.QColor(200, 255, 200)  # 연한 green
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)

        self.setExtraSelections(extraSelections)

    def gotoLine(self, line_number):
        """특정 라인으로 이동 (1-based)"""
        if line_number < 1:
            return
        line_index = line_number - 1
        block = self.document().findBlockByNumber(line_index)
        if not block.isValid():
            return
        cursor = QtGui.QTextCursor(block)
        cursor.setPosition(block.position())
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
        self.centerCursor()

    def wheelEvent(self, event):
        # hasFocus 체크: focus가 있고 Ctrl이 눌린 경우만 확대/축소
        if self.hasFocus() and (event.modifiers() & Qt.ControlModifier):
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoomIn()
            elif delta < 0:
                self.zoomOut()
            event.accept()
        else:
            super().wheelEvent(event)

    def zoomIn(self):
        font = self.font()
        size = font.pointSize()
        if size < g_MAX_FONT_SIZE:
            font.setPointSize(size + 1)
            # 에디터/라인넘버 동시 적용
            self.setFont(font)
            self.fontSizeChanged.emit(font.pointSize())

    def zoomOut(self):
        font = self.font()
        size = font.pointSize()
        if size > g_MIN_FONT_SIZE:
            font.setPointSize(size - 1)
            # 에디터/라인넘버 동시 적용
            self.setFont(font)
            self.fontSizeChanged.emit(font.pointSize())

    def keyPressEvent(self, event):
        # focus가 있을 때만 F2/Shift+F2로 북마크 이동
        if self.hasFocus() and event.key() == Qt.Key_F2:
            if event.modifiers() == Qt.ShiftModifier:
                self.goto_previous_bookmark()
            else:
                self.goto_next_bookmark()
            event.accept()
            return
        super().keyPressEvent(event)
