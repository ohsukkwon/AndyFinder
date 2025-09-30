# -*- coding: utf-8 -*-
import sys
import os
import re
import json
from datetime import datetime
from dataclasses import dataclass
from typing import List, Tuple, Optional

import chardet
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, Signal, QObject, QModelIndex, QTimer

# ------------------------------ 버전 관리 ------------------------------
VER_INFO__ver_1_250102_0001 = "ver_1_250102_0001"
VER_DESC__ver_1_250102_0001 = '''
1. Highlight Color 유지 기능 추가 - lineView의 mouse event에도 Color 하이라이트 유지.
2. 프로그램 Title에 버전 정보 추가.
3. 북마크 기능 추가 - Line Number 더블클릭으로 북마크 토글, F2/Shift+F2로 이동.
4. 설정 저장/불러오기 기능 추가.
5. 즐겨찾기 기능 추가 (edt_query, edt_result_search, edt_color_keywords).
6. F5 단축키 추가 (edt_query: 검색, edt_color_keywords: 설정).
7. lineView 내부 검색 기능 추가 (Ctrl+F, F3/F4로 이동).
8. Long Click시 바로 입력 UI 제공 후 즐겨찾기 목록 표시.
9. lineView 검색 다이얼로그 Modeless 변경.
10. Ctrl+F 실행시 선택된 텍스트를 검색어로 자동 입력.
11. tblResults row 더블클릭으로 Light Green 마킹 토글 기능 추가.
12. tblResults에서 F2/Shift+F2로 마킹된 row 이동 기능 추가.
'''

# # # # # # # # # # # # # # # # Config # # # # # # # # # # # # # # # # # #
gCurVerInfo = VER_INFO__ver_1_250102_0001
gCurVerDesc = VER_DESC__ver_1_250102_0001
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


# ------------------------------ Global 변수 ------------------------------
g_font_face = 'Arial'
g_font_size = 9


# ------------------------------ 데이터 구조 ------------------------------

@dataclass
class SearchResult:
    line: int
    snippet: str
    matches: List[Tuple[int, int]]  # (start, end) in snippet string


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
            # 부모 윈도우의 do_search 호출
            parent = self.parent()
            while parent:
                if isinstance(parent, QtWidgets.QMainWindow):
                    parent.do_search()
                    event.accept()
                    return
                parent = parent.parent()
        super().keyPressEvent(event)


class ColorKeywordsLineEdit(LongClickLineEdit):
    """F5로 설정을 적용하는 LineEdit"""

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F5:
            # 부모 윈도우의 on_color_settings_clicked 호출
            parent = self.parent()
            while parent:
                if isinstance(parent, QtWidgets.QMainWindow):
                    parent.on_color_settings_clicked()
                    event.accept()
                    return
                parent = parent.parent()
        super().keyPressEvent(event)


# ------------------------------ LineView 검색 다이얼로그 (Modeless) ------------------------------

class LineViewSearchDialog(QtWidgets.QDialog):
    """lineView 내부 검색 다이얼로그 (Modeless)"""

    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.setWindowTitle("텍스트 검색")
        self.setModal(False)  # Modeless로 변경
        self.editor = editor
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # 검색어 입력
        form_layout = QtWidgets.QFormLayout()
        self.edt_search = QtWidgets.QLineEdit()
        self.edt_search.setPlaceholderText("정규표현식 입력...")
        form_layout.addRow("검색어:", self.edt_search)
        layout.addLayout(form_layout)

        # 되돌이 검색
        self.chk_recursive = QtWidgets.QCheckBox("되돌이 검색")
        self.chk_recursive.setChecked(False)
        layout.addWidget(self.chk_recursive)

        # 상태 표시
        self.lbl_status = QtWidgets.QLabel("")
        layout.addWidget(self.lbl_status)

        # 버튼들
        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_prev = QtWidgets.QPushButton("Prev (F3)")
        self.btn_next = QtWidgets.QPushButton("Next (F4)")
        self.btn_close = QtWidgets.QPushButton("닫기")

        btn_layout.addWidget(self.btn_prev)
        btn_layout.addWidget(self.btn_next)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

        # 시그널
        self.edt_search.returnPressed.connect(self.on_search_next)
        self.btn_prev.clicked.connect(self.on_search_prev)
        self.btn_next.clicked.connect(self.on_search_next)
        self.btn_close.clicked.connect(self.close)

        self.resize(500, 150)

    def on_search_next(self):
        pattern = self.edt_search.text()
        recursive = self.chk_recursive.isChecked()
        result = self.editor.search_next(pattern, recursive)
        self.update_status(result)

    def on_search_prev(self):
        pattern = self.edt_search.text()
        recursive = self.chk_recursive.isChecked()
        result = self.editor.search_prev(pattern, recursive)
        self.update_status(result)

    def update_status(self, result):
        if result:
            current, total = result
            self.lbl_status.setText(f"{current} / {total}")
        else:
            self.lbl_status.setText("일치하는 항목 없음")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F3:
            self.on_search_prev()
            event.accept()
            return
        elif event.key() == Qt.Key_F4:
            self.on_search_next()
            event.accept()
            return
        elif event.key() == Qt.Key_Escape:
            self.close()
            event.accept()
            return
        super().keyPressEvent(event)


# ------------------------------ 즐겨찾기 추가 다이얼로그 ------------------------------

class FavoriteAddDialog(QtWidgets.QDialog):
    """즐겨찾기 추가를 위한 입력 다이얼로그"""

    def __init__(self, current_value="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("즐겨찾기 추가")
        self.current_value = current_value
        self.name = ""
        self.value = ""
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # 입력 폼
        form_layout = QtWidgets.QFormLayout()

        self.edt_name = QtWidgets.QLineEdit()
        self.edt_name.setPlaceholderText("즐겨찾기 이름 입력...")
        form_layout.addRow("이름:", self.edt_name)

        self.edt_value = QtWidgets.QLineEdit()
        self.edt_value.setText(self.current_value)
        self.edt_value.setPlaceholderText("값 입력...")
        form_layout.addRow("값:", self.edt_value)

        layout.addLayout(form_layout)

        # 버튼
        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_save = QtWidgets.QPushButton("Save")
        self.btn_cancel = QtWidgets.QPushButton("Cancel")

        btn_layout.addStretch()
        self.btn_save.setDefault(True)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        # 시그널
        self.btn_save.clicked.connect(self.on_save)
        self.btn_cancel.clicked.connect(self.reject)

        self.resize(500, 150)

        # 이름 필드에 포커스
        self.edt_name.setFocus()

    def on_save(self):
        name = self.edt_name.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "경고", "이름을 입력하세요.")
            return

        self.name = name
        self.value = self.edt_value.text()
        self.accept()


# ------------------------------ 즐겨찾기 다이얼로그 ------------------------------

class FavoriteDialog(QtWidgets.QDialog):
    """즐겨찾기 관리 다이얼로그"""

    def __init__(self, title, json_path, current_value="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.json_path = json_path
        self.current_value = current_value
        self.favorites = self.load_favorites()
        self.selected_value = None
        self.setup_ui()

    def load_favorites(self):
        """즐겨찾기 로드"""
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('favorites', [])
            except Exception as e:
                print(f"즐겨찾기 로드 실패: {e}")
                return []
        return []

    def save_favorites(self):
        """즐겨찾기 저장"""
        try:
            os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump({'favorites': self.favorites}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"저장 실패: {e}")

    def setup_ui(self):
        """UI 구성"""
        layout = QtWidgets.QVBoxLayout(self)

        # 안내 레이블
        info_label = QtWidgets.QLabel("더블클릭 또는 선택 버튼으로 항목을 선택할 수 있습니다.")
        layout.addWidget(info_label)

        # 리스트
        self.list_widget = QtWidgets.QListWidget()
        self.refresh_list()
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.list_widget)

        # 버튼들
        btn_layout = QtWidgets.QHBoxLayout()

        self.btn_add = QtWidgets.QPushButton("추가")
        self.btn_edit = QtWidgets.QPushButton("수정")
        self.btn_delete = QtWidgets.QPushButton("삭제")
        self.btn_select = QtWidgets.QPushButton("선택")
        self.btn_close = QtWidgets.QPushButton("닫기")

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_select)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

        # 시그널 연결
        self.btn_add.clicked.connect(self.add_favorite)
        self.btn_edit.clicked.connect(self.edit_favorite)
        self.btn_delete.clicked.connect(self.delete_favorite)
        self.btn_select.clicked.connect(self.select_favorite)
        self.btn_close.clicked.connect(self.reject)

        self.resize(600, 400)

    def refresh_list(self):
        """리스트 갱신"""
        self.list_widget.clear()
        for fav in self.favorites:
            item = QtWidgets.QListWidgetItem(f"{fav['name']}: {fav['value']}")
            self.list_widget.addItem(item)

    def add_favorite(self):
        """즐겨찾기 추가"""
        name, ok1 = QtWidgets.QInputDialog.getText(self, "이름 입력", "즐겨찾기 이름:")
        if not ok1 or not name.strip():
            return

        value, ok2 = QtWidgets.QInputDialog.getText(self, "값 입력", "값:", text=self.current_value)
        if not ok2:
            return

        self.favorites.append({'name': name.strip(), 'value': value})
        self.save_favorites()
        self.refresh_list()

    def edit_favorite(self):
        """즐겨찾기 수정"""
        current = self.list_widget.currentRow()
        if current < 0:
            QtWidgets.QMessageBox.warning(self, "경고", "수정할 항목을 선택하세요.")
            return

        fav = self.favorites[current]

        name, ok1 = QtWidgets.QInputDialog.getText(self, "이름 수정", "이름:", text=fav['name'])
        if not ok1:
            return

        value, ok2 = QtWidgets.QInputDialog.getText(self, "값 수정", "값:", text=fav['value'])
        if not ok2:
            return

        self.favorites[current] = {'name': name.strip(), 'value': value}
        self.save_favorites()
        self.refresh_list()

    def delete_favorite(self):
        """즐겨찾기 삭제"""
        current = self.list_widget.currentRow()
        if current < 0:
            QtWidgets.QMessageBox.warning(self, "경고", "삭제할 항목을 선택하세요.")
            return

        reply = QtWidgets.QMessageBox.question(
            self, "확인", "선택한 항목을 삭제하시겠습니까?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            del self.favorites[current]
            self.save_favorites()
            self.refresh_list()

    def select_favorite(self):
        """즐겨찾기 선택"""
        current = self.list_widget.currentRow()
        if current < 0:
            QtWidgets.QMessageBox.warning(self, "경고", "선택할 항목을 선택하세요.")
            return

        self.selected_value = self.favorites[current]['value']
        self.accept()

    def on_item_double_clicked(self, item):
        """아이템 더블클릭"""
        self.select_favorite()


# ------------------------------ 설정 저장/불러오기 다이얼로그 ------------------------------

class ConfigSaveDialog(QtWidgets.QDialog):
    """설정 저장 다이얼로그"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("설정 저장")
        self.config_name = ""
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # 이름 입력
        form_layout = QtWidgets.QFormLayout()
        self.edt_name = QtWidgets.QLineEdit()
        self.edt_name.setPlaceholderText("예: dumpstate구조")
        # 기본 문자열을 'default'로 설정
        self.edt_name.setText("default")
        form_layout.addRow("설정 이름:", self.edt_name)
        layout.addLayout(form_layout)

        # 안내
        info_label = QtWidgets.QLabel(
            "파일명 형식: index_날짜_시간_이름.json\n"
            "예: 0001_20250102_143022_dumpstate구조.json"
        )
        info_label.setStyleSheet("color: gray;")
        layout.addWidget(info_label)

        # 버튼
        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_ok = QtWidgets.QPushButton("저장")
        self.btn_cancel = QtWidgets.QPushButton("취소")
        btn_layout.addStretch()
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.resize(400, 150)

    def accept(self):
        name = self.edt_name.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "경고", "설정 이름을 입력하세요.")
            return
        self.config_name = name
        super().accept()


class ConfigLoadDialog(QtWidgets.QDialog):
    """설정 불러오기 다이얼로그"""

    def __init__(self, config_dir, parent=None):
        super().__init__(parent)
        self.setWindowTitle("설정 불러오기")
        self.config_dir = config_dir
        self.selected_file = None
        self.setup_ui()
        self.load_config_list()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # 리스트
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.list_widget)

        # 버튼
        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_load = QtWidgets.QPushButton("불러오기")
        self.btn_delete = QtWidgets.QPushButton("삭제")
        self.btn_cancel = QtWidgets.QPushButton("취소")
        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        # 시그널
        self.btn_load.clicked.connect(self.load_config)
        self.btn_delete.clicked.connect(self.delete_config)
        self.btn_cancel.clicked.connect(self.reject)

        self.resize(600, 400)

    def load_config_list(self):
        """설정 파일 목록 로드"""
        self.list_widget.clear()

        if not os.path.exists(self.config_dir):
            return

        files = [f for f in os.listdir(self.config_dir) if f.endswith('.json')]
        files.sort(reverse=True)  # 최신 파일이 위로

        for filename in files:
            self.list_widget.addItem(filename)

    def load_config(self):
        """설정 불러오기"""
        current_item = self.list_widget.currentItem()
        if not current_item:
            QtWidgets.QMessageBox.warning(self, "경고", "불러올 설정을 선택하세요.")
            return

        self.selected_file = os.path.join(self.config_dir, current_item.text())
        self.accept()

    def delete_config(self):
        """설정 삭제"""
        current_item = self.list_widget.currentItem()
        if not current_item:
            QtWidgets.QMessageBox.warning(self, "경고", "삭제할 설정을 선택하세요.")
            return

        reply = QtWidgets.QMessageBox.question(
            self, "확인",
            f"'{current_item.text()}' 설정을 삭제하시겠습니까?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            try:
                file_path = os.path.join(self.config_dir, current_item.text())
                os.remove(file_path)
                self.load_config_list()
                QtWidgets.QMessageBox.information(self, "완료", "설정이 삭제되었습니다.")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "오류", f"삭제 실패: {e}")

    def on_item_double_clicked(self, item):
        """아이템 더블클릭"""
        self.load_config()


# ------------------------------ 라인 번호가 있는 텍스트 에디터 ------------------------------

class LineNumberArea(QtWidgets.QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.codeEditor = editor

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
                if top <= event.pos().y() <= bottom:
                    line_number = block.blockNumber() + 1
                    self.codeEditor.toggle_bookmark(line_number)
                    break

                block = block.next()
                top = bottom
                bottom = top + self.codeEditor.blockBoundingRect(block).height()

        super().mouseDoubleClickEvent(event)


class CodeEditor(QtWidgets.QPlainTextEdit):
    def __init__(self):
        super().__init__()
        self.lineNumberArea = LineNumberArea(self)
        self.color_highlight_selections = []
        self.bookmarks = set()

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

    def toggle_bookmark(self, line_number):
        """북마크 토글 (1-based)"""
        if line_number in self.bookmarks:
            self.bookmarks.remove(line_number)
        else:
            self.bookmarks.add(line_number)
        self.lineNumberArea.update()

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
        extraSelections = []
        extraSelections.extend(self.color_highlight_selections)

        if not self.isReadOnly():
            selection = QtWidgets.QTextEdit.ExtraSelection()
            lineColor = QtGui.QColor(232, 242, 254)
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
        if event.modifiers() == Qt.ControlModifier:
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
        if size < 72:
            font.setPointSize(size + 1)
            self.setFont(font)

    def zoomOut(self):
        font = self.font()
        size = font.pointSize()
        if size > 6:
            font.setPointSize(size - 1)
            self.setFont(font)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F2:
            if event.modifiers() == Qt.ShiftModifier:
                self.goto_previous_bookmark()
            else:
                self.goto_next_bookmark()
            event.accept()
            return
        super().keyPressEvent(event)


# ------------------------------ 파일 로더(백그라운드) ------------------------------

class FileLoader(QObject):
    progress = Signal(int)
    finished = Signal(str, str)
    failed = Signal(str)

    def __init__(self, path: str):
        super().__init__()
        self.path = path
        self._stop = False

    def stop(self):
        self._stop = True

    def detect_encoding(self, sample: bytes) -> str:
        try:
            guess = chardet.detect(sample)
            enc = guess.get('encoding') or 'utf-8'
            if enc and enc.lower() in ('ascii',):
                return 'utf-8'
            return enc or 'utf-8'
        except Exception:
            return 'utf-8'

    @QtCore.Slot()
    def run(self):
        try:
            size = os.path.getsize(self.path)
            sample_size = min(1024 * 1024, size)
            with open(self.path, 'rb') as f:
                sample = f.read(sample_size)
            encoding = self.detect_encoding(sample)
            self.progress.emit(10)

            with open(self.path, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()

            self.progress.emit(100)
            self.finished.emit(content, encoding)
        except Exception as e:
            self.failed.emit(str(e))


# ------------------------------ 검색기(백그라운드) ------------------------------

class SearchWorker(QObject):
    progress = Signal(int)
    finished = Signal(list)
    failed = Signal(str)
    message = Signal(str)

    def __init__(self, content: str, query: str, mode: str, case_sensitive: bool):
        super().__init__()
        self.content = content
        self.lines = content.split('\n')
        self.query = query
        self.mode = mode
        self.case_sensitive = case_sensitive
        self._stop = False

    def stop(self):
        self._stop = True

    def build_matcher(self):
        text = self.query.strip()
        if not text:
            return None

        flags = 0 if self.case_sensitive else re.IGNORECASE

        if self.mode == 'regex':
            try:
                regex = re.compile(text, flags)
            except re.error as e:
                raise ValueError(f'정규식 오류: {e}')

            def fn_regex(s, rx=regex):
                return [(m.start(), m.end()) for m in rx.finditer(s)]

            return fn_regex
        else:
            needle = text if self.case_sensitive else text.lower()

            def fn_plain(s, n=needle, cs=self.case_sensitive):
                hay = s if cs else s.lower()
                spans = []
                start = 0
                ln = len(n)
                if ln == 0:
                    return spans
                while True:
                    pos = hay.find(n, start)
                    if pos == -1:
                        break
                    spans.append((pos, pos + ln))
                    start = pos + ln if ln > 0 else pos + 1
                return spans

            return fn_plain

    @QtCore.Slot()
    def run(self):
        try:
            matcher = self.build_matcher()
            if not matcher:
                self.finished.emit([])
                return

            results: List[SearchResult] = []
            total = len(self.lines)

            for idx, line_idx in enumerate(range(0, total)):
                if self._stop:
                    break

                s = self.lines[line_idx]
                spans = matcher(s)
                if spans:
                    results.append(SearchResult(line=line_idx, snippet=s, matches=spans))

                if idx % 1000 == 0:
                    self.progress.emit(int((idx / max(1, total)) * 100))

            self.progress.emit(100)
            self.finished.emit(results)
        except Exception as e:
            self.failed.emit(str(e))


# ------------------------------ DragDropCodeEditor (내부 검색 지원) ------------------------------

class DragDropCodeEditor(CodeEditor):
    """Drag & Drop이 가능하고 내부 검색을 지원하는 CodeEditor"""
    fileDropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__()
        self.setAcceptDrops(True)

        # 내부 검색 상태
        self.internal_search_pattern = ""
        self.internal_search_matches = []
        self.internal_search_index = -1
        self.search_dialog = None

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                file_path = urls[0].toLocalFile()
                self.fileDropped.emit(file_path)
                event.acceptProposedAction()
            return
        super().dropEvent(event)

    def show_search_dialog(self):
        """검색 다이얼로그 표시 (선택된 텍스트를 검색어로 사용)"""
        if self.search_dialog is None:
            self.search_dialog = LineViewSearchDialog(self, self.window())

        # 선택된 텍스트 확인
        cursor = self.textCursor()
        selected_text = cursor.selectedText()

        self.search_dialog.show()
        self.search_dialog.raise_()
        self.search_dialog.activateWindow()
        self.search_dialog.edt_search.setFocus()

        # 선택된 텍스트가 있으면 그것을 표시, 없으면 이전 검색어 표시
        if selected_text:
            self.search_dialog.edt_search.setText(selected_text)
        elif self.internal_search_pattern:
            self.search_dialog.edt_search.setText(self.internal_search_pattern)

        self.search_dialog.edt_search.selectAll()

    def find_all_matches(self, pattern):
        """모든 매칭 위치 찾기"""
        if not pattern:
            return []

        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            return []

        content = self.toPlainText()
        matches = []

        for match in regex.finditer(content):
            matches.append((match.start(), match.end()))

        return matches

    def search_next(self, pattern, recursive=True):
        """다음 검색 결과로 이동"""
        if not pattern:
            return None

        # 패턴이 변경되었으면 다시 검색
        if pattern != self.internal_search_pattern:
            self.internal_search_pattern = pattern
            self.internal_search_matches = self.find_all_matches(pattern)
            self.internal_search_index = -1

        if not self.internal_search_matches:
            return None

        # 현재 커서 위치: 선택이 있으면 선택 끝, 없으면 현재 위치
        cursor = self.textCursor()
        if cursor.hasSelection():
            cursor_pos = cursor.selectionEnd()
        else:
            cursor_pos = cursor.position()

        # 현재 위치 이후의 매칭 찾기
        found = False
        for i, (start, end) in enumerate(self.internal_search_matches):
            if start > cursor_pos:
                self.internal_search_index = i
                found = True
                break

        # 찾지 못했으면 처음부터
        if not found:
            if recursive:
                self.internal_search_index = 0
            else:
                return (len(self.internal_search_matches), len(self.internal_search_matches))

        # 해당 위치로 이동
        start, end = self.internal_search_matches[self.internal_search_index]
        cursor = self.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, QtGui.QTextCursor.KeepAnchor)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
        self.centerCursor()

        return (self.internal_search_index + 1, len(self.internal_search_matches))

    def search_prev(self, pattern, recursive=True):
        """이전 검색 결과로 이동"""
        if not pattern:
            return None

        # 패턴이 변경되었으면 다시 검색
        if pattern != self.internal_search_pattern:
            self.internal_search_pattern = pattern
            self.internal_search_matches = self.find_all_matches(pattern)
            self.internal_search_index = len(self.internal_search_matches)

        if not self.internal_search_matches:
            return None

        # 현재 커서 위치: 선택이 있으면 선택 시작, 없으면 현재 위치
        cursor = self.textCursor()
        if cursor.hasSelection():
            cursor_pos = min(cursor.selectionStart(), cursor.selectionEnd())
        else:
            cursor_pos = cursor.position()

        # 현재 위치 이전의 매칭 찾기 (현재 매치가 선택되어 있으면 그 이전으로 가야 함)
        found = False
        for i in range(len(self.internal_search_matches) - 1, -1, -1):
            start, end = self.internal_search_matches[i]
            if start < cursor_pos:
                self.internal_search_index = i
                found = True
                break

        # 찾지 못했으면 마지막으로
        if not found:
            if recursive:
                self.internal_search_index = len(self.internal_search_matches) - 1
            else:
                return (1, len(self.internal_search_matches))

        # 해당 위치로 이동
        start, end = self.internal_search_matches[self.internal_search_index]
        cursor = self.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, QtGui.QTextCursor.KeepAnchor)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
        self.centerCursor()

        return (self.internal_search_index + 1, len(self.internal_search_matches))

    def keyPressEvent(self, event):
        # Ctrl+F: 검색 다이얼로그 표시
        if event.key() == Qt.Key_F and event.modifiers() == Qt.ControlModifier:
            self.show_search_dialog()
            event.accept()
            return

        # F3: 이전 검색 결과 (검색 다이얼로그가 열려있을 때만)
        if event.key() == Qt.Key_F3 and self.search_dialog and self.search_dialog.isVisible():
            recursive = self.search_dialog.chk_recursive.isChecked()
            # 현재 다이얼로그의 입력값을 사용하도록 수정
            pattern = self.search_dialog.edt_search.text()
            result = self.search_prev(pattern, recursive)
            if self.search_dialog:
                self.search_dialog.update_status(result)
            event.accept()
            return

        # F4: 다음 검색 결과 (검색 다이얼로그가 열려있을 때만)
        if event.key() == Qt.Key_F4 and self.search_dialog and self.search_dialog.isVisible():
            recursive = self.search_dialog.chk_recursive.isChecked()
            # 현재 다이얼로그의 입력값을 사용하도록 수정
            pattern = self.search_dialog.edt_search.text()
            result = self.search_next(pattern, recursive)
            if self.search_dialog:
                self.search_dialog.update_status(result)
            event.accept()
            return

        super().keyPressEvent(event)


# ------------------------------ Results Model (마킹 기능 추가) ------------------------------

class ResultsModel(QtCore.QAbstractTableModel):
    HEADERS = ["Line", "검색결과"]

    def __init__(self):
        super().__init__()
        self.rows: List[SearchResult] = []
        self.marked_rows: set = set()  # 마킹된 row 인덱스들

    def set_results(self, rows: List[SearchResult]):
        self.beginResetModel()
        self.rows = rows
        self.marked_rows.clear()  # 결과가 바뀌면 마킹 초기화
        self.endResetModel()

    def toggle_mark(self, row: int):
        """row 마킹 토글"""
        if row < 0 or row >= len(self.rows):
            return

        if row in self.marked_rows:
            self.marked_rows.remove(row)
        else:
            self.marked_rows.add(row)

        # 해당 row 업데이트
        self.dataChanged.emit(
            self.index(row, 0),
            self.index(row, self.columnCount() - 1)
        )

    def is_marked(self, row: int) -> bool:
        return row in self.marked_rows

    def get_next_marked_row(self, current_row: int) -> int:
        """현재 row 다음의 마킹된 row 반환, 없으면 -1"""
        if not self.marked_rows:
            return -1

        marked_list = sorted(self.marked_rows)
        for row in marked_list:
            if row > current_row:
                return row
        return -1

    def get_prev_marked_row(self, current_row: int) -> int:
        """현재 row 이전의 마킹된 row 반환, 없으면 -1"""
        if not self.marked_rows:
            return -1

        marked_list = sorted(self.marked_rows, reverse=True)
        for row in marked_list:
            if row < current_row:
                return row
        return -1

    def rowCount(self, parent=QModelIndex()):
        return len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 2

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        r = self.rows[index.row()]
        c = index.column()

        if role == Qt.DisplayRole:
            if c == 0:
                return str(r.line + 1)
            elif c == 1:
                return r.snippet
        elif role == Qt.BackgroundRole:
            # 마킹된 row는 light green 배경
            if index.row() in self.marked_rows:
                return QtGui.QColor(144, 238, 144)  # light green
        elif role == Qt.UserRole:
            return r

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return str(section + 1)

    def get(self, row: int) -> SearchResult:
        return self.rows[row]


# ------------------------------ 메인 윈도우 ------------------------------

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Dumpstate Finder - {gCurVerInfo}")
        self.resize(1300, 800)

        # 상태
        self.content: str = ""
        self.encoding: str = 'utf-8'
        self.search_thread: Optional[QtCore.QThread] = None
        self.search_worker: Optional[SearchWorker] = None
        self.file_thread: Optional[QtCore.QThread] = None
        self.file_loader: Optional[FileLoader] = None
        self.current_results: List[SearchResult] = []
        self.current_result_index: int = -1
        self.current_file_path: str = ""
        self.is_modified: bool = False

        self.result_search_query: str = ""
        self.result_search_index: int = -1
        self.result_search_matches: List[int] = []

        self.color_keywords: List[Tuple[str, QtGui.QColor]] = []

        # 50가지 색상 팔레트
        self.color_palette = [
            QtGui.QColor(255, 255, 200), QtGui.QColor(255, 200, 200), QtGui.QColor(200, 255, 200),
            QtGui.QColor(200, 220, 255), QtGui.QColor(255, 200, 255), QtGui.QColor(200, 255, 255),
            QtGui.QColor(255, 220, 180), QtGui.QColor(230, 200, 255), QtGui.QColor(255, 240, 200),
            QtGui.QColor(220, 255, 220), QtGui.QColor(240, 200, 200), QtGui.QColor(200, 240, 255),
            QtGui.QColor(255, 230, 230), QtGui.QColor(230, 255, 230), QtGui.QColor(230, 230, 255),
            QtGui.QColor(255, 255, 230), QtGui.QColor(255, 230, 255), QtGui.QColor(230, 255, 255),
            QtGui.QColor(255, 210, 180), QtGui.QColor(210, 255, 180), QtGui.QColor(180, 210, 255),
            QtGui.QColor(255, 180, 210), QtGui.QColor(210, 180, 255), QtGui.QColor(180, 255, 210),
            QtGui.QColor(255, 235, 180), QtGui.QColor(235, 180, 255), QtGui.QColor(180, 255, 235),
            QtGui.QColor(255, 200, 230), QtGui.QColor(200, 230, 255), QtGui.QColor(230, 255, 200),
            QtGui.QColor(255, 190, 200), QtGui.QColor(190, 255, 200), QtGui.QColor(200, 190, 255),
            QtGui.QColor(255, 245, 190), QtGui.QColor(245, 190, 255), QtGui.QColor(190, 245, 255),
            QtGui.QColor(255, 215, 200), QtGui.QColor(215, 200, 255), QtGui.QColor(200, 255, 215),
            QtGui.QColor(255, 200, 215), QtGui.QColor(245, 255, 200), QtGui.QColor(200, 245, 255),
            QtGui.QColor(255, 225, 215), QtGui.QColor(225, 215, 255), QtGui.QColor(215, 255, 225),
            QtGui.QColor(255, 210, 225), QtGui.QColor(210, 225, 255), QtGui.QColor(225, 255, 210),
            QtGui.QColor(255, 235, 210), QtGui.QColor(235, 210, 255),
        ]

        self._build_ui()
        self._create_menus()

    def _create_menus(self):
        menubar = self.menuBar()

        # 파일 메뉴
        file_menu = menubar.addMenu('파일(&F)')

        open_action = QtGui.QAction('열기(&O)', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QtGui.QAction('저장(&S)', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        # 설정 저장/불러오기
        save_config_action = QtGui.QAction('설정 저장(&C)', self)
        save_config_action.setShortcut('Ctrl+Shift+S')
        save_config_action.triggered.connect(self.save_config)
        file_menu.addAction(save_config_action)

        load_config_action = QtGui.QAction('설정 불러오기(&L)', self)
        load_config_action.setShortcut('Ctrl+Shift+O')
        load_config_action.triggered.connect(self.load_config)
        file_menu.addAction(load_config_action)

        file_menu.addSeparator()

        exit_action = QtGui.QAction('종료(&X)', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 편집 메뉴
        edit_menu = menubar.addMenu('편집(&E)')

        find_action = QtGui.QAction('찾기(&F)', self)
        find_action.setShortcut('Ctrl+F')
        find_action.triggered.connect(self.focus_search)
        edit_menu.addAction(find_action)

        # 보기 메뉴
        view_menu = menubar.addMenu('보기(&V)')

        zoom_in_action = QtGui.QAction('확대(&I)', self)
        zoom_in_action.setShortcut('Ctrl+=')
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QtGui.QAction('축소(&O)', self)
        zoom_out_action.setShortcut('Ctrl+-')
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)

        self.always_on_top_action = QtGui.QAction('항상위(&A)', self)
        self.always_on_top_action.setCheckable(True)
        self.always_on_top_action.toggled.connect(self.toggle_always_on_top)
        view_menu.addAction(self.always_on_top_action)

        # 검색 메뉴
        search_menu = menubar.addMenu('검색(&S)')

        search_action = QtGui.QAction('검색 실행(&S)', self)
        search_action.triggered.connect(self.do_search)
        search_menu.addAction(search_action)

        # 도움말 메뉴
        help_menu = menubar.addMenu('도움말(&H)')

        about_action = QtGui.QAction('정보(&A)', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def toggle_always_on_top(self, checked: bool):
        self.setWindowFlag(Qt.WindowStaysOnTopHint, checked)
        self.show()

    def focus_search(self):
        # lineView에 focus가 있으면 내부 검색 다이얼로그 표시
        if self.lineView.hasFocus():
            self.lineView.show_search_dialog()
        else:
            self.edt_query.setFocus()
            self.edt_query.selectAll()

    def zoom_in(self):
        self.lineView.zoomIn()

    def zoom_out(self):
        self.lineView.zoomOut()

    def show_about(self):
        QtWidgets.QMessageBox.about(
            self,
            "Dumpstate Searcher 정보",
            f"Dumpstate Searcher {gCurVerInfo}\n\n"
            "대용량 dumpstate 파일을 빠르게 검색하고 분석하는 도구입니다.\n\n"
            f"버전 정보:\n{gCurVerDesc}"
        )

    def _build_ui(self):
        top_widget = QtWidgets.QWidget()
        top_layout = QtWidgets.QVBoxLayout(top_widget)
        top_layout.setContentsMargins(6, 6, 6, 6)
        top_layout.setSpacing(4)

        # 첫 번째 줄
        first_row = QtWidgets.QWidget()
        first_layout = QtWidgets.QHBoxLayout(first_row)
        first_layout.setContentsMargins(0, 0, 0, 0)
        first_layout.setSpacing(8)

        self.btn_open = QtWidgets.QPushButton("열기")
        self.lbl_file = QtWidgets.QLabel("파일 없음")
        self.lbl_file.setMinimumWidth(300)
        self.lbl_file.setTextInteractionFlags(Qt.TextSelectableByMouse)

        first_layout.addWidget(self.btn_open)
        first_layout.addWidget(self.lbl_file, 1)

        # 두 번째 줄
        second_row = QtWidgets.QWidget()
        second_layout = QtWidgets.QHBoxLayout(second_row)
        second_layout.setContentsMargins(0, 0, 0, 0)
        second_layout.setSpacing(8)

        # 요청 1: edt_query 왼쪽에 라벨 추가
        self.lbl_query_title = QtWidgets.QLabel("기본 검색어 :")
        self.edt_query = QueryLineEdit()  # F5 단축키 지원
        self.edt_query.setPlaceholderText("검색어를 입력하세요 (Long Click으로 즐겨찾기, F5로 검색)")
        self.edt_query.returnPressed.connect(self.do_search)
        self.edt_query.longClicked.connect(self.show_query_favorites)
        self.edt_query.setStyleSheet("QLineEdit { background-color: lightyellow; }")

        second_layout.addWidget(self.lbl_query_title)
        second_layout.addWidget(self.edt_query, 1)

        # 세 번째 줄
        third_row = QtWidgets.QWidget()
        third_layout = QtWidgets.QHBoxLayout(third_row)
        third_layout.setContentsMargins(0, 0, 0, 0)
        third_layout.setSpacing(8)

        self.cmb_mode = QtWidgets.QComboBox()
        self.cmb_mode.addItems(["일반", "정규식"])
        self.cmb_mode.setCurrentIndex(1)
        self.cmb_mode.currentIndexChanged.connect(self.on_mode_changed)

        self.cmb_mode.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid #A0A0A0;
                padding: 4px;
                border-radius: 2px;
            }
            QComboBox:hover {
                border: 1px solid #0078D7;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                selection-background-color: yellow;
                selection-color: red;
            }
        """)

        self.chk_case = QtWidgets.QCheckBox("대소문자")

        self.btn_search = QtWidgets.QPushButton("검색")
        self.btn_search.setStyleSheet("""
            QPushButton {
                background-color: lightblue;
                color: red;
                font-weight: bold;
            }
        """)

        # 요청 2: 검색/중지 사이에 previous/next lines 입력 추가 (QueryLineEdit)
        int_validator = QtGui.QIntValidator(0, 999999, self)
        self.edt_prev_lines = QueryLineEdit()
        self.edt_prev_lines.setValidator(int_validator)
        self.edt_prev_lines.setText("0")
        self.edt_prev_lines.setPlaceholderText("previous lines")
        self.edt_prev_lines.setFixedWidth(80)
        self.edt_prev_lines.setToolTip("매칭 라인 이전에 포함할 줄 수 (기본 0)")
        self.edt_prev_lines.editingFinished.connect(self.on_context_lines_changed)

        self.edt_next_lines = QueryLineEdit()
        self.edt_next_lines.setValidator(int_validator)
        self.edt_next_lines.setText("0")
        self.edt_next_lines.setPlaceholderText("next lines")
        self.edt_next_lines.setFixedWidth(80)
        self.edt_next_lines.setToolTip("매칭 라인 이후에 포함할 줄 수 (기본 0)")
        self.edt_next_lines.editingFinished.connect(self.on_context_lines_changed)

        self.btn_stop = QtWidgets.QPushButton("중지")
        self.btn_stop.setEnabled(False)
        self.prog = QtWidgets.QProgressBar()
        self.prog.setMaximumWidth(200)
        self.prog.setRange(0, 100)
        self.prog.setValue(0)

        third_layout.addWidget(QtWidgets.QLabel("검색모드:"))
        third_layout.addWidget(self.cmb_mode)
        third_layout.addWidget(self.chk_case)
        third_layout.addWidget(self.btn_search)

        # 요청 2: 여기서 두 개의 QueryLineEdit 추가 (검색과 중지 사이)
        third_layout.addWidget(self.edt_prev_lines)
        third_layout.addWidget(self.edt_next_lines)

        third_layout.addWidget(self.btn_stop)
        third_layout.addWidget(self.prog)
        third_layout.addStretch()

        # 네 번째 줄
        fourth_row = QtWidgets.QWidget()
        fourth_layout = QtWidgets.QHBoxLayout(fourth_row)
        fourth_layout.setContentsMargins(0, 0, 0, 0)
        fourth_layout.setSpacing(8)

        fourth_layout.addWidget(QtWidgets.QLabel("검색결과에서 검색(정규표현식):"))
        self.edt_result_search = LongClickLineEdit()
        self.edt_result_search.setPlaceholderText("검색 결과 내에서 검색... (Long Click으로 즐겨찾기)")
        self.edt_result_search.returnPressed.connect(self.search_in_results_next)
        self.edt_result_search.longClicked.connect(self.show_result_search_favorites)

        self.btn_result_search_prev = QtWidgets.QPushButton("이전 (F3)")
        self.btn_result_search_next = QtWidgets.QPushButton("다음 (F4)")
        self.lbl_result_search_status = QtWidgets.QLabel("")

        self.chk_recursive_search = QtWidgets.QCheckBox("되돌이 검색")
        self.chk_recursive_search.setChecked(False)

        fourth_layout.addWidget(self.edt_result_search, 1)
        fourth_layout.addWidget(self.btn_result_search_prev)
        fourth_layout.addWidget(self.btn_result_search_next)
        fourth_layout.addWidget(self.lbl_result_search_status)
        fourth_layout.addWidget(self.chk_recursive_search)
        fourth_layout.addStretch()

        # 다섯 번째 줄
        fifth_row = QtWidgets.QWidget()
        fifth_layout = QtWidgets.QHBoxLayout(fifth_row)
        fifth_layout.setContentsMargins(0, 0, 0, 0)
        fifth_layout.setSpacing(8)

        fifth_layout.addWidget(QtWidgets.QLabel("Highlight Color 설정:"))
        self.edt_color_keywords = ColorKeywordsLineEdit()  # F5 단축키 지원
        self.edt_color_keywords.setPlaceholderText("예: activity|window|package (Long Click으로 즐겨찾기, F5로 설정)")
        self.edt_color_keywords.longClicked.connect(self.show_color_keywords_favorites)

        self.btn_apply_colors = QtWidgets.QPushButton("설정")
        self.btn_apply_colors.clicked.connect(self.on_color_settings_clicked)

        self.btn_clear_colors = QtWidgets.QPushButton("Clear")
        self.btn_clear_colors.clicked.connect(self.on_color_clear_clicked)

        fifth_layout.addWidget(self.edt_color_keywords, 1)
        fifth_layout.addWidget(self.btn_apply_colors)
        fifth_layout.addWidget(self.btn_clear_colors)
        fifth_layout.addStretch()

        top_layout.addWidget(first_row)
        top_layout.addWidget(second_row)
        top_layout.addWidget(third_row)
        top_layout.addWidget(fourth_row)
        top_layout.addWidget(fifth_row)

        # 중앙
        splitter = QtWidgets.QSplitter()
        splitter.setOrientation(Qt.Vertical)

        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #0078D7;
                height: 3px;
                margin: 0px;
            }
            QSplitter::handle:vertical {
                height: 3px;
            }
        """)

        self.lineView = DragDropCodeEditor()
        self.lineView.setFont(QtGui.QFont(g_font_face, g_font_size))
        self.lineView.textChanged.connect(self.on_text_changed)
        self.lineView.fileDropped.connect(self.load_dropped_file)

        self.tblResults = QtWidgets.QTableView()
        self.tblResults.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tblResults.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tblResults.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tblResults.verticalHeader().setVisible(False)
        self.tblResults.setAlternatingRowColors(True)
        # 멀티라인 스니펫 표시 위해 wordWrap 활성화
        self.tblResults.setWordWrap(True)
        self.tblResults.setShowGrid(False)

        self.tblResults.setStyleSheet("""
            QTableView {
                color: black;
                background-color: white;
                alternate-background-color: #F0F0F0;
                selection-background-color: #0078D7;
                selection-color: white;
                gridline-color: #D0D0D0;
            }
            QHeaderView::section {
                background-color: #E0E0E0;
                padding: 4px;
                border: 1px solid #C0C0C0;
                font-weight: bold;
            }
        """)

        self.resultsModel = ResultsModel()
        self.tblResults.setModel(self.resultsModel)
        self.tblResults.doubleClicked.connect(self.on_table_double_clicked)

        splitter.addWidget(self.lineView)
        splitter.addWidget(self.tblResults)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        self.status = QtWidgets.QStatusBar()
        self.setStatusBar(self.status)

        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(top_widget)
        layout.addWidget(splitter, 1)
        self.setCentralWidget(central)

        # 시그널
        self.btn_open.clicked.connect(self.open_file)
        self.btn_search.clicked.connect(self.do_search)
        self.btn_stop.clicked.connect(self.stop_search)
        self.btn_result_search_prev.clicked.connect(self.search_in_results_prev)
        self.btn_result_search_next.clicked.connect(self.search_in_results_next)

        # F2/Shift+F2 단축키 (윈도우 전역에서 동작, 먼저 tblResults에 포커스를 주고 이동)
        self.sc_next_mark = QtGui.QShortcut(QtGui.QKeySequence("F2"), self)
        self.sc_next_mark.setContext(Qt.WindowShortcut)
        self.sc_next_mark.activated.connect(lambda: self.handle_marked_row_shortcut(next=True))

        self.sc_prev_mark = QtGui.QShortcut(QtGui.QKeySequence("Shift+F2"), self)
        self.sc_prev_mark.setContext(Qt.WindowShortcut)
        self.sc_prev_mark.activated.connect(lambda: self.handle_marked_row_shortcut(next=False))

        self.on_mode_changed(1)

    # ---------------- 마킹 관련 메서드 추가 ----------------
    def handle_marked_row_shortcut(self, next: bool):
        """F2/Shift+F2 단축키 처리: tblResults에 포커스 후 이동"""
        self.tblResults.setFocus(Qt.OtherFocusReason)
        if next:
            self.goto_next_marked_result()
        else:
            self.goto_prev_marked_result()

    def on_table_double_clicked(self, index: QModelIndex):
        """테이블 더블클릭: 마킹 토글 + 해당 라인으로 이동"""
        row = index.row()
        # 마킹 토글
        self.resultsModel.toggle_mark(row)
        # 기존의 이동 로직도 수행
        self.goto_result_from_table(index)

    def goto_next_marked_result(self):
        """다음 마킹된 결과로 이동 (F2)"""
        if not self.resultsModel.marked_rows:
            self.status.showMessage("마킹된 항목이 없습니다", 2000)
            return

        current_row = self.tblResults.currentIndex().row()
        next_row = self.resultsModel.get_next_marked_row(current_row if current_row is not None else -1)

        if next_row >= 0:
            index = self.resultsModel.index(next_row, 0)
            self.tblResults.setCurrentIndex(index)
            self.tblResults.scrollTo(index, QtWidgets.QAbstractItemView.PositionAtCenter)
            self.goto_result_from_table(index)
        else:
            self.status.showMessage("다음 마킹된 항목이 없습니다", 2000)

    def goto_prev_marked_result(self):
        """이전 마킹된 결과로 이동 (Shift+F2)"""
        if not self.resultsModel.marked_rows:
            self.status.showMessage("마킹된 항목이 없습니다", 2000)
            return

        current_row = self.tblResults.currentIndex().row()
        # 선택이 없을 때는 마지막 마킹으로 이동
        if current_row is None or current_row < 0:
            prev_row = max(self.resultsModel.marked_rows) if self.resultsModel.marked_rows else -1
        else:
            prev_row = self.resultsModel.get_prev_marked_row(current_row)

        if prev_row >= 0:
            index = self.resultsModel.index(prev_row, 0)
            self.tblResults.setCurrentIndex(index)
            self.tblResults.scrollTo(index, QtWidgets.QAbstractItemView.PositionAtCenter)
            self.goto_result_from_table(index)
        else:
            self.status.showMessage("이전 마킹된 항목이 없습니다", 2000)

    # ---------------- 즐겨찾기 관련 ----------------
    def show_query_favorites(self):
        """edt_query 즐겨찾기 - Long Click시 입력 다이얼로그 먼저 표시"""
        current_value = self.edt_query.text()

        # 1. 입력 다이얼로그 표시
        add_dialog = FavoriteAddDialog(current_value, self)
        add_result = add_dialog.exec()

        # 2. Save 선택시 즐겨찾기에 추가
        if add_result == QtWidgets.QDialog.Accepted:
            json_path = "./fav/edit_query.json"

            # 즐겨찾기 로드
            favorites = []
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        favorites = data.get('favorites', [])
                except Exception as e:
                    print(f"즐겨찾기 로드 실패: {e}")

            # 새 항목 추가
            favorites.append({'name': add_dialog.name, 'value': add_dialog.value})

            # 저장
            try:
                os.makedirs(os.path.dirname(json_path), exist_ok=True)
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump({'favorites': favorites}, f, ensure_ascii=False, indent=2)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "오류", f"저장 실패: {e}")

        # 3. Save든 Cancel이든 즐겨찾기 목록 다이얼로그 표시
        dialog = FavoriteDialog("검색어 즐겨찾기", "./fav/edit_query.json", current_value, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted and dialog.selected_value is not None:
            self.edt_query.setText(dialog.selected_value)

    def show_result_search_favorites(self):
        """edt_result_search 즐겨찾기 - Long Click시 입력 다이얼로그 먼저 표시"""
        current_value = self.edt_result_search.text()

        # 1. 입력 다이얼로그 표시
        add_dialog = FavoriteAddDialog(current_value, self)
        add_result = add_dialog.exec()

        # 2. Save 선택시 즐겨찾기에 추가
        if add_result == QtWidgets.QDialog.Accepted:
            json_path = "./fav/edt_result_search.json"

            # 즐겨찾기 로드
            favorites = []
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        favorites = data.get('favorites', [])
                except Exception as e:
                    print(f"즐겨찾기 로드 실패: {e}")

            # 새 항목 추가
            favorites.append({'name': add_dialog.name, 'value': add_dialog.value})

            # 저장
            try:
                os.makedirs(os.path.dirname(json_path), exist_ok=True)
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump({'favorites': favorites}, f, ensure_ascii=False, indent=2)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "오류", f"저장 실패: {e}")

        # 3. Save든 Cancel이든 즐겨찾기 목록 다이얼로그 표시
        dialog = FavoriteDialog("검색결과 검색 즐겨찾기", "./fav/edt_result_search.json", current_value, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted and dialog.selected_value is not None:
            self.edt_result_search.setText(dialog.selected_value)

    def show_color_keywords_favorites(self):
        """edt_color_keywords 즐겨찾기 - Long Click시 입력 다이얼로그 먼저 표시"""
        current_value = self.edt_color_keywords.text()

        # 1. 입력 다이얼로그 표시
        add_dialog = FavoriteAddDialog(current_value, self)
        add_result = add_dialog.exec()

        # 2. Save 선택시 즐겨찾기에 추가
        if add_result == QtWidgets.QDialog.Accepted:
            json_path = "./fav/edt_color_keywords.json"

            # 즐겨찾기 로드
            favorites = []
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        favorites = data.get('favorites', [])
                except Exception as e:
                    print(f"즐겨찾기 로드 실패: {e}")

            # 새 항목 추가
            favorites.append({'name': add_dialog.name, 'value': add_dialog.value})

            # 저장
            try:
                os.makedirs(os.path.dirname(json_path), exist_ok=True)
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump({'favorites': favorites}, f, ensure_ascii=False, indent=2)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "오류", f"저장 실패: {e}")

        # 3. Save든 Cancel이든 즐겨찾기 목록 다이얼로그 표시
        dialog = FavoriteDialog("Color 키워드 즐겨찾기", "./fav/edt_color_keywords.json", current_value, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted and dialog.selected_value is not None:
            self.edt_color_keywords.setText(dialog.selected_value)

    # ---------------- 설정 저장/불러오기 ----------------
    def save_config(self):
        """현재 설정 저장"""
        dialog = ConfigSaveDialog(self)
        if dialog.exec() != QtWidgets.QDialog.Accepted:
            return

        config_name = dialog.config_name

        # 설정 데이터 구성 (file_path, bookmarks 저장하지 않음)
        config = {
            # 'file_path': self.current_file_path,  # 저장 제외
            'query': self.edt_query.text(),
            'search_mode': self.cmb_mode.currentText(),
            'case_sensitive': self.chk_case.isChecked(),
            'result_search': self.edt_result_search.text(),
            'color_keywords': self.edt_color_keywords.text(),
            'recursive_search': self.chk_recursive_search.isChecked(),
            # 'bookmarks': list(self.lineView.bookmarks),  # 저장 제외
            'marked_rows': list(self.resultsModel.marked_rows),  # 마킹된 row는 저장 유지
        }

        # 파일명 생성
        config_dir = "./config"
        os.makedirs(config_dir, exist_ok=True)

        # 기존 파일 개수로 index 계산
        existing_files = [f for f in os.listdir(config_dir) if f.endswith('.json')]
        index = len(existing_files) + 1

        # 날짜_시간
        now = datetime.now()
        date_str = now.strftime("%Y%m%d_%H%M%S")

        # 파일명: index_날짜_시간_이름.json
        filename = f"{index:04d}_{date_str}_{config_name}.json"
        filepath = os.path.join(config_dir, filename)

        # 저장
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self.status.showMessage(f"설정 저장 완료: {filename}", 5000)
            QtWidgets.QMessageBox.information(self, "완료", f"설정이 저장되었습니다.\n{filename}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"설정 저장 실패: {e}")

    def load_config(self):
        """설정 불러오기"""
        config_dir = "./config"
        dialog = ConfigLoadDialog(config_dir, self)
        if dialog.exec() != QtWidgets.QDialog.Accepted or not dialog.selected_file:
            return

        filepath = dialog.selected_file

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 설정 적용
            self.edt_query.setText(config.get('query', ''))

            search_mode = config.get('search_mode', '정규식')
            index = self.cmb_mode.findText(search_mode)
            if index >= 0:
                self.cmb_mode.setCurrentIndex(index)

            self.chk_case.setChecked(config.get('case_sensitive', False))
            self.edt_result_search.setText(config.get('result_search', ''))
            self.edt_color_keywords.setText(config.get('color_keywords', ''))
            self.chk_recursive_search.setChecked(config.get('recursive_search', False))

            # 마킹된 row 복원만 적용
            marked_rows = config.get('marked_rows', [])
            self.resultsModel.marked_rows = set(marked_rows)
            if marked_rows:
                # 테이블 업데이트
                self.resultsModel.dataChanged.emit(
                    self.resultsModel.index(0, 0),
                    self.resultsModel.index(self.resultsModel.rowCount() - 1,
                                            self.resultsModel.columnCount() - 1)
                )

            self.status.showMessage(f"설정 불러오기 완료: {os.path.basename(filepath)}", 5000)
            QtWidgets.QMessageBox.information(self, "완료", "설정을 불러왔습니다.")

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"설정 불러오기 실패: {e}")

    # ---------------- 기존 기능들 ----------------
    def on_mode_changed(self, index):
        mode = self.cmb_mode.currentText()
        if mode == "일반":
            self.chk_case.setEnabled(True)
        else:
            self.chk_case.setEnabled(False)

    def on_text_changed(self):
        self.is_modified = True
        title = self.windowTitle()
        if not title.endswith('*'):
            self.setWindowTitle(title + '*')

    def load_dropped_file(self, file_path):
        if os.path.isfile(file_path):
            self.load_file(file_path)
        else:
            QtWidgets.QMessageBox.warning(self, "경고", "올바른 파일이 아닙니다.")

    def load_file(self, path):
        self.close_current_file()
        self.current_file_path = path

        self.lbl_file.setText("로딩 중: " + path)
        self.prog.setValue(0)
        self.lineView.setEnabled(False)

        self.file_thread = QtCore.QThread(self)
        self.file_loader = FileLoader(path)
        self.file_loader.moveToThread(self.file_thread)
        self.file_thread.started.connect(self.file_loader.run)
        self.file_loader.progress.connect(self.prog.setValue)
        self.file_loader.failed.connect(self.on_file_failed)
        self.file_loader.finished.connect(self.on_file_loaded)
        self.file_thread.start()

    def open_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "dumpstate 파일 선택", "", "Log/Text Files (*.txt *.log *.*)")
        if not path:
            return
        self.load_file(path)

    def save_file(self):
        if not self.current_file_path:
            QtWidgets.QMessageBox.information(self, "안내", "저장할 파일이 없습니다.")
            return

        try:
            content = self.lineView.toPlainText()
            with open(self.current_file_path, 'w', encoding=self.encoding, errors='replace') as f:
                f.write(content)

            self.is_modified = False
            title = self.windowTitle()
            if title.endswith('*'):
                self.setWindowTitle(title[:-1])

            self.status.showMessage("파일 저장 완료: " + self.current_file_path, 3000)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "저장 실패", f"파일 저장 중 오류가 발생했습니다: {str(e)}")

    def on_file_failed(self, msg: str):
        QtWidgets.QMessageBox.critical(self, "파일 열기 실패", msg)
        self.lbl_file.setText("파일 없음")
        self.prog.setValue(0)
        self.lineView.setEnabled(True)
        if self.file_thread:
            self.file_thread.quit()
            self.file_thread.wait()

    def on_file_loaded(self, content: str, encoding: str):
        if self.file_thread:
            self.file_thread.quit()
            self.file_thread.wait()

        self.content = content
        self.encoding = encoding

        self.lineView.setPlainText(content)
        self.lineView.setEnabled(True)

        self.lbl_file.setText(f"파일: {len(content)} chars, 인코딩: {encoding}, 라인: {len(content.split(chr(10)))}")
        self.status.showMessage("파일 로딩 완료", 3000)

        self.resultsModel.set_results([])
        self.current_results = []
        self.current_result_index = -1
        self.prog.setValue(0)

        self.result_search_query = ""
        self.result_search_index = -1
        self.result_search_matches = []
        self.lbl_result_search_status.setText("")

        self.is_modified = False
        self.setWindowTitle(f"Dumpstate Searcher - {os.path.basename(self.current_file_path)} - {gCurVerInfo}")

        if self.color_keywords:
            self.apply_color_highlights()

    def close_current_file(self):
        self.resultsModel.set_results([])
        self.current_results = []
        self.current_result_index = -1
        self.content = ""
        self.lineView.clear()
        self.lineView.bookmarks.clear()
        self.current_file_path = ""
        self.is_modified = False
        self.result_search_query = ""
        self.result_search_index = -1
        self.result_search_matches = []
        self.lbl_result_search_status.setText("")
        self.setWindowTitle(f"Dumpstate Searcher - {gCurVerInfo}")

    # --------- 컨텍스트(prev/next) 유틸 ---------
    def get_context_counts(self) -> Tuple[int, int]:
        def to_int(s: str) -> int:
            try:
                return max(0, int(s))
            except Exception:
                return 0
        return to_int(self.edt_prev_lines.text()), to_int(self.edt_next_lines.text())

    def apply_context_snippets_to_current_results(self):
        """현재 결과 리스트의 snippet을 prev/next 라인 포함하여 업데이트"""
        if not self.current_results:
            return
        lines = self.lineView.toPlainText().split('\n')
        total = len(lines)
        prev_n, next_n = self.get_context_counts()

        for r in self.current_results:
            start = max(0, r.line - prev_n)
            end = min(total, r.line + next_n + 1)
            r.snippet = '\n'.join(lines[start:end])

    def refresh_results_view_after_context_change(self):
        """컨텍스트 값 변경 후 테이블 뷰 갱신"""
        if self.resultsModel.rowCount() == 0:
            return
        # 1열(검색결과) 전부 갱신
        top_left = self.resultsModel.index(0, 1)
        bottom_right = self.resultsModel.index(self.resultsModel.rowCount() - 1, 1)
        self.resultsModel.dataChanged.emit(top_left, bottom_right)
        # 멀티라인 높이 반영
        self.tblResults.resizeRowsToContents()

    def on_context_lines_changed(self):
        """previous/next lines 값 변경 시 현재 결과에 즉시 반영"""
        if not self.current_results:
            return
        self.apply_context_snippets_to_current_results()
        self.refresh_results_view_after_context_change()

    def do_search(self):
        if not self.lineView.toPlainText():
            QtWidgets.QMessageBox.information(self, "안내", "먼저 dumpstate 파일을 여세요.")
            return
        query = self.edt_query.text()
        if not query.strip():
            QtWidgets.QMessageBox.information(self, "안내", "검색어를 입력하세요.")
            return

        self.stop_search()

        mode_map = {'일반': 'plain', '정규식': 'regex'}
        mode = mode_map[self.cmb_mode.currentText()]
        case = self.chk_case.isChecked() if mode == 'plain' else False

        current_content = self.lineView.toPlainText()

        self.search_thread = QtCore.QThread(self)
        self.search_worker = SearchWorker(current_content, query, mode, case)
        self.search_worker.moveToThread(self.search_thread)
        self.search_thread.started.connect(self.search_worker.run)
        self.search_worker.progress.connect(self.prog.setValue)
        self.search_worker.failed.connect(self.on_search_failed)
        self.search_worker.finished.connect(self.on_search_finished)
        self.btn_stop.setEnabled(True)
        self.btn_search.setEnabled(False)
        self.prog.setValue(0)
        self.status.showMessage("검색 중...")
        self.search_thread.start()

    def stop_search(self):
        if self.search_worker:
            self.search_worker.stop()
        if self.search_thread:
            self.search_thread.quit()
            self.search_thread.wait()
        self.btn_stop.setEnabled(False)
        self.btn_search.setEnabled(True)

    def on_search_failed(self, msg: str):
        self.stop_search()
        QtWidgets.QMessageBox.critical(self, "검색 실패", msg)
        self.status.showMessage("검색 실패: " + msg, 5000)

    def on_search_finished(self, results: List[SearchResult]):
        self.stop_search()
        self.current_results = results

        # prev/next 컨텍스트를 snippet에 반영하여 결과 세팅
        self.apply_context_snippets_to_current_results()
        self.resultsModel.set_results(results)

        self.tblResults.resizeColumnToContents(0)
        self.tblResults.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.tblResults.resizeRowsToContents()  # 멀티라인 반영

        self.result_search_query = ""
        self.result_search_index = -1
        self.result_search_matches = []
        self.lbl_result_search_status.setText("")

        if results:
            self.current_result_index = 0
            self.goto_result(results[0])
            self.status.showMessage(f"검색 완료: {len(results)}건", 8000)
        else:
            self.current_result_index = -1
            self.status.showMessage("검색 결과 없음", 5000)

    def goto_result_from_table(self, index: QModelIndex):
        r = self.resultsModel.get(index.row())
        self.current_result_index = index.row()
        self.lineView.setFocus()

        block = self.lineView.document().findBlockByNumber(r.line)
        if block.isValid():
            cursor = QtGui.QTextCursor(block)
            cursor.setPosition(block.position())
            self.lineView.setTextCursor(cursor)
            self.lineView.ensureCursorVisible()
            self.lineView.centerCursor()

        self.update_all_highlights(r)
        self.tblResults.selectRow(index.row())

    def goto_result(self, r: SearchResult):
        if not self.lineView.toPlainText():
            return

        line_number = r.line + 1
        self.lineView.gotoLine(line_number)
        self.update_all_highlights(r)

        if self.current_result_index >= 0 and self.current_result_index < self.resultsModel.rowCount():
            tidx = self.resultsModel.index(self.current_result_index, 0)
            self.tblResults.selectRow(tidx.row())
            self.tblResults.scrollTo(tidx, QtWidgets.QAbstractItemView.PositionAtCenter)

    def update_all_highlights(self, result: Optional[SearchResult] = None):
        extraSelections = []
        extraSelections.extend(self.lineView.color_highlight_selections)

        if result:
            lines = self.lineView.toPlainText().split('\n')
            if result.line < len(lines):
                line_text = lines[result.line]
                line_start_pos = sum(len(lines[i]) + 1 for i in range(result.line))

                for start, end in result.matches:
                    if start < len(line_text) and end <= len(line_text):
                        selection = QtWidgets.QTextEdit.ExtraSelection()
                        selection.format.setBackground(QtGui.QColor(102, 255, 255))

                        # 새로운 QTextCursor를 매 selection마다 생성하여 참조 공유로 인한 오동작 방지
                        cursor = QtGui.QTextCursor(self.lineView.document())
                        cursor.setPosition(line_start_pos + start)
                        cursor.setPosition(line_start_pos + end, QtGui.QTextCursor.KeepAnchor)
                        selection.cursor = cursor
                        extraSelections.append(selection)

        self.lineView.setExtraSelections(extraSelections)

    def highlight_search_results(self, result: SearchResult):
        self.update_all_highlights(result)

    def on_color_settings_clicked(self):
        keywords_text = self.edt_color_keywords.text().strip()
        if not keywords_text:
            QtWidgets.QMessageBox.information(self, "안내", "키워드를 입력하세요.")
            return

        keywords = [kw.strip() for kw in keywords_text.split('|') if kw.strip()]

        if not keywords:
            QtWidgets.QMessageBox.information(self, "안내", "유효한 키워드가 없습니다.")
            return

        self.color_keywords = []
        for i, keyword in enumerate(keywords):
            color = self.color_palette[i % len(self.color_palette)]
            self.color_keywords.append((keyword, color))

        self.apply_color_highlights()
        self.status.showMessage(f"Color 설정 적용: {len(keywords)}개 키워드", 3000)

    def on_color_clear_clicked(self):
        self.color_keywords = []
        self.edt_color_keywords.clear()
        self.lineView.color_highlight_selections = []

        if self.current_result_index >= 0 and self.current_result_index < len(self.current_results):
            result = self.current_results[self.current_result_index]
            self.update_all_highlights(result)
        else:
            self.lineView.highlightCurrentLine()

        self.status.showMessage("Color 설정 초기화", 3000)

    def apply_color_highlights(self):
        if not self.lineView.toPlainText():
            return

        color_selections = []
        if self.color_keywords:
            content = self.lineView.toPlainText()
            for keyword, color in self.color_keywords:
                try:
                    # 키워드는 정규식이 아닌 '문자 그대로' 매칭하도록 escape 처리
                    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                    for match in pattern.finditer(content):
                        selection = QtWidgets.QTextEdit.ExtraSelection()
                        selection.format.setBackground(color)

                        # 매 번 새로운 QTextCursor를 사용하여 선택 범위 지정 (버그 방지)
                        cursor = QtGui.QTextCursor(self.lineView.document())
                        cursor.setPosition(match.start())
                        cursor.setPosition(match.end(), QtGui.QTextCursor.KeepAnchor)
                        selection.cursor = cursor
                        color_selections.append(selection)
                except re.error:
                    pass

        self.lineView.color_highlight_selections = color_selections

        if self.current_result_index >= 0 and self.current_result_index < len(self.current_results):
            result = self.current_results[self.current_result_index]
            self.update_all_highlights(result)
        else:
            self.lineView.highlightCurrentLine()

    def search_in_results_next(self):
        query = self.edt_result_search.text().strip()
        if not query:
            return

        if not self.current_results:
            self.lbl_result_search_status.setText("검색 결과가 없습니다")
            return

        if query != self.result_search_query:
            self.result_search_query = query
            self.result_search_matches = []

            try:
                pattern = re.compile(query, re.IGNORECASE)

                for idx, result in enumerate(self.current_results):
                    line_str = str(result.line + 1)
                    snippet = result.snippet

                    if pattern.search(line_str) or pattern.search(snippet):
                        self.result_search_matches.append(idx)

            except re.error as e:
                self.lbl_result_search_status.setText(f"정규식 오류: {e}")
                return

            self.result_search_index = -1

        if not self.result_search_matches:
            self.lbl_result_search_status.setText("일치하는 항목 없음")
            return

        is_recursive = self.chk_recursive_search.isChecked()

        if self.result_search_index >= len(self.result_search_matches) - 1:
            if is_recursive:
                self.result_search_index = 0
            else:
                self.lbl_result_search_status.setText(
                    f"{len(self.result_search_matches)} / {len(self.result_search_matches)} (마지막)"
                )
                return
        else:
            self.result_search_index += 1

        row_index = self.result_search_matches[self.result_search_index]
        self.current_result_index = row_index
        result = self.current_results[row_index]
        self.goto_result(result)

        self.lbl_result_search_status.setText(
            f"{self.result_search_index + 1} / {len(self.result_search_matches)}"
        )

    def search_in_results_prev(self):
        query = self.edt_result_search.text().strip()
        if not query:
            return

        if not self.current_results:
            self.lbl_result_search_status.setText("검색 결과가 없습니다")
            return

        if query != self.result_search_query:
            self.result_search_query = query
            self.result_search_matches = []

            try:
                pattern = re.compile(query, re.IGNORECASE)

                for idx, result in enumerate(self.current_results):
                    line_str = str(result.line + 1)
                    snippet = result.snippet

                    if pattern.search(line_str) or pattern.search(snippet):
                        self.result_search_matches.append(idx)

            except re.error as e:
                self.lbl_result_search_status.setText(f"정규식 오류: {e}")
                return

            self.result_search_index = len(self.result_search_matches)

        if not self.result_search_matches:
            self.lbl_result_search_status.setText("일치하는 항목 없음")
            return

        is_recursive = self.chk_recursive_search.isChecked()

        if self.result_search_index <= 0:
            if is_recursive:
                self.result_search_index = len(self.result_search_matches) - 1
            else:
                self.lbl_result_search_status.setText(
                    f"1 / {len(self.result_search_matches)} (첫번째)"
                )
                return
        else:
            self.result_search_index -= 1

        row_index = self.result_search_matches[self.result_search_index]
        self.current_result_index = row_index
        result = self.current_results[row_index]
        self.goto_result(result)

        self.lbl_result_search_status.setText(
            f"{self.result_search_index + 1} / {len(self.result_search_matches)}"
        )

    def keyPressEvent(self, event):
        # F3/F4 처리 (결과 내 검색). F2/Shift+F2는 QShortcut에서 처리.
        # lineView에 focus가 있고 검색 다이얼로그가 열려있으면 lineView에서 처리
        if self.lineView.hasFocus() and self.lineView.search_dialog and self.lineView.search_dialog.isVisible():
            return

        if event.key() == Qt.Key_F3:
            self.search_in_results_prev()
            event.accept()
            return
        elif event.key() == Qt.Key_F4:
            self.search_in_results_next()
            event.accept()
            return

        super().keyPressEvent(event)

    def closeEvent(self, event):
        if self.is_modified:
            reply = QtWidgets.QMessageBox.question(
                self, '확인',
                '변경사항이 있습니다. 저장하지 않고 종료하시겠습니까?',
                QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel,
                QtWidgets.QMessageBox.Save
            )

            if reply == QtWidgets.QMessageBox.Save:
                self.save_file()
                event.accept()
            elif reply == QtWidgets.QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


# ------------------------------ 앱 실행 ------------------------------

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


def main():
    app = QtWidgets.QApplication(sys.argv)
    apply_light_theme(app)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()