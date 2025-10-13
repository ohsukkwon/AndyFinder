# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, Signal, QModelIndex, QTimer

if TYPE_CHECKING:
    from AndyFinderTab import TabContent

# Global 상수
g_MIN_FONT_SIZE = 1
g_MAX_FONT_SIZE = 70


class DragTableView(QtWidgets.QTableView):
    """드래그를 지원하는 TableView (Long Press + Move로 드래그 시작, 0번 컬럼(LineNumber) 전용)
       + 요청사항 반영: Ctrl+Wheel 폰트 확대/축소, Ctrl+C 복사, Ctrl+A 전체선택
       + 요청사항 반영: Shift + 마우스 오른쪽 클릭으로도 범위 선택 가능
       + 요청사항 반영: 행 선택 시 가로 스크롤을 첫 번째 컬럼으로 이동
    """
    fontSizeChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 기본 자동 드래그는 끄고(충돌 방지), 수동으로 처리
        self.setDragEnabled(False)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragOnly)

        # 스크롤바 항상 표시
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        # 스크롤 모드: 픽셀 단위로 스크롤(가로/세로 모두 자연스럽게 드래그 가능)
        self.setHorizontalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)
        self.setVerticalScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)

        # 자동 줄바꿈 비활성화: 한 줄 텍스트는 항상 한 줄로
        self.setWordWrap(False)
        # 텍스트 생략(elide) 비활성화: 가로 스크롤로 전체를 볼 수 있도록
        self.setTextElideMode(Qt.ElideNone)

        # Long press용 상태 변수
        self._press_timer = QTimer(self)
        self._press_timer.setSingleShot(True)
        self._press_timer.timeout.connect(self._on_long_press_timeout)
        self._long_press_duration = 500  # ms

        self._pressed = False
        self._press_pos = QtCore.QPoint()
        self._press_index = QModelIndex()

        # 드래그 이미지 설정용
        self._drag_pixmap_size = QtCore.QSize(100, 30)

    def setModel(self, model):
        """모델 설정 시 선택 변경 시그널 연결"""
        super().setModel(model)
        if model:
            sel_model = self.selectionModel()
            if sel_model:
                sel_model.currentChanged.connect(self.on_current_changed)

    def scrollTo(self, index, hint=QtWidgets.QAbstractItemView.EnsureVisible):
        """세로 스크롤만 수행하고, 가로 스크롤은 항상 0(첫 번째 컬럼)으로 유지"""
        super().scrollTo(index, hint)
        # scrollTo 후 가로 스크롤을 첫 번째 컬럼으로 이동
        self.horizontalScrollBar().setValue(0)
        # 이벤트 루프 후에도 확실하게 설정 (Qt의 지연된 조정 방지)
        QtCore.QTimer.singleShot(0, lambda: self.horizontalScrollBar().setValue(0))

    def on_current_changed(self, current, previous):
        """현재 선택이 변경될 때 가로 스크롤을 첫 번째 컬럼으로 이동"""
        if current.isValid():
            # 가로 스크롤바를 맨 왼쪽(첫 번째 컬럼)으로 이동
            self.horizontalScrollBar().setValue(0)
            # 이벤트 루프 후에도 확실하게 설정
            QtCore.QTimer.singleShot(0, lambda: self.horizontalScrollBar().setValue(0))

    def mouseDoubleClickEvent(self, event):
        """더블클릭 이벤트 처리: 왼쪽/오른쪽 구분"""
        if event.button() == Qt.LeftButton:
            # 왼쪽 더블클릭: 기본 동작 (시그널 발생하여 lineView 이동만)
            super().mouseDoubleClickEvent(event)
        elif event.button() == Qt.RightButton:
            # 오른쪽 더블클릭: 마킹 토글만 (lineView 이동 안함)
            index = self.indexAt(event.position().toPoint())
            if index.isValid():
                # TYPE_CHECKING을 위한 import를 사용하므로 런타임에는 문자열 비교
                tab_content = self.parent()
                while tab_content and tab_content.__class__.__name__ != 'TabContent':
                    tab_content = tab_content.parent()
                if tab_content and hasattr(tab_content, 'toggle_result_mark'):
                    tab_content.toggle_result_mark(index.row())
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        # Shift + Right Click 으로 범위 선택 지원
        if event.button() == Qt.RightButton and (event.modifiers() & Qt.ShiftModifier):
            idx = self.indexAt(event.position().toPoint())
            if idx.isValid():
                sel_model = self.selectionModel()
                model = self.model()
                if sel_model and model:
                    anchor = sel_model.currentIndex()
                    if not anchor.isValid():
                        anchor = idx
                    start_row = min(anchor.row(), idx.row())
                    end_row = max(anchor.row(), idx.row())
                    top_left = model.index(start_row, 0)
                    bottom_right = model.index(end_row, model.columnCount() - 1)
                    selection = QtCore.QItemSelection(top_left, bottom_right)
                    # 기본 Shift-LeftClick처럼 ClearAndSelect + Rows 동작
                    sel_model.select(selection, QtCore.QItemSelectionModel.ClearAndSelect | QtCore.QItemSelectionModel.Rows)
                    sel_model.setCurrentIndex(idx, QtCore.QItemSelectionModel.NoUpdate)
            event.accept()
            return

        if event.button() == Qt.LeftButton:
            self._pressed = True
            self._press_pos = event.position().toPoint()
            self._press_index = self.indexAt(event.position().toPoint())

            # 선택은 기본 동작대로 수행
            super().mousePressEvent(event)

            # Long press 타이머 시작 (LineNumber(0번 컬럼)에서만)
            if self._press_index.isValid() and self._press_index.column() == 0:
                self._press_timer.start(self._long_press_duration)
            else:
                self._press_timer.stop()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._pressed:
            # 이동 거리 확인해서 기준 넘으면 즉시 드래그 시작
            if (event.position().toPoint() - self._press_pos).manhattanLength() >= QtWidgets.QApplication.startDragDistance():
                self._press_timer.stop()
                if self._press_index.isValid() and self._press_index.column() == 0:
                    self._start_drag(self._press_index)
                self._pressed = False
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._press_timer.stop()
            self._pressed = False
        super().mouseReleaseEvent(event)

    def _on_long_press_timeout(self):
        # 길게 누름이 유지되었고, 여전히 유효한 0번 컬럼이면 드래그 시작
        if self._pressed and self._press_index.isValid() and self._press_index.column() == 0:
            self._start_drag(self._press_index)
            self._pressed = False

    def _start_drag(self, index: QModelIndex):
        if not index.isValid():
            return

        # 0번 컬럼(라인번호) 셀로 보정
        model = self.model()
        ln_index = model.index(index.row(), 0)
        line_str = model.data(ln_index, Qt.DisplayRole)

        if not line_str:
            return

        try:
            line_number = int(str(line_str))
        except ValueError:
            return

        # 드래그 데이터 설정
        drag = QtGui.QDrag(self)
        mime_data = QtCore.QMimeData()
        mime_data.setText(f"LINENUMBER:{line_number}")
        drag.setMimeData(mime_data)

        # 드래그 시각적 표시
        pixmap = QtGui.QPixmap(self._drag_pixmap_size)
        pixmap.fill(QtGui.QColor(200, 200, 255, 180))
        painter = QtGui.QPainter(pixmap)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, f"Line {line_number}")
        painter.end()
        drag.setPixmap(pixmap)
        drag.setHotSpot(QtCore.QPoint(pixmap.width() // 2, pixmap.height() // 2))

        # 드래그 실행 (Copy)
        drag.exec_(Qt.CopyAction)

    # 기존 startDrag는 사용하지 않지만, 혹시 모를 호출에 대비해 남겨둠
    def startDrag(self, supportedActions):
        index = self.currentIndex()
        if not (index.isValid() and index.column() == 0):
            return
        self._start_drag(index)

    # ---- Ctrl+Wheel로 폰트 크기 조절 (focus가 있을 때만) ----
    def wheelEvent(self, event: QtGui.QWheelEvent):
        if self.hasFocus() and (event.modifiers() & Qt.ControlModifier):
            delta = event.angleDelta().y()
            if delta == 0:
                delta = event.pixelDelta().y()
            if delta > 0:
                self.zoomIn()
            elif delta < 0:
                self.zoomOut()
            event.accept()
            return
        super().wheelEvent(event)

    def zoomIn(self):
        font = self.font()
        size = font.pointSize()
        if size < g_MAX_FONT_SIZE:
            font.setPointSize(size + 1)
            self.setFont(font)
            self._refresh_layout_after_font_change()
            self.fontSizeChanged.emit(font.pointSize())

    def zoomOut(self):
        font = self.font()
        size = font.pointSize()
        if size > g_MIN_FONT_SIZE:
            font.setPointSize(size - 1)
            self.setFont(font)
            self._refresh_layout_after_font_change()
            self.fontSizeChanged.emit(font.pointSize())

    def _refresh_layout_after_font_change(self):
        # 행 높이/열 너비 갱신
        try:
            self.resizeRowsToContents()
            self.resizeColumnToContents(0)
            self.resizeColumnToContents(1)
        except Exception:
            pass
        self.viewport().update()

    def copy_range_from_current_row(self):
        """
        현재 active row의 0번째 컬럼(LineNumber)에서 시작하여
        다음 row의 0번째 컬럼 LineNumber 이전까지의 내용을 복사.
        마지막 행일 경우 파일 끝까지 복사.
        NUL 문자 제거 후 복사.
        """
        model = self.model()
        if not model:
            return

        current_index = self.currentIndex()
        if not current_index.isValid():
            return

        current_row = current_index.row()

        # 현재 행의 LineNumber (0번째 컬럼)
        start_line_data = model.data(model.index(current_row, 0), Qt.DisplayRole)

        try:
            start_line = int(str(start_line_data))
        except (ValueError, TypeError):
            return

        # 마지막 행인지 확인
        is_last_row = (current_row + 1 >= model.rowCount())

        if is_last_row:
            # 마지막 행이면 파일 끝까지 복사
            end_line = -1  # -1은 파일 끝을 의미
        else:
            # 다음 행의 LineNumber (0번째 컬럼)
            end_line_data = model.data(model.index(current_row + 1, 0), Qt.DisplayRole)
            try:
                end_line = int(str(end_line_data)) - 1  # 다음 행의 이전 줄까지
            except (ValueError, TypeError):
                return

        # TabContent의 복사 메서드 호출
        parent = self.parent()
        while parent:
            if parent.__class__.__name__ == 'TabContent':
                if is_last_row:
                    parent.copy_lines_to_end_remove_nul(start_line)
                else:
                    parent.copy_lines_range_remove_nul(start_line, end_line)
                break
            parent = parent.parent()

    # ---- Ctrl+C 복사, Ctrl+A 전체 선택 (focus가 있을 때만) ----
    def keyPressEvent(self, event: QtGui.QKeyEvent):
        # tblResults에 focus가 있을 때 Ctrl+Shift+C로 범위 복사
        if self.hasFocus() and event.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier) and event.key() == Qt.Key_C:
            self.copy_range_from_current_row()
            event.accept()
            return

        # tblResults에 focus가 있을 때 F2/Shift+F2로 마킹된 row 이동
        if self.hasFocus() and event.key() == Qt.Key_F2:
            if event.modifiers() == Qt.ShiftModifier:
                parent = self.parent()
                while parent:
                    if hasattr(parent, 'goto_prev_marked_result_from_table'):
                        parent.goto_prev_marked_result_from_table()
                        event.accept()
                        return
                    parent = parent.parent()
            else:
                parent = self.parent()
                while parent:
                    if hasattr(parent, 'goto_next_marked_result_from_table'):
                        parent.goto_next_marked_result_from_table()
                        event.accept()
                        return
                    parent = parent.parent()
            event.accept()
            return

        # F3/F4 처리 추가 (focus가 있을 때만)
        if self.hasFocus():
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

        # Ctrl+C 복사, Ctrl+A 전체 선택 (focus가 있을 때만)
        if self.hasFocus():
            if event.matches(QtGui.QKeySequence.Copy):
                self.copy_selected_rows_to_clipboard()
                event.accept()
                return
            if event.matches(QtGui.QKeySequence.SelectAll):
                self.selectAll()
                event.accept()
                return
        super().keyPressEvent(event)

    def copy_selected_rows_to_clipboard(self):
        model = self.model()
        sel_model = self.selectionModel()
        if not model or not sel_model:
            return
        # 선택된 모든 인덱스에서 행 번호만 모아 정렬
        rows = sorted({idx.row() for idx in sel_model.selectedIndexes()})
        if not rows:
            return

        lines = []
        for r in rows:
            c0 = model.data(model.index(r, 0), Qt.DisplayRole)
            c1 = model.data(model.index(r, 1), Qt.DisplayRole)
            c0 = "" if c0 is None else str(c0)
            c1 = "" if c1 is None else str(c1)
            # 탭으로 컬럼 구분, 행은 줄바꿈
            lines.append(f"{c0}\t{c1}")

        QtWidgets.QApplication.clipboard().setText("\n".join(lines))
