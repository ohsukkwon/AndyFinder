# -*- coding: utf-8 -*-
import sys
import os
import re
import json
import subprocess
import time
from datetime import datetime
from dataclasses import dataclass
from typing import List, Tuple, Optional

import chardet
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, Signal, QObject, QModelIndex, QTimer
from PySide6.QtGui import QIcon


# ------------------------------ 버전 관리 ------------------------------
class MyVersionHistory:
    VER_INFO__ver_1_251001_0140 = "ver_1_251001_0140"
    VER_DESC__ver_1_251001_0140 = '''
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
13. tblResults LineNumber를 lineView LineNumber로 Drag&Drop하여 범위 복사 기능 추가.
14. 즐겨찾기 Category(폴더 구조) 지원: 세 가지 즐겨찾기(기본 검색어/결과내 검색/Color 키워드)에 폴더 생성/이동/선택 기능 추가.
'''
    VER_INFO__ver_1_251001_0927 = "ver_1_251001_0927"
    VER_DESC__ver_1_251001_0927 = '''
1. 즐겨찾기 Add 입력방식 개선 : 문자열이 있는 경우 값에 표시하고, 이름을 입력받도록 개선
'''
    VER_INFO__ver_1_251001_1300 = "ver_1_251001_1300"
    VER_DESC__ver_1_251001_1300 = '''
- 파일 메뉴에 "All data clear" 메뉴 추가: lineView, tblResults, lbl_status 등 로드된 파일 관련 정보를 초기화합니다.
- lineView에 포커스가 있을 때 Ctrl + Mouse Wheel로 글꼴 크기 조절 시, 라인 번호 영역(LineNumberArea)도 동일하게 폰트 크기가 연동되도록 수정:
- CodeEditor.setFont을 오버라이드하여 에디터와 라인 번호 영역의 폰트를 동기화.
- zoomIn/zoomOut에서도 LineNumberArea 폰트를 동기화하고, 너비를 재계산하도록 처리.
- wheelEvent는 lineView에 포커스가 있고 Ctrl이 눌린 경우에만 확대/축소 수행.
'''
    VER_INFO__ver_1_251001_1500 = "ver_1_251001_1500"
    VER_DESC__ver_1_251001_1500 = '''
- MainWindow에 latest_config 관련 메서드 추가: latest_config_file_path, build_latest_config, apply_latest_config, save_latest_config, load_latest_config
- 프로그램 시작 시 load_latest_config() 호출
- 종료 시 closeEvent에서 save_latest_config() 호출 (파일 저장 여부와 무관하게 종료 확정 시 항상 저장)
- 저장 항목: query, search_mode, case_sensitive, result_search, color_keywords, recursive_search, prev_lines, next_lines, lineView_font_pt, tblResults_font_pt, always_on_top
'''

    VER_INFO__ver_1_251001_1600 = "ver_1_251001_1600"
    VER_DESC__ver_1_251001_1600 = '''
- prog(QProgressBar) 우측에 dropbox(QComboBox) 추가
- dropbox에 "기본 검색어 즐겨찾기" 항목을 category 구분하여 모든 favorite 항목의 이름 표시
- dropbox의 세부 항목 이름이 전체가 보이도록 충분한 width 설정
- 이름 위에 마우스 over 시 값의 내용이 툴팁으로 표시
- dropbox에서 항목 선택 후 F5 누르면 선택된 favorite 값을 edt_query에 로딩하고 포커스 설정
'''

    VER_INFO__ver_1_251001_1700 = "ver_1_251001_1700"
    VER_DESC__ver_1_251001_1700 = '''
- 파일 로딩 시 소요 시간을 lbl_status에 "Loading duration : xx sec(s)" 형식으로 표시
- 검색 시 소요 시간을 검색 결과 옆에 "Searching duration : xx sec(s)" 형식으로 표시
'''

    VER_INFO__ver_1_251002_1426 = "ver_1_251002_1426"
    VER_DESC__ver_1_251002_1426 = '''
- 행 선택 시 가로 스크롤을 첫 번째 컬럼으로 이동
'''

    VER_INFO__ver_1_251003_1530 = "ver_1_251003_1530"
    VER_DESC__ver_1_251003_1530 = '''
- 텍스트 검색(LineViewSearchDialog) 창에서 F5로 재검색 기능 추가
'''

    VER_INFO__ver_1_251003_2000 = "ver_1_251003_2000"
    VER_DESC__ver_1_251003_2000 = '''
- 텍스트 검색(LineViewSearchDialog) 창에 전체검색 기능 추가
- 전체검색 버튼 클릭 시 TableView에 검색 결과(줄번호, 내용) 표시
- TableView row 더블클릭 시 lineView에서 해당 라인으로 이동
'''

    VER_INFO__ver_1_251004_1100 = "ver_1_251004_1100"
    VER_DESC__ver_1_251004_1100 = '''
- go to line 기능 추가
'''

    VER_INFO__ver_1_251004_1650 = "ver_1_251004_1650"
    VER_DESC__ver_1_251004_1650 = '''
- lineView 우측에 lineView_clone 추가 (QSplitter로 좌우 비율 조절 가능)
- lineView_clone은 read-only, search/selection만 가능
- focus를 가진 widget만 동작 (모든 key/mouse 이벤트)
- 파일 drop 시 lineView_clone에도 동일 내용 loading
- lineView 상단에 노란색 widget, lineView_clone 상단에 파란색 widget 표시
- lineView와 lineView_clone 초기 width 비율 95:5로 설정
- focus 상태에 따라 테두리 색상 변경 (focus: 빨간색 2px, no focus: 검은색 2px)
- lineView_clone에도 current active line에 light blue 배경 표시
'''

    def __init__(self):
        pass

    def get_version_info(self):
        return self.VER_INFO__ver_1_251004_1650, self.VER_DESC__ver_1_251004_1650


# ------------------------------ Global 변수 ------------------------------
g_my_version_info = MyVersionHistory()

gCurVerInfo, gCurVerDesc = g_my_version_info.get_version_info()

g_pgm_name = 'AndyFinder'
g_win_size_w = 1300
g_win_size_h = 800
g_font_face = 'Arial'
g_font_size = 8
g_MIN_FONT_SIZE = 1
g_MAX_FONT_SIZE = 70
g_icon_name = 'app.png'

MIN_BUF_LOAD_SIZE = 1 * 1024 * 1024

debug_measuretime_start = 0
debug_measuretime_snapshot = 0


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


# ------------------------------ 커스텀 ComboBox (F5로 즐겨찾기 로딩) ------------------------------

class FavoriteComboBox(QtWidgets.QComboBox):
    """F5로 선택된 즐겨찾기를 로딩하는 ComboBox"""

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F5:
            parent = self.parent()
            while parent:
                if isinstance(parent, QtWidgets.QMainWindow):
                    parent.load_favorite_from_combobox()
                    event.accept()
                    return
                parent = parent.parent()
        super().keyPressEvent(event)


# ------------------------------ LineView 검색 다이얼로그 (Modeless + 전체검색 기능) ------------------------------

class LineViewSearchDialog(QtWidgets.QDialog):
    """lineView 내부 검색 다이얼로그 (Modeless + 전체검색 기능)"""

    def __init__(self, editor, parent=None, viewer_name=""):  # viewer_name 파라미터 추가
        super().__init__(parent)
        # viewer_name에 따라 제목 설정
        if viewer_name == "left":
            self.setWindowTitle("Left TextViewer 텍스트 검색")
        elif viewer_name == "right":
            self.setWindowTitle("Right TextViewer 텍스트 검색")
        else:
            self.setWindowTitle("텍스트 검색")

        self.setModal(False)  # Modeless로 변경
        self.editor = editor
        self.opacity_value = 100  # 투명도 값 (0~100)
        self.setup_ui()
        self.update_opacity()  # 초기 투명도 설정

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Title bar 커스터마이징을 위한 위젯 추가
        title_widget = QtWidgets.QWidget()
        title_layout = QtWidgets.QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QtWidgets.QLabel("투명도:")

        # 투명도 조절 슬라이더 추가
        self.opacity_slider = QtWidgets.QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(50)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setFixedWidth(150)
        self.opacity_slider.setToolTip("투명도 조절 (50: 최소, 100: 불투명)")
        self.opacity_slider.valueChanged.connect(self.on_opacity_changed)

        title_layout.addWidget(title_label)
        title_layout.addWidget(self.opacity_slider)
        title_layout.addStretch()

        layout.addWidget(title_widget)

        # 검색어 입력
        form_layout = QtWidgets.QFormLayout()
        self.edt_search = QtWidgets.QLineEdit()
        self.edt_search.setPlaceholderText("정규표현식 입력/F5:새로고침...")
        form_layout.addRow("검색어(정규표현식/F5:새로고침):", self.edt_search)
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
        self.btn_prev = QtWidgets.QPushButton("Prev(F3)")
        self.btn_next = QtWidgets.QPushButton("Next(F4)")
        self.btn_search_all = QtWidgets.QPushButton("전체검색")
        self.btn_search_all.setStyleSheet("""
            QPushButton {
                background-color: blue4;
                color: #FFFFFF;
                border: 2px solid black;
                font-weight: bold;
            }
            QPushButton:hover {
                color: white;
                font-weight: bold;
                border: 2px solid white;
            }
        """)

        self.btn_close = QtWidgets.QPushButton("닫기")

        btn_layout.addWidget(self.btn_prev)
        self.btn_prev.setAutoDefault(False)
        btn_layout.addWidget(self.btn_next)
        self.btn_next.setAutoDefault(False)
        btn_layout.addWidget(self.btn_search_all)
        self.btn_search_all.setAutoDefault(False)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

        # 전체검색 결과 테이블 추가
        self.tbl_search_results = QtWidgets.QTableView()
        self.tbl_search_results.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tbl_search_results.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tbl_search_results.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tbl_search_results.verticalHeader().setVisible(False)
        self.tbl_search_results.setAlternatingRowColors(True)
        self.tbl_search_results.setWordWrap(False)
        self.tbl_search_results.setTextElideMode(Qt.ElideNone)

        # 모델 설정
        self.search_model = QtGui.QStandardItemModel()
        self.search_model.setHorizontalHeaderLabels(["LineNumber", "내용"])
        self.tbl_search_results.setModel(self.search_model)

        # 헤더 설정
        header = self.tbl_search_results.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)

        layout.addWidget(self.tbl_search_results, 1)

        # 시그널
        self.edt_search.returnPressed.connect(self.on_search_next)
        self.btn_prev.clicked.connect(self.on_search_prev)
        self.btn_next.clicked.connect(self.on_search_next)
        self.btn_search_all.clicked.connect(self.on_search_all)
        self.btn_close.clicked.connect(self.close)
        self.tbl_search_results.doubleClicked.connect(self.on_table_double_clicked)

        self.resize(800, 600)

    def on_opacity_changed(self, value):
        """슬라이더 값 변경 시 투명도 업데이트"""
        self.opacity_value = value
        self.update_opacity()

    def update_opacity(self):
        """현재 focus 상태에 따라 투명도 적용"""
        if self.isActiveWindow():
            # focus가 있을 때: 슬라이더 값 그대로 적용
            opacity = self.opacity_value / 100.0
        else:
            # focus가 없을 때: 슬라이더 값에서 30% 감소
            opacity = max(0.0, (self.opacity_value - 30) / 100.0)

        self.setWindowOpacity(opacity)

    def focusInEvent(self, event):
        """다이얼로그가 focus를 얻을 때"""
        super().focusInEvent(event)
        self.update_opacity()

    def focusOutEvent(self, event):
        """다이얼로그가 focus를 잃을 때"""
        super().focusOutEvent(event)
        self.update_opacity()

    def changeEvent(self, event):
        """창 활성화 상태 변경 감지"""
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.ActivationChange:
            self.update_opacity()

    def on_search_all(self):
        """전체검색: edt_search의 정규표현식으로 lineView 전체를 검색하여 테이블에 표시"""
        pattern = self.edt_search.text().strip()
        if not pattern:
            self.lbl_status.setText("검색어를 입력하세요")
            return

        # 모델 초기화
        self.search_model.removeRows(0, self.search_model.rowCount())

        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            self.lbl_status.setText(f"정규식 오류: {e}")
            return

        content = self.editor.toPlainText()
        lines = content.split('\n')
        match_count = 0

        for line_num, line_text in enumerate(lines, start=1):
            if regex.search(line_text):
                # 줄번호와 내용을 테이블에 추가
                line_num_item = QtGui.QStandardItem(str(line_num))
                content_item = QtGui.QStandardItem(line_text)
                self.search_model.appendRow([line_num_item, content_item])
                match_count += 1

        self.lbl_status.setText(f"전체검색 완료: {match_count}건")

        # 첫 번째 결과로 이동 (있는 경우)
        if match_count > 0:
            self.tbl_search_results.selectRow(0)

    def on_table_double_clicked(self, index):
        """테이블 더블클릭: lineView에서 해당 라인으로 이동하고 focus는 테이블 유지"""
        if not index.isValid():
            return

        # 줄번호 가져오기 (0번 컬럼)
        line_num_item = self.search_model.item(index.row(), 0)
        if not line_num_item:
            return

        try:
            line_number = int(line_num_item.text())
            # lineView에서 해당 라인으로 이동
            self.editor.gotoLine(line_number)
            # focus는 테이블로 다시 설정
            self.tbl_search_results.setFocus()
        except ValueError:
            pass

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

    # 추가: F5 키로 재검색 수행
    def on_refresh_search(self):
        """F5: 현재 검색어로 처음부터 다시 검색"""
        pattern = self.edt_search.text().strip()
        if not pattern:
            self.lbl_status.setText("검색어를 입력하세요")
            return

        # 검색 상태 초기화 후 재검색
        self.editor.internal_search_pattern = ""
        self.editor.internal_search_matches = []
        self.editor.internal_search_index = -1

        # 재검색 수행
        recursive = self.chk_recursive.isChecked()
        result = self.editor.search_next(pattern, recursive)
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
        elif event.key() == Qt.Key_F5:  # 추가: F5 키 처리
            self.on_refresh_search()
            event.accept()
            return
        elif event.key() == Qt.Key_Escape:
            self.close()
            event.accept()
            return
        super().keyPressEvent(event)


# ------------------------------ Go to Line 다이얼로그 ------------------------------

class GoToLineDialog(QtWidgets.QDialog):
    """Go to Line 다이얼로그"""

    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Go to line")
        self.setModal(True)
        self.editor = editor
        self.line_number = -1
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # 라벨과 입력창
        form_layout = QtWidgets.QFormLayout()
        self.edt_line = QtWidgets.QLineEdit()
        self.edt_line.setPlaceholderText("줄 번호 입력...")

        # 숫자만 입력 가능하도록
        int_validator = QtGui.QIntValidator(1, 999999999, self)
        self.edt_line.setValidator(int_validator)

        form_layout.addRow("Go to line:", self.edt_line)
        layout.addLayout(form_layout)

        # 버튼들
        btn_layout = QtWidgets.QHBoxLayout()
        self.btn_ok = QtWidgets.QPushButton("OK")
        self.btn_cancel = QtWidgets.QPushButton("Cancel")

        btn_layout.addStretch()
        self.btn_ok.setAutoDefault(False)
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        # 시그널
        self.btn_ok.clicked.connect(self.on_ok)
        self.btn_cancel.clicked.connect(self.reject)

        self.resize(300, 120)
        self.edt_line.setFocus()

    def keyPressEvent(self, event):
        """엔터키 처리를 위한 keyPressEvent 오버라이드"""
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.on_ok()
            event.accept()
            return
        super().keyPressEvent(event)

    def on_ok(self):
        line_text = self.edt_line.text().strip()
        if not line_text:
            QtWidgets.QMessageBox.warning(self, "경고", "줄 번호를 입력하세요.")
            return

        try:
            line_number = int(line_text)
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "경고", "올바른 숫자를 입력하세요.")
            return

        # 범위 확인
        total_lines = self.editor.document().blockCount()
        if line_number < 1 or line_number > total_lines:
            QtWidgets.QMessageBox.warning(
                self, "경고",
                f"줄 번호가 범위를 벗어났습니다.\n유효 범위: 1 ~ {total_lines}"
            )
            return

        self.line_number = line_number
        self.accept()


# ------------------------------ 즐겨찾기 추가 다이얼로그 ------------------------------

class FavoriteAddDialog(QtWidgets.QDialog):
    """즐겨찾기 추가/수정 입력 다이얼로그"""

    def __init__(self, current_value="", current_name="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("즐겨찾기 추가/수정")
        self.current_value = current_value
        self.init_name = current_name
        self.name = ""
        self.value = ""
        self.setup_ui()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # 입력 폼
        form_layout = QtWidgets.QFormLayout()

        self.edt_name = QtWidgets.QLineEdit()
        self.edt_name.setPlaceholderText("즐겨찾기 이름 입력...")
        if self.init_name:
            self.edt_name.setText(self.init_name)
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


# ------------------------------ 즐겨찾기 트리 위젯 (드래그 앤 드롭 내부 이동 전용) ------------------------------

class FavoritesTree(QtWidgets.QTreeWidget):
    internalMoveFinished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # 드래그 앤 드롭 설정
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)

    def dropEvent(self, event: QtGui.QDropEvent):
        super().dropEvent(event)
        # 내부 이동 후 알림
        self.internalMoveFinished.emit()


# ------------------------------ 즐겨찾기 다이얼로그 (폴더 구조 + Drag & Drop 이동) ------------------------------

class FavoriteDialog(QtWidgets.QDialog):
    """즐겨찾기 관리 다이얼로그 (폴더 구조 + Drag & Drop 이동 지원)"""

    ROLE_PATH = Qt.UserRole  # 내부 경로(인덱스 리스트)
    ROLE_TYPE = Qt.UserRole + 1  # 'folder' or 'item'

    def __init__(self, title, json_path, current_value="", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.json_path = json_path
        self.current_value = current_value
        self.favorites = self.load_favorites()  # list of nodes (folder/item)
        self.selected_value = None
        self.setup_ui()

    # ---------- 데이터 로드/저장 ----------
    def load_favorites(self):
        """폴더 구조의 즐겨찾기 로드 (구버전 평면 포맷 자동 변환)"""
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    favs = data.get('favorites', [])
                    # 구버전(평면 리스트) -> item 노드로 변환
                    needs_migrate = False
                    for e in favs:
                        if not isinstance(e, dict) or 'type' not in e:
                            needs_migrate = True
                            break
                    if needs_migrate:
                        migrated = []
                        for e in favs:
                            if isinstance(e, dict) and 'name' in e and 'value' in e:
                                migrated.append({'type': 'item', 'name': e['name'], 'value': e.get('value', '')})
                        return migrated
                    # 이미 폴더 구조
                    return favs
            except Exception as e:
                print(f"즐겨찾기 로드 실패: {e}")
                return []
        return []

    def save_favorites(self):
        """즐겨찾기 저장 (폴더 구조)"""
        try:
            os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump({'favorites': self.favorites}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"저장 실패: {e}")

    # ---------- UI ----------
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        info_label = QtWidgets.QLabel("폴더/아이템을 더블클릭하거나, 버튼 또는 드래그앤드롭으로 관리할 수 있습니다."
                                      "\n"
                                      "- 아이템을 폴더로 드래그하여 이동, 루트(바깥)로 드래그하여 루트로 이동할 수 있습니다.")
        layout.addWidget(info_label)

        # 트리
        self.tree = FavoritesTree()
        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["이름", "값"])
        self.tree.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        # 드래그 내부 이동 완료 후 데이터/파일 저장 및 트리 갱신
        self.tree.internalMoveFinished.connect(self.on_tree_internal_move)
        layout.addWidget(self.tree, 1)

        # 버튼들
        btn_layout = QtWidgets.QHBoxLayout()

        self.btn_add_folder = QtWidgets.QPushButton("폴더 추가")
        self.btn_add_item = QtWidgets.QPushButton("즐겨찾기 추가")
        self.btn_edit = QtWidgets.QPushButton("수정")
        self.btn_delete = QtWidgets.QPushButton("삭제")
        self.btn_select = QtWidgets.QPushButton("선택")
        self.btn_close = QtWidgets.QPushButton("닫기")

        btn_layout.addWidget(self.btn_add_folder)
        btn_layout.addWidget(self.btn_add_item)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_select)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_close)
        layout.addLayout(btn_layout)

        self.btn_add_folder.clicked.connect(self.add_folder)
        self.btn_add_item.clicked.connect(self.add_favorite)
        self.btn_edit.clicked.connect(self.edit_node)
        self.btn_delete.clicked.connect(self.delete_node)
        self.btn_select.clicked.connect(self.select_favorite)
        self.btn_close.clicked.connect(self.reject)

        self.resize(700, 500)
        self.refresh_tree(expand_all=True)

    # ---------- 트리 헬퍼 ----------
    def refresh_tree(self, expand_all=False):
        self.tree.clear()
        self._build_tree_items(self.tree.invisibleRootItem(), self.favorites, [])

        if expand_all:
            self.tree.expandAll()
        else:
            self.tree.expandToDepth(1)

    def _set_item_flags(self, qitem: QtWidgets.QTreeWidgetItem, node_type: str):
        flags = qitem.flags()
        # 공통
        flags |= Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled
        # 폴더만 드롭 허용
        if node_type == 'folder':
            flags |= Qt.ItemIsDropEnabled
        else:
            flags &= ~Qt.ItemIsDropEnabled
        qitem.setFlags(flags)

    def _build_tree_items(self, parent_qitem: QtWidgets.QTreeWidgetItem, nodes: List[dict], path_prefix: List[int]):
        style = self.style()
        folder_icon = style.standardIcon(QtWidgets.QStyle.SP_DirIcon)
        item_icon = style.standardIcon(QtWidgets.QStyle.SP_FileIcon)

        for i, node in enumerate(nodes):
            path = path_prefix + [i]
            if node.get('type') == 'folder':
                qitem = QtWidgets.QTreeWidgetItem([node.get('name', ''), ''])
                qitem.setIcon(0, folder_icon)
                qitem.setData(0, self.ROLE_PATH, path)
                qitem.setData(0, self.ROLE_TYPE, 'folder')
                self._set_item_flags(qitem, 'folder')
                parent_qitem.addChild(qitem)
                children = node.get('children', [])
                self._build_tree_items(qitem, children, path)
            else:  # item
                value = node.get('value', '')
                qitem = QtWidgets.QTreeWidgetItem([node.get('name', ''), value])
                qitem.setIcon(0, item_icon)
                qitem.setData(0, self.ROLE_PATH, path)
                qitem.setData(0, self.ROLE_TYPE, 'item')
                self._set_item_flags(qitem, 'item')
                # 마우스 오버 시 값 전체를 툴팁으로 표시
                qitem.setToolTip(0, value)
                qitem.setToolTip(1, value)
                parent_qitem.addChild(qitem)

    def _get_node_by_path(self, path: List[int]) -> Optional[dict]:
        if not path:
            return None
        node = None
        try:
            node = self.favorites[path[0]]
            for idx in path[1:]:
                node = node['children'][idx]
            return node
        except Exception:
            return None

    def _get_parent_list_and_index(self, path: List[int]):
        """해당 path의 부모 리스트와 index 반환"""
        if not path:
            return None, -1
        if len(path) == 1:
            return self.favorites, path[0]
        parent = self.favorites[path[0]]
        for idx in path[1:-1]:
            parent = parent['children'][idx]
        return parent.get('children', []), path[-1]

    def _get_target_children_list_for_add(self, sel_item: Optional[QtWidgets.QTreeWidgetItem]):
        """선택된 아이템 기준으로 추가될 대상 children 리스트 반환 (folder면 그 안, item이면 parent, 선택없으면 root)"""
        if not sel_item:
            return self.favorites
        path = sel_item.data(0, self.ROLE_PATH)
        node = self._get_node_by_path(path)
        if not node:
            return self.favorites
        if node.get('type') == 'folder':
            node.setdefault('children', [])
            return node['children']
        # item이면 부모 children
        parent_list, _ = self._get_parent_list_and_index(path)
        return parent_list if parent_list is not None else self.favorites

    def _rebuild_from_tree(self) -> List[dict]:
        """현재 트리 구조로 favorites 리스트를 재구성"""

        def build_from_item(item: QtWidgets.QTreeWidgetItem) -> dict:
            node_type = item.data(0, self.ROLE_TYPE)
            name = item.text(0)
            if node_type == 'folder':
                children = [build_from_item(item.child(i)) for i in range(item.childCount())]
                return {'type': 'folder', 'name': name, 'children': children}
            else:
                value = item.text(1)
                return {'type': 'item', 'name': name, 'value': value}

        root = self.tree.invisibleRootItem()
        rebuilt: List[dict] = []
        for i in range(root.childCount()):
            rebuilt.append(build_from_item(root.child(i)))
        return rebuilt

    # ---------- 드래그 앤 드롭 콜백 ----------
    def on_tree_internal_move(self):
        """트리 내부 이동(drop) 후 favorites를 재구성/저장하고 트리 갱신"""
        try:
            self.favorites = self._rebuild_from_tree()
            self.save_favorites()
            # 경로(path) 정보를 다시 정합하게 하기 위해 트리 재구성
            self.refresh_tree(expand_all=True)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"드래그 이동 처리 실패: {e}")

    # ---------- 액션 ----------
    def add_folder(self):
        sel_item = self.tree.currentItem()
        target_list = self._get_target_children_list_for_add(sel_item)

        name, ok = QtWidgets.QInputDialog.getText(self, "폴더 추가", "폴더 이름:")
        if not ok:
            return
        name = name.strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "경고", "폴더 이름을 입력하세요.")
            return

        target_list.append({'type': 'folder', 'name': name, 'children': []})
        self.save_favorites()
        self.refresh_tree(expand_all=True)

    def add_favorite(self):
        sel_item = self.tree.currentItem()
        target_list = self._get_target_children_list_for_add(sel_item)

        dlg = FavoriteAddDialog(current_value=self.current_value, parent=self)
        if dlg.exec() != QtWidgets.QDialog.Accepted:
            return

        target_list.append({'type': 'item', 'name': dlg.name, 'value': dlg.value})
        self.save_favorites()
        self.refresh_tree(expand_all=True)

    def edit_node(self):
        sel_item = self.tree.currentItem()
        if not sel_item:
            QtWidgets.QMessageBox.warning(self, "경고", "수정할 항목을 선택하세요.")
            return

        path = sel_item.data(0, self.ROLE_PATH)
        node = self._get_node_by_path(path)
        if not node:
            return

        if node.get('type') == 'folder':
            new_name, ok = QtWidgets.QInputDialog.getText(self, "폴더 이름 수정", "이름:", text=node.get('name', ''))
            if not ok:
                return
            new_name = new_name.strip()
            if not new_name:
                QtWidgets.QMessageBox.warning(self, "경고", "이름을 입력하세요.")
                return
            node['name'] = new_name
        else:
            dlg = FavoriteAddDialog(current_value=node.get('value', ''), current_name=node.get('name', ''), parent=self)
            if dlg.exec() != QtWidgets.QDialog.Accepted:
                return
            node['name'] = dlg.name
            node['value'] = dlg.value

        self.save_favorites()
        self.refresh_tree(expand_all=True)

    def delete_node(self):
        sel_item = self.tree.currentItem()
        if not sel_item:
            QtWidgets.QMessageBox.warning(self, "경고", "삭제할 항목을 선택하세요.")
            return

        path = sel_item.data(0, self.ROLE_PATH)
        node = self._get_node_by_path(path)
        if not node:
            return

        if node.get('type') == 'folder':
            reply = QtWidgets.QMessageBox.question(
                self, "확인", f"폴더 '{node.get('name', '')}' 및 하위 모든 항목을 삭제하시겠습니까?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
        else:
            reply = QtWidgets.QMessageBox.question(
                self, "확인", f"'{node.get('name', '')}' 항목을 삭제하시겠습니까?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )

        if reply != QtWidgets.QMessageBox.Yes:
            return

        parent_list, idx = self._get_parent_list_and_index(path)
        if parent_list is None or idx < 0 or idx >= len(parent_list):
            return

        del parent_list[idx]
        self.save_favorites()
        self.refresh_tree(expand_all=True)

    def select_favorite(self):
        sel_item = self.tree.currentItem()
        if not sel_item:
            QtWidgets.QMessageBox.warning(self, "경고", "선택할 항목을 선택하세요.")
            return

        path = sel_item.data(0, self.ROLE_PATH)
        node = self._get_node_by_path(path)
        if not node:
            return

        if node.get('type') != 'item':
            QtWidgets.QMessageBox.information(self, "안내", "폴더는 선택할 수 없습니다. 아이템을 선택하세요.")
            return

        self.selected_value = node.get('value', '')
        self.accept()

    def on_item_double_clicked(self, item, column):
        """폴더는 펼침/접기, 아이템은 선택"""
        path = item.data(0, self.ROLE_PATH)
        node = self._get_node_by_path(path)
        if not node:
            return
        if node.get('type') == 'folder':
            self.tree.setItemExpanded(item, not self.tree.isItemExpanded(item))
        else:
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
        self.edt_name.setPlaceholderText("예: (dumpstate)구조")
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
        self.btn_load.setAutoDefault(False)
        btn_layout.addWidget(self.btn_delete)
        self.btn_delete.setAutoDefault(False)
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
                        # MainWindow의 복사 메서드 호출
                        main_window = self.codeEditor.window()
                        if hasattr(main_window, 'copy_lines_between'):
                            main_window.copy_lines_between(source_line_number, target_line_number)
                        event.acceptProposedAction()
                    else:
                        event.ignore()
                except ValueError:
                    event.ignore()
            else:
                event.ignore()
        else:
            event.ignore()


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
        self.cursorPositionChanged.connect(self.highlightCurrentLine)
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


# ------------------------------ 파일 로더(백그라운드) ------------------------------

class FileLoader(QObject):
    progress = Signal(int)
    finished = Signal(str, str, float)  # content, encoding, duration
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
        start_time = time.time()
        try:
            size = os.path.getsize(self.path)
            sample_size = min(MIN_BUF_LOAD_SIZE, size)
            with open(self.path, 'rb') as f:
                sample = f.read(sample_size)
            encoding = self.detect_encoding(sample)
            self.progress.emit(10)

            with open(self.path, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()

            self.progress.emit(100)
            duration = time.time() - start_time
            self.finished.emit(content, encoding, duration)
        except Exception as e:
            self.failed.emit(str(e))


# ------------------------------ 검색기(백그라운드) ------------------------------

class SearchWorker(QObject):
    progress = Signal(int)
    finished = Signal(list, float)  # results, duration
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
        start_time = time.time()
        try:
            matcher = self.build_matcher()
            if not matcher:
                duration = time.time() - start_time
                self.finished.emit([], duration)
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
            duration = time.time() - start_time
            self.finished.emit(results, duration)
        except Exception as e:
            self.failed.emit(str(e))


class ResultSearchLineEdit(LongClickLineEdit):
    """F3/F4로 결과 내 검색을 수행하는 LineEdit"""

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F3:
            parent = self.window()
            if isinstance(parent, QtWidgets.QMainWindow):
                parent.search_in_results_prev()
                event.accept()
                return
        elif event.key() == Qt.Key_F4:
            parent = self.window()
            if isinstance(parent, QtWidgets.QMainWindow):
                parent.search_in_results_next()
                event.accept()
                return
        super().keyPressEvent(event)


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
            # viewer_name 결정: MainWindow에서 lineView인지 lineView_clone인지 확인
            viewer_name = ""
            main_window = self.window()
            if hasattr(main_window, 'lineView') and hasattr(main_window, 'lineView_clone'):
                if self is main_window.lineView:
                    viewer_name = "left"
                elif self is main_window.lineView_clone:
                    viewer_name = "right"

            self.search_dialog = LineViewSearchDialog(self, self.window(), viewer_name)

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
            if start >= cursor_pos:
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

        # 현재 위치 이전의 매칭 찾기
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
        # Ctrl+G: Go to Line (focus가 있을 때만)
        if self.hasFocus() and event.key() == Qt.Key_G and event.modifiers() == Qt.ControlModifier:
            self.show_goto_line_dialog()
            event.accept()
            return

        # Ctrl+1/2/3: 선택 텍스트를 지정 입력란에 추가 (focus가 있을 때만)
        if self.hasFocus() and event.modifiers() == Qt.ControlModifier and event.key() in (Qt.Key_1, Qt.Key_2, Qt.Key_3):
            cursor = self.textCursor()
            if cursor.hasSelection():
                selected_text = cursor.selectedText().replace('\u2029', '\n')
                mw = self.window()
                if hasattr(mw, 'append_text_to_lineedit'):
                    if event.key() == Qt.Key_1 and hasattr(mw, 'edt_query'):
                        mw.append_text_to_lineedit(mw.edt_query, selected_text)
                        mw.edt_query.setFocus()
                        event.accept()
                        return
                    elif event.key() == Qt.Key_2 and hasattr(mw, 'edt_result_search'):
                        mw.append_text_to_lineedit(mw.edt_result_search, selected_text)
                        mw.edt_result_search.setFocus()
                        event.accept()
                        return
                    elif event.key() == Qt.Key_3 and hasattr(mw, 'edt_color_keywords'):
                        mw.append_text_to_lineedit(mw.edt_color_keywords, selected_text)
                        mw.edt_color_keywords.setFocus()
                        event.accept()
                        return

        # Ctrl+F: 검색 다이얼로그 표시 (focus가 있을 때만)
        if self.hasFocus() and event.key() == Qt.Key_F and event.modifiers() == Qt.ControlModifier:
            self.show_search_dialog()
            event.accept()
            return

        # F3/F4: 검색 다이얼로그가 열려있고 focus가 있을 때만
        if self.hasFocus() and self.search_dialog and self.search_dialog.isVisible():
            if event.key() == Qt.Key_F3:
                recursive = self.search_dialog.chk_recursive.isChecked()
                pattern = self.search_dialog.edt_search.text()
                result = self.search_prev(pattern, recursive)
                if self.search_dialog:
                    self.search_dialog.update_status(result)
                event.accept()
                return
            elif event.key() == Qt.Key_F4:
                recursive = self.search_dialog.chk_recursive.isChecked()
                pattern = self.search_dialog.edt_search.text()
                result = self.search_next(pattern, recursive)
                if self.search_dialog:
                    self.search_dialog.update_status(result)
                event.accept()
                return

        super().keyPressEvent(event)

    def show_goto_line_dialog(self):
        """Go to Line 다이얼로그 표시"""
        dialog = GoToLineDialog(self, self.window())
        if dialog.exec() == QtWidgets.QDialog.Accepted and dialog.line_number > 0:
            self.gotoLine(dialog.line_number)


# ------------------------------ Drag 지원 TableView ------------------------------

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
            index = self.indexAt(event.pos())
            if index.isValid():
                main_window = self.window()
                if hasattr(main_window, 'toggle_result_mark'):
                    main_window.toggle_result_mark(index.row())
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        # Shift + Right Click 으로 범위 선택 지원
        if event.button() == Qt.RightButton and (event.modifiers() & Qt.ShiftModifier):
            idx = self.indexAt(event.pos())
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

    # ---- Ctrl+C 복사, Ctrl+A 전체 선택 (focus가 있을 때만) ----
    def keyPressEvent(self, event: QtGui.QKeyEvent):
        # tblResults에 focus가 있을 때 F2/Shift+F2로 마킹된 row 이동
        if self.hasFocus() and event.key() == Qt.Key_F2:
            if event.modifiers() == Qt.ShiftModifier:
                parent = self.window()
                if hasattr(parent, 'goto_prev_marked_result_from_table'):
                    parent.goto_prev_marked_result_from_table()
            else:
                parent = self.window()
                if hasattr(parent, 'goto_next_marked_result_from_table'):
                    parent.goto_next_marked_result_from_table()
            event.accept()
            return

        # F3/F4 처리 추가 (focus가 있을 때만)
        if self.hasFocus():
            if event.key() == Qt.Key_F3:
                parent = self.window()
                if hasattr(parent, 'search_in_results_prev'):
                    parent.search_in_results_prev()
                event.accept()
                return
            elif event.key() == Qt.Key_F4:
                parent = self.window()
                if hasattr(parent, 'search_in_results_next'):
                    parent.search_in_results_next()
                event.accept()
                return

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


# ------------------------------ NoWrapDelegate (tblResults 1열 전용) ------------------------------

class NoWrapDelegate(QtWidgets.QStyledItemDelegate):
    """
    - 줄바꿈 문자가 없는 텍스트: 반드시 한 줄로 표시되도록 sizeHint를 1줄 높이로 계산
    - 줄바꿈 문자가 있는 텍스트: 각 줄을 그대로 표시하되, 최대 폭/줄 수에 맞게 크기 계산
    - 너비는 텍스트의 실제 픽셀 폭을 기준으로 계산하여, 헤더가 ResizeToContents일 때
      열 너비가 컨텐츠 폭만큼 넓어지고, 가로 스크롤로 전체를 확인할 수 있음
    """

    def sizeHint(self, option, index):
        value = index.data(Qt.DisplayRole)
        if not isinstance(value, str):
            return super().sizeHint(option, index)

        fm = option.fontMetrics
        padding_w = 12
        padding_h = 8

        lines = value.split('\n')
        if len(lines) == 1:
            width = fm.horizontalAdvance(lines[0]) + padding_w
            height = fm.height() + padding_h
        else:
            width = max(fm.horizontalAdvance(line) for line in lines) + padding_w
            # 줄간격(lineSpacing)을 사용하면 자간이 포함된 높이를 얻을 수 있음
            height = fm.lineSpacing() * len(lines) + padding_h

        return QtCore.QSize(width, height)


# ------------------------------ Results Model (마킹 기능 추가) ------------------------------

class ResultsModel(QtCore.QAbstractTableModel):
    HEADERS = ["LineNumber", "검색결과"]

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
    def resource_path(self, relpath):
        try:
            abspath = sys._MEIPASS
        except Exception:
            abspath = os.path.abspath(".")
        return os.path.join(abspath, relpath)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{g_pgm_name} - {gCurVerInfo}")
        self.resize(g_win_size_w, g_win_size_h)

        icon_path = self.resource_path(g_icon_name)
        if os.path.isfile(icon_path):
            self.setWindowIcon(QIcon(icon_path))

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

        # F11 전체화면 토글용 상태 저장
        self._previous_window_state = Qt.WindowNoState
        self._previous_geometry = None

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

        self._create_menus()
        self._build_ui()

        # 시작 시 최신 설정 로드
        try:
            self.load_latest_config()
        except Exception:
            pass

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

        # All data clear 추가
        all_clear_action = QtGui.QAction('All data clear', self)
        all_clear_action.setStatusTip('로드된 파일 및 관련 표시들을 초기화합니다')
        all_clear_action.triggered.connect(self.all_data_clear)
        file_menu.addAction(all_clear_action)

        file_menu.addSeparator()

        exit_action = QtGui.QAction('종료(&X)', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 보기 메뉴
        view_menu = menubar.addMenu('보기(&V)')

        self.always_on_top_action = QtGui.QAction('항상위(&A)', self)
        self.always_on_top_action.setCheckable(True)
        self.always_on_top_action.toggled.connect(self.toggle_always_on_top)
        view_menu.addAction(self.always_on_top_action)

        # Tools 메뉴
        tools_menu = menubar.addMenu('Tools(&T)')

        open_folder_action = QtGui.QAction('Loaded 파일위치 열기(&O)', self)
        open_folder_action.triggered.connect(self.open_loaded_file_folder)
        tools_menu.addAction(open_folder_action)

        # 도움말 메뉴
        help_menu = menubar.addMenu('도움말(&H)')

        about_action = QtGui.QAction('정보(&A)', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def toggle_always_on_top(self, checked: bool):
        self.setWindowFlag(Qt.WindowStaysOnTopHint, checked)
        self.show()

    def open_loaded_file_folder(self):
        """로드된 파일이 존재하는 폴더를 탐색기로 열기"""
        if not self.current_file_path:
            QtWidgets.QMessageBox.information(self, "안내", "로드된 파일이 없습니다.")
            return

        if not os.path.exists(self.current_file_path):
            QtWidgets.QMessageBox.warning(self, "경고", "파일이 존재하지 않습니다.")
            return

        folder_path = os.path.dirname(os.path.abspath(self.current_file_path))

        try:
            if sys.platform == 'win32':
                os.startfile(folder_path)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', folder_path])
            else:  # linux
                subprocess.Popen(['xdg-open', folder_path])
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"폴더 열기 실패: {e}")

    def show_about(self):
        QtWidgets.QMessageBox.about(
            self,
            "♣ Andy Finder Program ♣",
            f"Andy Finder : {gCurVerInfo}\n\n"
            "(dumpstate) This tool can find and analyse a (dumpstate)file."
        )

    def highlight_current_line(self):
        extra_selections = []

        if not self.lineView.isReadOnly():
            selection = QtWidgets.QTextEdit.ExtraSelection()

            # 노란색 배경
            line_color = QtGui.QColor(QtCore.Qt.yellow).lighter(160)

            selection.format.setBackground(line_color)
            selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            selection.cursor = self.lineView.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        self.lineView.setExtraSelections(extra_selections)

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

        self.btn_open = QtWidgets.QPushButton("Open file...")

        self.btn_open.setFixedWidth(120)
        self.btn_open.setStyleSheet("""
            QPushButton {
                background-color: #82CAFF;
                color: black;
                border: 1px solid black;
                font-weight: bold;
            }
            QPushButton:hover {
                color: red;
                font-weight: bold;
                border: 2px solid red;
            }
        """)

        self.lbl_file = QtWidgets.QLabel("No file loaded yet!")
        self.lbl_file.setMinimumWidth(300)
        self.lbl_file.setTextInteractionFlags(Qt.TextSelectableByMouse)

        first_layout.addWidget(self.btn_open)
        first_layout.addWidget(self.lbl_file, 1)

        # 두 번째 줄
        second_row = QtWidgets.QWidget()
        second_layout = QtWidgets.QHBoxLayout(second_row)
        second_layout.setContentsMargins(0, 0, 0, 0)
        second_layout.setSpacing(8)

        self.lbl_query_title = QtWidgets.QLabel("기본 검색어 :")

        # 즐겨찾기 버튼(노란색) - edt_query 왼쪽
        self.btn_query_fav = QtWidgets.QPushButton("★")
        self.btn_query_fav.setToolTip("기본 검색어 즐겨찾기")
        self.btn_query_fav.setFixedSize(26, 26)
        self.btn_query_fav.setContentsMargins(0, 0, 0, 0)
        self.btn_query_fav.setStyleSheet("""
            QPushButton {
                background-color: Black;
                color: yellow;
                border: 2px solid Black;
                border-radius: 4px;
                font-weight: bold;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                background-color: yellow;
                border: 2px solid blue;
                color: blue;
            }
        """)
        self.btn_query_fav.clicked.connect(self.show_query_favorites)

        self.edt_query = QueryLineEdit()
        self.edt_query.setPlaceholderText("검색어를 입력하세요 (F5:검색)")
        self.edt_query.returnPressed.connect(self.do_search)
        self.edt_query.setStyleSheet("QLineEdit { background-color : lightyellow; }")

        second_layout.addWidget(self.lbl_query_title)
        second_layout.addWidget(self.btn_query_fav)
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
                selection-color: red;
            }
        """)

        self.chk_case = QtWidgets.QCheckBox("대소문자")

        self.btn_search = QtWidgets.QPushButton("Search")
        self.btn_search.setFixedWidth(120)
        self.btn_search.setStyleSheet("""
            QPushButton {
                background-color: #10069f;
                color: #FFFFFF;
                border: 2px solid black;
                font-weight: bold;
                margin-right: 20px;
            }
            QPushButton:hover {
                color: yellow;
                font-weight: bold;
                border: 2px solid yellow;
            }
        """)

        int_validator = QtGui.QIntValidator(0, 999999, self)

        lbl_prev = QtWidgets.QLabel("previous lines:")
        self.edt_prev_lines = QueryLineEdit()
        self.edt_prev_lines.setValidator(int_validator)
        self.edt_prev_lines.setText("0")
        self.edt_prev_lines.setPlaceholderText("previous lines")
        self.edt_prev_lines.setFixedWidth(35)
        self.edt_prev_lines.setToolTip("매칭 라인 이전에 포함할 줄 수 (기본 0)")
        self.edt_prev_lines.editingFinished.connect(self.on_context_lines_changed)

        lbl_next = QtWidgets.QLabel("next lines:")
        self.edt_next_lines = QueryLineEdit()
        self.edt_next_lines.setValidator(int_validator)
        self.edt_next_lines.setText("0")
        self.edt_next_lines.setPlaceholderText("next lines")
        self.edt_next_lines.setFixedWidth(35)
        self.edt_next_lines.setToolTip("매칭 라인 이후에 포함할 줄 수 (기본 0)")
        self.edt_next_lines.editingFinished.connect(self.on_context_lines_changed)

        self.btn_stop = QtWidgets.QPushButton("중지")
        self.btn_stop.setEnabled(False)
        self.prog = QtWidgets.QProgressBar()
        self.prog.setFixedWidth(150)
        self.prog.setRange(0, 100)
        self.prog.setValue(0)

        # 즐겨찾기 드롭박스
        self.cmb_favorites = FavoriteComboBox()
        self.cmb_favorites.setMinimumWidth(800)
        self.cmb_favorites.setToolTip("기본 검색어 즐겨찾기 항목 선택 (F5:로딩)")
        self.cmb_favorites.currentIndexChanged.connect(self.on_favorite_combobox_changed)
        self.cmb_favorites.setStyleSheet("""
            QComboBox {
                background-color: white;
                border: 1px solid black;
                padding: 4px;
                border-radius: 2px;
            }
            QComboBox:hover {
                border: 1px solid #0078D7;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                selection-color: red;
            }   
        """)

        third_layout.addWidget(QtWidgets.QLabel("검색모드:"))
        third_layout.addWidget(self.cmb_mode)
        third_layout.addWidget(self.chk_case)
        third_layout.addWidget(self.btn_search)
        third_layout.addWidget(lbl_prev)
        third_layout.addWidget(self.edt_prev_lines)
        third_layout.addWidget(lbl_next)
        third_layout.addWidget(self.edt_next_lines)
        third_layout.addWidget(self.btn_stop)
        third_layout.addWidget(self.prog)
        third_layout.addWidget(self.cmb_favorites)
        third_layout.addStretch()

        # 네 번째 줄
        fourth_row = QtWidgets.QWidget()
        fourth_layout = QtWidgets.QHBoxLayout(fourth_row)
        fourth_layout.setContentsMargins(0, 0, 0, 0)
        fourth_layout.setSpacing(8)

        fourth_layout.addWidget(QtWidgets.QLabel("검색결과에서 검색(정규표현식):"))

        # 즐겨찾기 버튼(노란색) - edt_result_search 왼쪽
        self.btn_result_search_fav = QtWidgets.QPushButton("★")
        self.btn_result_search_fav.setToolTip("검색결과에서 검색 즐겨찾기")
        self.btn_result_search_fav.setFixedSize(26, 26)
        self.btn_result_search_fav.setContentsMargins(0, 0, 0, 0)
        self.btn_result_search_fav.setStyleSheet("""
            QPushButton {
                background-color: #66FF00;
                color: black;
                border: 2px solid #0000FF;
                border-radius: 4px;
                font-weight: bold;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                background-color: yellow;
                border: 2px solid blue;
                color: blue;
            }
        """)
        self.btn_result_search_fav.clicked.connect(self.show_result_search_favorites)

        self.edt_result_search = ResultSearchLineEdit()
        self.edt_result_search.setPlaceholderText("검색 결과 내에서 검색...")
        self.edt_result_search.returnPressed.connect(self.search_in_results_next)
        self.edt_result_search.setStyleSheet("QLineEdit { background-color: #F0FFFF; }")

        self.btn_result_search_prev = QtWidgets.QPushButton("이전(F3)")
        self.btn_result_search_prev.setFixedWidth(80)
        self.btn_result_search_next = QtWidgets.QPushButton("다음(F4)")
        self.btn_result_search_next.setFixedWidth(80)
        self.lbl_result_search_status = QtWidgets.QLabel("")

        self.chk_recursive_search = QtWidgets.QCheckBox("되돌이 검색")
        self.chk_recursive_search.setChecked(False)

        fourth_layout.addWidget(self.btn_result_search_fav)
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

        # 즐겨찾기 버튼(노란색) - edt_color_keywords 왼쪽
        self.btn_color_keywords_fav = QtWidgets.QPushButton("★")
        self.btn_color_keywords_fav.setToolTip("Highlight Color 즐겨찾기")
        self.btn_color_keywords_fav.setFixedSize(26, 26)
        self.btn_color_keywords_fav.setContentsMargins(0, 0, 0, 0)
        self.btn_color_keywords_fav.setStyleSheet("""
            QPushButton {
                background-color: #DBF9DB;
                color: black;
                border: 2px solid #0000FF;
                border-radius: 4px;
                font-weight: bold;
                padding: 0px;
                margin: 0px;
            }
            QPushButton:hover {
                background-color: yellow;
                border: 2px solid blue;
                color: blue;
            }
        """)
        self.btn_color_keywords_fav.clicked.connect(self.show_color_keywords_favorites)

        self.edt_color_keywords = ColorKeywordsLineEdit()
        self.edt_color_keywords.setPlaceholderText("예: activity|window|package (F5:Color 설정)")
        self.edt_color_keywords.setStyleSheet("QLineEdit { background-color: #C9DFEC; }")

        self.btn_apply_colors = QtWidgets.QPushButton("설정")
        self.btn_apply_colors.clicked.connect(self.on_color_settings_clicked)

        self.btn_clear_colors = QtWidgets.QPushButton("Clear")
        self.btn_clear_colors.clicked.connect(self.on_color_clear_clicked)

        fifth_layout.addWidget(self.btn_color_keywords_fav)
        fifth_layout.addWidget(self.edt_color_keywords, 1)
        fifth_layout.addWidget(self.btn_apply_colors)
        fifth_layout.addWidget(self.btn_clear_colors)
        fifth_layout.addStretch()

        top_layout.addWidget(first_row)
        top_layout.addWidget(second_row)
        top_layout.addWidget(third_row)
        top_layout.addWidget(fourth_row)
        top_layout.addWidget(fifth_row)

        # 중앙: 세로 splitter
        splitter_vertical = QtWidgets.QSplitter()
        splitter_vertical.setOrientation(Qt.Vertical)
        splitter_vertical.setStyleSheet("""
            QSplitter::handle {
                background-color: #16F529;
                height: 2px;
                margin: 0px;
            }
            QSplitter::handle:vertical {
                height: 2px;
            }
            QSplitter::handle:vertical:hover {
                background-color: blue;
            }
        """)

        # ========== 요청사항 1, 2: lineView와 lineView_clone 컨테이너 구성 ==========
        # lineView와 lineView_clone을 가로 splitter로 배치
        splitter_horizontal = QtWidgets.QSplitter()
        splitter_horizontal.setOrientation(Qt.Horizontal)
        splitter_horizontal.setStyleSheet("""
            QSplitter::handle {
                background-color: #16F529;
                width: 2px;
                margin: 0px;
            }
            QSplitter::handle:horizontal {
                width: 3px;
            }
            QSplitter::handle:horizontal:hover {
                background-color: blue;
            }
        """)

        # lineView (왼쪽) - 컨테이너 위젯 생성
        lineView_container = QtWidgets.QWidget()
        lineView_layout = QtWidgets.QVBoxLayout(lineView_container)
        lineView_layout.setContentsMargins(0, 0, 0, 0)
        lineView_layout.setSpacing(0)

        # 요청사항 1: 노란색 위젯 (lineView 상단)
        lineView_indicator = QtWidgets.QWidget()
        lineView_indicator.setFixedHeight(1)
        lineView_indicator.setStyleSheet("background-color: yellow;")
        lineView_layout.addWidget(lineView_indicator)

        # lineView
        self.lineView = DragDropCodeEditor()
        self.lineView.setFont(QtGui.QFont(g_font_face, g_font_size))
        self.lineView.textChanged.connect(self.on_text_changed)
        self.lineView.fileDropped.connect(self.load_dropped_file)
        self.lineView.cursorPositionChanged.connect(self.highlight_current_line)

        lineView_layout.addWidget(self.lineView)

        # lineView_clone (오른쪽) - 컨테이너 위젯 생성
        lineView_clone_container = QtWidgets.QWidget()
        lineView_clone_layout = QtWidgets.QVBoxLayout(lineView_clone_container)
        lineView_clone_layout.setContentsMargins(0, 0, 0, 0)
        lineView_clone_layout.setSpacing(0)

        # 요청사항 1: 파란색 위젯 (lineView_clone 상단)
        lineView_clone_indicator = QtWidgets.QWidget()
        lineView_clone_indicator.setFixedHeight(1)
        lineView_clone_indicator.setStyleSheet("background-color: blue;")
        lineView_clone_layout.addWidget(lineView_clone_indicator)

        # lineView_clone (오른쪽) - read-only
        self.lineView_clone = DragDropCodeEditor()
        self.lineView_clone.setFont(QtGui.QFont(g_font_face, g_font_size))
        self.lineView_clone.setReadOnly(True)  # 읽기 전용
        self.lineView_clone.fileDropped.connect(self.load_dropped_file)  # 파일 drop 허용
        # lineView_clone의 current line 배경색을 연한 green으로 설정
        self.lineView_clone.cursorPositionChanged.connect(self.highlight_current_line_clone)

        lineView_clone_layout.addWidget(self.lineView_clone)

        # 가로 splitter에 컨테이너 추가
        splitter_horizontal.addWidget(lineView_container)
        splitter_horizontal.addWidget(lineView_clone_container)

        # 요청사항 2: 초기 비율 99:1 설정
        splitter_horizontal.setSizes([9990, 10])

        # tblResults
        self.tblResults = DragTableView()
        self.tblResults.setFont(QtGui.QFont(g_font_face, g_font_size))
        self.tblResults.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tblResults.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tblResults.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tblResults.verticalHeader().setVisible(False)
        self.tblResults.setAlternatingRowColors(True)
        self.tblResults.setWordWrap(False)
        self.tblResults.setTextElideMode(Qt.ElideNone)
        self.tblResults.setItemDelegateForColumn(1, NoWrapDelegate(self.tblResults))
        self.tblResults.setShowGrid(False)

        self.resultsModel = ResultsModel()
        self.tblResults.setModel(self.resultsModel)
        self.tblResults.doubleClicked.connect(self.on_table_double_clicked)

        # 초기 헤더 width 설정
        header = self.tblResults.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)
        self.tblResults.setColumnWidth(1, 1300)

        # 세로 splitter에 추가
        splitter_vertical.addWidget(splitter_horizontal)
        splitter_vertical.addWidget(self.tblResults)
        splitter_vertical.setStretchFactor(0, 3)
        splitter_vertical.setStretchFactor(1, 1)

        # 상태바
        self.status = QtWidgets.QStatusBar()
        self.lbl_status = QtWidgets.QLabel("")
        self.status.addWidget(self.lbl_status)
        self.setStatusBar(self.status)

        # 우측: 폰트 사이즈 라벨
        self.lable_lineView = QtWidgets.QLabel("")
        self.lable_tblResults = QtWidgets.QLabel("")
        self.lable_lineView.setStyleSheet("color: #404040;")
        self.lable_tblResults.setStyleSheet("color: #404040;")
        self.status.addPermanentWidget(self.lable_lineView)
        self.status.addPermanentWidget(self.lable_tblResults)

        # 초기 폰트 사이즈 표시
        self.update_lineview_font_label(self.lineView.font().pointSize())
        self.update_tbl_font_label(self.tblResults.font().pointSize())

        # 폰트 변경 시 라벨 업데이트 연결
        self.lineView.fontSizeChanged.connect(self.update_lineview_font_label)
        self.lineView_clone.fontSizeChanged.connect(self.update_lineview_font_label)  # clone도 연동
        self.tblResults.fontSizeChanged.connect(self.update_tbl_font_label)

        # 중앙 위젯 구성
        central = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(top_widget)
        layout.addWidget(splitter_vertical, 1)
        self.setCentralWidget(central)

        # 시그널
        self.btn_open.clicked.connect(self.open_file)
        self.btn_search.clicked.connect(self.do_search)
        self.btn_stop.clicked.connect(self.stop_search)
        self.btn_result_search_prev.clicked.connect(self.search_in_results_prev)
        self.btn_result_search_next.clicked.connect(self.search_in_results_next)

        self.on_mode_changed(1)

        # 즐겨찾기 콤보박스 초기 로딩
        self.refresh_favorite_combobox()

    # ---------------- 즐겨찾기 콤보박스 관련 메서드 ----------------
    def refresh_favorite_combobox(self):
        """즐겨찾기 JSON 파일을 읽어서 cmb_favorites를 category별로 구성"""
        json_path = "./fav/edit_query.json"
        favorites = self._load_favorites_from_file(json_path)

        self.cmb_favorites.clear()
        self.cmb_favorites.addItem("-- 즐겨찾기(F5:적용) --", None)

        self._populate_combobox_recursive(favorites, "")

    def _populate_combobox_recursive(self, nodes: List[dict], prefix: str):
        """재귀적으로 폴더 구조를 탐색하여 ComboBox에 항목 추가"""
        for node in nodes:
            if node.get('type') == 'folder':
                folder_name = node.get('name', '')
                new_prefix = f"{prefix}{folder_name}/" if prefix else f"{folder_name}/"
                children = node.get('children', [])
                self._populate_combobox_recursive(children, new_prefix)
            else:  # item
                name = node.get('name', '')
                value = node.get('value', '')
                display_text = f"{prefix}{name}" if prefix else name
                self.cmb_favorites.addItem(display_text, value)
                # 툴팁에 값 표시
                index = self.cmb_favorites.count() - 1
                self.cmb_favorites.setItemData(index, value, Qt.ToolTipRole)

    def on_favorite_combobox_changed(self, index: int):
        """콤보박스 선택 변경 시 툴팁 업데이트"""
        if index > 0:
            value = self.cmb_favorites.itemData(index)
            if value:
                self.cmb_favorites.setToolTip(f"값: {value}")
        else:
            self.cmb_favorites.setToolTip("기본 검색어 즐겨찾기 항목 선택 (F5:로딩)")

    def load_favorite_from_combobox(self):
        """cmb_favorites에서 선택된 항목의 값을 edt_query에 로딩하고 포커스 설정"""
        index = self.cmb_favorites.currentIndex()
        if index <= 0:
            QtWidgets.QMessageBox.information(self, "안내", "즐겨찾기 항목을 선택하세요.")
            return

        value = self.cmb_favorites.itemData(index)
        if value:
            self.edt_query.setText(value)
            self.edt_query.setFocus()
            self.status.showMessage("즐겨찾기 항목이 로드되었습니다.", 2000)
        else:
            QtWidgets.QMessageBox.warning(self, "경고", "선택한 항목의 값이 없습니다.")

    def highlight_current_line_clone(self):
        """lineView_clone의 current line을 연한 green으로 하이라이트"""
        extraSelections = []
        extraSelections.extend(self.lineView_clone.color_highlight_selections)

        if not self.lineView_clone.isReadOnly():
            selection = QtWidgets.QTextEdit.ExtraSelection()
            lineColor = QtGui.QColor(200, 255, 200)  # 연한 green
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            selection.cursor = self.lineView_clone.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        else:
            # read-only 상태에서도 현재 줄 강조 표시
            selection = QtWidgets.QTextEdit.ExtraSelection()
            lineColor = QtGui.QColor(200, 255, 200)  # 연한 green
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            selection.cursor = self.lineView_clone.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)

        self.lineView_clone.setExtraSelections(extraSelections)

    # ---------------- All data clear ----------------
    def all_data_clear(self):
        """로드된 파일 및 관련 표시를 모두 초기화"""
        try:
            # 검색 중이면 중지
            self.stop_search()
            # 현재 파일/결과/상태 초기화
            self.close_current_file()
            # 파일 라벨/상태/프로그레스/테이블 선택 초기화
            self.lbl_file.setText("파일 없음")
            self.lbl_status.setText("")
            self.prog.setValue(0)
            self.tblResults.clearSelection()

            # 헤더 width 초기화
            header = self.tblResults.horizontalHeader()
            header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
            header.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)
            self.tblResults.setColumnWidth(1, 1300)

            self.status.showMessage("All data cleared", 3000)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"초기화 중 오류: {e}")

    # ---------------- 우측 하단 폰트 라벨 업데이트 ----------------
    def update_lineview_font_label(self, size: int):
        self.lable_lineView.setText(f"상단창: {size}pt")

    def update_tbl_font_label(self, size: int):
        self.lable_tblResults.setText(f"하단창: {size}pt")

    # ---------------- 유틸: 선택문자열을 지정 LineEdit에 추가 ----------------
    def append_text_to_lineedit(self, lineedit: QtWidgets.QLineEdit, text: str):
        """
        - 대상 LineEdit에 현재 문자열이 없으면 text로 교체
        - 문자열이 있고, 끝 문자가 '|'이면 그대로 text 이어붙임
        - 문자열이 있고, 끝 문자가 '|'가 아니면 '|' + text 이어붙임
        """
        current = lineedit.text()
        if not current:
            lineedit.setText(text)
        else:
            if current.endswith('|'):
                lineedit.setText(current + text)
            else:
                lineedit.setText(current + '|' + text)

    # ---------------- 라인 복사 기능 추가 ----------------
    def copy_lines_between(self, line1: int, line2: int):
        """두 라인 번호 사이의 내용을 클립보드에 복사"""
        if line1 == line2:
            QtWidgets.QMessageBox.information(self, "안내", "같은 라인입니다.")
            return

        # 순서 정렬
        start_line = min(line1, line2)
        end_line = max(line1, line2)

        # 텍스트 가져오기
        content = self.lineView.toPlainText()
        lines = content.split('\n')

        if start_line < 1 or end_line > len(lines):
            QtWidgets.QMessageBox.warning(self, "경고", "라인 번호가 범위를 벗어났습니다.")
            return

        # 사이의 내용 추출
        selected_lines = lines[start_line - 1:end_line]
        selected_text = '\n'.join(selected_lines)

        # 클립보드에 복사
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(selected_text)

        self.status.showMessage(
            f"라인 {start_line}~{end_line} 복사됨 ({len(selected_lines)}줄)",
            3000
        )

    # ---------------- 마킹 관련 메서드 추가 ----------------
    def goto_next_marked_result_from_table(self):
        """tblResults에서 F2: 다음 마킹된 결과로 이동"""
        if not self.resultsModel.marked_rows:
            self.status.showMessage("마킹된 항목이 없습니다", 2000)
            return

        current_row = self.tblResults.currentIndex().row()
        next_row = self.resultsModel.get_next_marked_row(current_row if current_row is not None else -1)

        if next_row >= 0:
            index = self.resultsModel.index(next_row, 0)
            self.tblResults.setCurrentIndex(index)
            self.tblResults.scrollTo(index, QtWidgets.QAbstractItemView.PositionAtCenter)

            # lineView에서 해당 라인으로 이동
            result = self.resultsModel.get(next_row)
            line_number = result.line + 1
            self.lineView.gotoLine(line_number)
            self.update_all_highlights(result)

            # focus는 tblResults로 다시 설정
            self.tblResults.setFocus()
        else:
            self.status.showMessage("다음 마킹된 항목이 없습니다", 2000)

    def goto_prev_marked_result_from_table(self):
        """tblResults에서 Shift+F2: 이전 마킹된 결과로 이동"""
        if not self.resultsModel.marked_rows:
            self.status.showMessage("마킹된 항목이 없습니다", 2000)
            return

        current_row = self.tblResults.currentIndex().row()
        if current_row is None or current_row < 0:
            prev_row = max(self.resultsModel.marked_rows) if self.resultsModel.marked_rows else -1
        else:
            prev_row = self.resultsModel.get_prev_marked_row(current_row)

        if prev_row >= 0:
            index = self.resultsModel.index(prev_row, 0)
            self.tblResults.setCurrentIndex(index)
            self.tblResults.scrollTo(index, QtWidgets.QAbstractItemView.PositionAtCenter)

            # lineView에서 해당 라인으로 이동
            result = self.resultsModel.get(prev_row)
            line_number = result.line + 1
            self.lineView.gotoLine(line_number)
            self.update_all_highlights(result)

            # focus는 tblResults로 다시 설정
            self.tblResults.setFocus()
        else:
            self.status.showMessage("이전 마킹된 항목이 없습니다", 2000)

    def on_table_double_clicked(self, index: QModelIndex):
        """테이블 왼쪽 더블클릭: lineView로 이동만"""
        self.goto_result_from_table(index)

    def toggle_result_mark(self, row: int):
        """테이블 오른쪽 더블클릭: 마킹 토글만"""
        if row < 0 or row >= self.resultsModel.rowCount():
            return
        self.resultsModel.toggle_mark(row)
        self.status.showMessage(f"Row {row + 1} marking toggled", 2000)

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

    # ---------------- 즐겨찾기 파일 로드/저장 헬퍼 ----------------
    def _load_favorites_from_file(self, json_path: str) -> List[dict]:
        """FavoriteDialog의 포맷과 동일한 구조로 favorites 로드"""
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    favs = data.get('favorites', [])
                    needs_migrate = False
                    for e in favs:
                        if not isinstance(e, dict) or 'type' not in e:
                            needs_migrate = True
                            break
                    if needs_migrate:
                        migrated = []
                        for e in favs:
                            if isinstance(e, dict) and 'name' in e and 'value' in e:
                                migrated.append({'type': 'item', 'name': e['name'], 'value': e.get('value', '')})
                        return migrated
                    return favs
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "오류", f"즐겨찾기 로드 실패: {e}")
                return []
        return []

    def _save_favorites_to_file(self, json_path: str, favorites: List[dict]):
        """FavoriteDialog의 포맷으로 저장"""
        try:
            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({'favorites': favorites}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"즐겨찾기 저장 실패: {e}")

    def _open_favorites_with_quick_add(self, title: str, json_path: str, base_value: str,
                                       target_lineedit: QtWidgets.QLineEdit):
        """즐겨찾기 빠른 추가 + 관리 다이얼로그"""
        # 1) 빠른 추가 UX
        add_dlg = FavoriteAddDialog(current_value=base_value, parent=self)
        if add_dlg.exec() == QtWidgets.QDialog.Accepted:
            favs = self._load_favorites_from_file(json_path)
            favs.append({'type': 'item', 'name': add_dlg.name, 'value': add_dlg.value})
            self._save_favorites_to_file(json_path, favs)
            # 콤보박스 갱신
            if json_path == "./fav/edit_query.json":
                self.refresh_favorite_combobox()

        # 2) 즐겨찾기 다이얼로그 열기
        dialog = FavoriteDialog(title, json_path, base_value, self)
        if dialog.exec() == QtWidgets.QDialog.Accepted and dialog.selected_value is not None:
            target_lineedit.setText(dialog.selected_value)

        # 다이얼로그 닫힌 후에도 콤보박스 갱신
        if json_path == "./fav/edit_query.json":
            self.refresh_favorite_combobox()

    # ---------------- 즐겨찾기 관련 ----------------
    def show_query_favorites(self):
        """기본 검색어 즐겨찾기"""
        base_value = self.edt_query.text()
        json_path = "./fav/edit_query.json"
        self._open_favorites_with_quick_add("기본 검색어 즐겨찾기", json_path, base_value, self.edt_query)

    def show_result_search_favorites(self):
        """검색결과에서 검색 즐겨찾기"""
        base_value = self.edt_result_search.text()
        json_path = "./fav/edt_result_search.json"
        self._open_favorites_with_quick_add("검색결과에서 검색 즐겨찾기", json_path, base_value, self.edt_result_search)

    def show_color_keywords_favorites(self):
        """Color 키워드 즐겨찾기"""
        base_value = self.edt_color_keywords.text()
        json_path = "./fav/edt_color_keywords.json"
        self._open_favorites_with_quick_add("Highlight Color 즐겨찾기", json_path, base_value, self.edt_color_keywords)

    # ---------------- 설정 저장/불러오기 ----------------
    def save_config(self):
        """현재 설정 저장"""
        dialog = ConfigSaveDialog(self)
        if dialog.exec() != QtWidgets.QDialog.Accepted:
            return

        config_name = dialog.config_name

        config = {
            'query': self.edt_query.text(),
            'search_mode': self.cmb_mode.currentText(),
            'case_sensitive': self.chk_case.isChecked(),
            'result_search': self.edt_result_search.text(),
            'color_keywords': self.edt_color_keywords.text(),
            'recursive_search': self.chk_recursive_search.isChecked(),
            'marked_rows': list(self.resultsModel.marked_rows),
        }

        config_dir = "./config"
        os.makedirs(config_dir, exist_ok=True)

        existing_files = [f for f in os.listdir(config_dir) if f.endswith('.json')]
        index = len(existing_files) + 1

        now = datetime.now()
        date_str = now.strftime("%Y%m%d_%H%M%S")

        filename = f"{index:04d}_{date_str}_{config_name}.json"
        filepath = os.path.join(config_dir, filename)

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

            self.edt_query.setText(config.get('query', ''))

            search_mode = config.get('search_mode', '정규식')
            index = self.cmb_mode.findText(search_mode)
            if index >= 0:
                self.cmb_mode.setCurrentIndex(index)

            self.chk_case.setChecked(config.get('case_sensitive', False))
            self.edt_result_search.setText(config.get('result_search', ''))
            self.edt_color_keywords.setText(config.get('color_keywords', ''))
            self.chk_recursive_search.setChecked(config.get('recursive_search', False))

            marked_rows = config.get('marked_rows', [])
            self.resultsModel.marked_rows = set(marked_rows)
            if marked_rows:
                self.resultsModel.dataChanged.emit(
                    self.resultsModel.index(0, 0),
                    self.resultsModel.index(self.resultsModel.rowCount() - 1,
                                            self.resultsModel.columnCount() - 1)
                )

            self.status.showMessage(f"설정 불러오기 완료: {os.path.basename(filepath)}", 5000)
            QtWidgets.QMessageBox.information(self, "완료", "설정을 불러왔습니다.")

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"설정 불러오기 실패: {e}")

    # ---------------- 최신 설정(자동 저장/로드) ----------------
    def latest_config_file_path(self) -> str:
        return os.path.join(".", "config", "latest_config.json")

    def build_latest_config(self) -> dict:
        """파일 관련 정보는 저장하지 않고, UI 설정값 + 윈도우 상태 저장"""
        cfg = {
            'query': self.edt_query.text(),
            'search_mode': self.cmb_mode.currentText(),
            'case_sensitive': self.chk_case.isChecked(),
            'result_search': self.edt_result_search.text(),
            'color_keywords': self.edt_color_keywords.text(),
            'recursive_search': self.chk_recursive_search.isChecked(),
            'prev_lines': self.edt_prev_lines.text(),
            'next_lines': self.edt_next_lines.text(),
            'lineView_font_pt': self.lineView.font().pointSize(),
            'tblResults_font_pt': self.tblResults.font().pointSize(),
            'always_on_top': self.always_on_top_action.isChecked(),
            # 윈도우 상태 추가
            'window_geometry': {
                'x': self.geometry().x(),
                'y': self.geometry().y(),
                'width': self.geometry().width(),
                'height': self.geometry().height()
            },
            'window_state': 'maximized' if self.isMaximized() else 'normal'
        }
        return cfg

    def apply_latest_config(self, cfg: dict):
        """저장된 설정 적용 + 윈도우 상태 복원"""
        try:
            # 검색 모드
            search_mode = cfg.get('search_mode')
            if search_mode:
                idx = self.cmb_mode.findText(search_mode)
                if idx >= 0:
                    self.cmb_mode.setCurrentIndex(idx)

            # 대소문자
            if 'case_sensitive' in cfg:
                self.chk_case.setChecked(bool(cfg.get('case_sensitive', False)))

            # 쿼리/검색결과 검색
            self.edt_query.setText(cfg.get('query', ''))
            self.edt_result_search.setText(cfg.get('result_search', ''))

            # 되돌이 검색
            self.chk_recursive_search.setChecked(bool(cfg.get('recursive_search', False)))

            # 컨텍스트 라인 수
            if 'prev_lines' in cfg:
                self.edt_prev_lines.setText(str(cfg.get('prev_lines')))
            if 'next_lines' in cfg:
                self.edt_next_lines.setText(str(cfg.get('next_lines')))

            # 폰트 사이즈
            lv_pt = cfg.get('lineView_font_pt')
            if isinstance(lv_pt, int) and lv_pt > 0:
                f = QtGui.QFont(g_font_face, lv_pt)
                self.lineView.setFont(f)
                self.lineView_clone.setFont(f)
                self.update_lineview_font_label(lv_pt)

            tbl_pt = cfg.get('tblResults_font_pt')
            if isinstance(tbl_pt, int) and tbl_pt > 0:
                f2 = QtGui.QFont(g_font_face, tbl_pt)
                self.tblResults.setFont(f2)
                self.update_tbl_font_label(tbl_pt)

            # 항상 위
            if 'always_on_top' in cfg:
                self.always_on_top_action.setChecked(bool(cfg.get('always_on_top', False)))

            # Color 키워드
            color_text = cfg.get('color_keywords', '')
            self.edt_color_keywords.setText(color_text)
            if color_text:
                self.on_color_settings_clicked()

            # 윈도우 상태 복원
            geom = cfg.get('window_geometry')
            if geom and isinstance(geom, dict):
                x = geom.get('x', 100)
                y = geom.get('y', 100)
                width = geom.get('width', g_win_size_w)
                height = geom.get('height', g_win_size_h)
                self.setGeometry(x, y, width, height)

            window_state = cfg.get('window_state', 'normal')
            if window_state == 'maximized':
                self.showMaximized()
            else:
                self.showNormal()

        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "경고", f"최신 설정 적용 중 일부 오류가 발생했습니다: {e}")

    def save_latest_config(self):
        """앱 종료 시 최신 설정 저장"""
        try:
            cfg = self.build_latest_config()
            path = self.latest_config_file_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"latest_config 저장 실패: {e}")

    def load_latest_config(self):
        """앱 시작 시 최신 설정 자동 로드"""
        path = self.latest_config_file_path()
        if not os.path.exists(path):
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            self.apply_latest_config(cfg)
            self.status.showMessage("최신 설정을 불러왔습니다.", 3000)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "경고", f"최신 설정 불러오기 실패: {e}")

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
        global debug_measuretime_start, debug_measuretime_snapshot
        debug_measuretime_start = time.time()

        self.close_current_file()
        self.current_file_path = path

        self.lbl_file.setText("로딩 중: " + path)
        self.prog.setValue(0)
        self.lineView.setEnabled(False)
        self.lineView_clone.setEnabled(False)  # clone도 비활성화

        self.file_thread = QtCore.QThread(self)
        self.file_loader = FileLoader(path)
        self.file_loader.moveToThread(self.file_thread)
        self.file_thread.started.connect(self.file_loader.run)
        self.file_loader.progress.connect(self.prog.setValue)
        self.file_loader.failed.connect(self.on_file_failed)
        self.file_loader.finished.connect(self.on_file_loaded)
        self.file_thread.start()

    def open_file(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "파일 선택", "", "Log/Text Files (*.txt *.log *.*)")
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
        self.lineView_clone.setEnabled(True)
        if self.file_thread:
            self.file_thread.quit()
            self.file_thread.wait()

    def on_file_loaded(self, content: str, encoding: str, duration: float):
        """파일 로딩 완료 - lineView_clone에도 동일 내용 loading"""
        if self.file_thread:
            self.file_thread.quit()
            self.file_thread.wait()

        self.content = content
        self.encoding = encoding

        global debug_measuretime_start, debug_measuretime_snapshot
        debug_measuretime_snapshot = time.time()
        print(f"debug_measuretime_duration(on_file_loaded) : {debug_measuretime_snapshot - debug_measuretime_start:.4f} sec")

        # lineView와 lineView_clone 모두에 내용 설정
        self.lineView.setPlainText(content)
        self.lineView_clone.setPlainText(content)  # clone에도 동일 내용 loading

        self.lineView.setEnabled(True)
        self.lineView_clone.setEnabled(True)

        debug_measuretime_snapshot = time.time()
        print(f"debug_measuretime_duration(lineView.setPlainText) : {debug_measuretime_snapshot - debug_measuretime_start:.4f} sec")

        self.lbl_file.setText(f"파일: {len(content)} chars, 인코딩: {encoding}, 라인: {len(content.split(chr(10)))}")

        # lbl_status에 로딩 시간 표시
        self.lbl_status.setText(f"Loading duration : {duration:.2f} sec(s)")
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
        self.setWindowTitle(f"Andy Finder - {os.path.basename(self.current_file_path)} - {gCurVerInfo}")

        if self.color_keywords:
            self.apply_color_highlights()

    def close_current_file(self):
        self.resultsModel.set_results([])
        self.current_results = []
        self.current_result_index = -1
        self.content = ""
        self.lineView.clear()
        self.lineView_clone.clear()  # clone도 clear
        self.lineView.bookmarks.clear()
        self.lineView_clone.bookmarks.clear()  # clone 북마크도 clear
        self.current_file_path = ""
        self.is_modified = False
        self.result_search_query = ""
        self.result_search_index = -1
        self.result_search_matches = []
        self.lbl_result_search_status.setText("")
        self.setWindowTitle(f"Andy Finder - {gCurVerInfo}")

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
        top_left = self.resultsModel.index(0, 1)
        bottom_right = self.resultsModel.index(self.resultsModel.rowCount() - 1, 1)
        self.resultsModel.dataChanged.emit(top_left, bottom_right)
        self.tblResults.resizeRowsToContents()

    def on_context_lines_changed(self):
        """previous/next lines 값 변경 시 현재 결과에 즉시 반영"""
        if not self.current_results:
            return
        self.apply_context_snippets_to_current_results()
        self.refresh_results_view_after_context_change()

    def do_search(self):
        if not self.lineView.toPlainText():
            QtWidgets.QMessageBox.information(self, "안내", "먼저 (dumpstate) 파일을 여세요.")
            return

        global debug_measuretime_start, debug_measuretime_snapshot
        debug_measuretime_start = time.time()

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

    def on_search_finished(self, results: List[SearchResult], duration: float):
        """검색 완료"""
        self.stop_search()
        self.current_results = results

        self.apply_context_snippets_to_current_results()
        self.resultsModel.set_results(results)

        # 헤더 리사이즈 모드
        header = self.tblResults.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        self.tblResults.setColumnWidth(1, 1500)

        self.tblResults.resizeRowsToContents()

        self.result_search_query = ""
        self.result_search_index = -1
        self.result_search_matches = []
        self.lbl_result_search_status.setText("")

        # 좌측 하단 라벨에 검색 결과 건수 + 검색 시간 표시
        self.lbl_status.setText(f"검색 결과 : {len(results)}개 | Searching duration : {duration:.2f} sec(s)")

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

        block = self.lineView.document().findBlockByNumber(r.line)
        if block.isValid():
            cursor = QtGui.QTextCursor(block)
            cursor.setPosition(block.position())
            self.lineView.setTextCursor(cursor)
            self.lineView.ensureCursorVisible()
            self.lineView.centerCursor()

        self.update_all_highlights(r)
        self.tblResults.selectRow(index.row())

        # focus는 tblResults로 유지
        self.tblResults.setFocus()

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
        pass

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
        self.lineView_clone.color_highlight_selections = []  # clone도 clear

        if self.current_result_index >= 0 and self.current_result_index < len(self.current_results):
            result = self.current_results[self.current_result_index]
            self.update_all_highlights(result)
        else:
            self.lineView.highlightCurrentLine()

        self.status.showMessage("Color 설정 초기화", 3000)

    def apply_color_highlights(self):
        """lineView와 lineView_clone 모두에 color highlight 적용"""
        if not self.lineView.toPlainText():
            return

        color_selections = []
        color_selections_clone = []

        if self.color_keywords:
            content = self.lineView.toPlainText()
            for keyword, color in self.color_keywords:
                try:
                    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
                    for match in pattern.finditer(content):
                        # lineView용
                        selection = QtWidgets.QTextEdit.ExtraSelection()
                        selection.format.setBackground(color)
                        cursor = QtGui.QTextCursor(self.lineView.document())
                        cursor.setPosition(match.start())
                        cursor.setPosition(match.end(), QtGui.QTextCursor.KeepAnchor)
                        selection.cursor = cursor
                        color_selections.append(selection)

                        # lineView_clone용
                        selection_clone = QtWidgets.QTextEdit.ExtraSelection()
                        selection_clone.format.setBackground(color)
                        cursor_clone = QtGui.QTextCursor(self.lineView_clone.document())
                        cursor_clone.setPosition(match.start())
                        cursor_clone.setPosition(match.end(), QtGui.QTextCursor.KeepAnchor)
                        selection_clone.cursor = cursor_clone
                        color_selections_clone.append(selection_clone)
                except re.error:
                    pass

        self.lineView.color_highlight_selections = color_selections
        self.lineView_clone.color_highlight_selections = color_selections_clone

        if self.current_result_index >= 0 and self.current_result_index < len(self.current_results):
            result = self.current_results[self.current_result_index]
            self.update_all_highlights(result)
        else:
            self.lineView.highlightCurrentLine()
            # clone도 highlight 적용
            self.lineView_clone.highlightCurrentLine()

    def search_in_results_next(self):
        query = self.edt_result_search.text().strip()
        if not query:
            return

        if not self.current_results:
            self.lbl_result_search_status.setText("검색 결과가 없습니다")
            return

        # 검색어가 바뀌면 매칭 리스트 재생성
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

        if not self.result_search_matches:
            self.lbl_result_search_status.setText("일치하는 항목 없음")
            return

        is_recursive = self.chk_recursive_search.isChecked()

        current_row = self.tblResults.currentIndex().row()
        if current_row < 0:
            current_row = -1

        # 다음 매칭 찾기
        next_match_idx = None
        for idx in self.result_search_matches:
            if idx > current_row:
                next_match_idx = idx
                break

        if next_match_idx is None:
            if is_recursive and self.result_search_matches:
                next_match_idx = self.result_search_matches[0]
            else:
                self.lbl_result_search_status.setText(
                    f"마지막 매칭 (전체 {len(self.result_search_matches)}개)"
                )
                return

        # 이동
        self.current_result_index = next_match_idx
        result = self.current_results[next_match_idx]
        self.goto_result(result)

        # 현재 매칭의 순서 계산
        match_position = self.result_search_matches.index(next_match_idx) + 1
        self.lbl_result_search_status.setText(
            f"{match_position} / {len(self.result_search_matches)}"
        )

    def search_in_results_prev(self):
        query = self.edt_result_search.text().strip()
        if not query:
            return

        if not self.current_results:
            self.lbl_result_search_status.setText("검색 결과가 없습니다")
            return

        # 검색어가 바뀌면 매칭 리스트 재생성
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

        if not self.result_search_matches:
            self.lbl_result_search_status.setText("일치하는 항목 없음")
            return

        is_recursive = self.chk_recursive_search.isChecked()

        current_row = self.tblResults.currentIndex().row()
        if current_row < 0:
            current_row = len(self.current_results)

        # 이전 매칭 찾기
        prev_match_idx = None
        for idx in reversed(self.result_search_matches):
            if idx < current_row:
                prev_match_idx = idx
                break

        if prev_match_idx is None:
            if is_recursive and self.result_search_matches:
                prev_match_idx = self.result_search_matches[-1]
            else:
                self.lbl_result_search_status.setText(
                    f"첫 번째 매칭 (전체 {len(self.result_search_matches)}개)"
                )
                return

        # 이동
        self.current_result_index = prev_match_idx
        result = self.current_results[prev_match_idx]
        self.goto_result(result)

        # 현재 매칭의 순서 계산
        match_position = self.result_search_matches.index(prev_match_idx) + 1
        self.lbl_result_search_status.setText(
            f"{match_position} / {len(self.result_search_matches)}"
        )

    def keyPressEvent(self, event):
        # F11: 전체화면 토글
        if event.key() == Qt.Key_F11:
            self.toggle_fullscreen()
            event.accept()
            return

        # lineView나 lineView_clone에 포커스가 있고 search_dialog가 열려있으면 해당 editor의 검색이 처리
        if (self.lineView.hasFocus() and self.lineView.search_dialog and self.lineView.search_dialog.isVisible()) or \
                (self.lineView_clone.hasFocus() and self.lineView_clone.search_dialog and self.lineView_clone.search_dialog.isVisible()):
            return

        # edt_result_search나 tblResults에 포커스가 있을 때만 F3/F4 처리
        if self.edt_result_search.hasFocus() or self.tblResults.hasFocus():
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
                self.save_latest_config()
                event.accept()
            elif reply == QtWidgets.QMessageBox.Discard:
                self.save_latest_config()
                event.accept()
            else:
                event.ignore()
        else:
            self.save_latest_config()
            event.accept()

    def toggle_fullscreen(self):
        """F11: 전체화면과 이전 상태를 토글"""
        if self.isFullScreen():
            # 전체화면 -> 이전 상태로 복원
            self.showNormal()
            if self._previous_geometry:
                self.setGeometry(self._previous_geometry)

            if self._previous_window_state == Qt.WindowMaximized:
                self.showMaximized()

            self.status.showMessage("전체화면 종료", 2000)
        else:
            # 현재 상태 저장
            self._previous_geometry = self.geometry()
            self._previous_window_state = Qt.WindowMaximized if self.isMaximized() else Qt.WindowNoState

            # 전체화면으로 전환
            self.showFullScreen()
            self.status.showMessage("전체화면 모드 (F11: 종료)", 2000)


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