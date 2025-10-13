# -*- coding: utf-8 -*-
"""
TabContent - 각 탭의 컨텐츠를 담당하는 위젯
"""
import os
import re
import json
import time
from typing import List, Tuple, Optional

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QModelIndex

# andyfinder 모듈에서 import
from andyfinder.constants import (
    g_font_face, g_font_size,
    debug_measuretime_start, debug_measuretime_snapshot
)
from andyfinder.models import SearchResult
from andyfinder.widgets.line_edit import (
    QueryLineEdit,
    ColorKeywordsLineEdit,
    ResultSearchLineEdit
)
from andyfinder.widgets.combo_box import FavoriteComboBox
from andyfinder.editors.drag_drop_editor import DragDropCodeEditor
from andyfinder.views.drag_table_view import DragTableView
from andyfinder.views.results_model import ResultsModel, NoWrapDelegate
from andyfinder.workers.file_loader import FileLoader
from andyfinder.workers.search_worker import SearchWorker
from andyfinder.dialogs.favorite_dialogs import FavoriteDialog, FavoriteAddDialog


class TabContent(QtWidgets.QWidget):
    """각 탭의 컨텐츠를 담당하는 위젯"""

    def __init__(self, tab_number: int, parent=None):
        super().__init__(parent)
        self.tab_number = tab_number

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

        self.btn_clear_colors = QtWidgets.QPushButton("Clear")
        self.btn_clear_colors.clicked.connect(self.on_color_clear_clicked)

        fifth_layout.addWidget(self.btn_color_keywords_fav)
        fifth_layout.addWidget(self.edt_color_keywords, 1)
        fifth_layout.addWidget(self.btn_clear_colors)
        fifth_layout.addStretch()

        top_layout.addWidget(first_row)
        top_layout.addWidget(second_row)
        top_layout.addWidget(third_row)
        top_layout.addWidget(fourth_row)
        top_layout.addWidget(fifth_row)

        # ===== 변경: 세로 splitter 추가 (top_widget와 중앙 컨텐츠 사이) =====
        main_vertical_splitter = QtWidgets.QSplitter()
        main_vertical_splitter.setOrientation(Qt.Vertical)
        main_vertical_splitter.setStyleSheet("""
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

        # 중앙: 세로 splitter (기존의 splitter_vertical)
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

        # =============================== LEFT viewer ===============================
        # lineView (왼쪽) - 컨테이너 위젯 생성
        lineView_container = QtWidgets.QWidget()
        lineView_layout = QtWidgets.QVBoxLayout(lineView_container)
        lineView_layout.setContentsMargins(0, 0, 0, 0)
        lineView_layout.setSpacing(0)

        lineView_lbl_container = QtWidgets.QWidget()
        lineView_lbl_layout = QtWidgets.QHBoxLayout(lineView_lbl_container)
        lineView_lbl_layout.setContentsMargins(0, 0, 0, 0)
        lineView_lbl_layout.setSpacing(0)
        lineView_layout.addWidget(lineView_lbl_container)

        # Left 사각형 위젯 (lineView 상단)
        lineView_indicator = QtWidgets.QWidget()
        lineView_indicator.setFixedWidth(10)
        lineView_indicator.setFixedHeight(10)
        lineView_indicator.setStyleSheet("background-color: brown;")
        lineView_lbl_layout.addWidget(lineView_indicator)

        # 라벨 추가 (lineView 상단) - 변경된 부분
        self.lable_lineView = QtWidgets.QLabel()
        self.lable_lineView.setStyleSheet("color: black; brown; padding: 2px; font-weight: bold;")
        self.lable_lineView.setAlignment(Qt.AlignLeft)
        self.lable_lineView.setMinimumWidth(50)
        lineView_lbl_layout.addWidget(self.lable_lineView)

        # lineView
        self.lineView = DragDropCodeEditor()
        self.lineView.setFont(QtGui.QFont(g_font_face, g_font_size))
        self.lineView.textChanged.connect(self.on_text_changed)
        self.lineView.fileDropped.connect(self.load_dropped_file)
        self.lineView.cursorPositionChanged.connect(self.highlight_current_line)
        # 북마크 변경 시그널 연결 추가
        self.lineView.cursorPositionChanged.connect(self.update_bookmark_labels)

        lineView_layout.addWidget(self.lineView)

        # =============================== RIGHT viewer ===============================
        # lineView_clone (오른쪽) - 컨테이너 위젯 생성
        lineView_clone_container = QtWidgets.QWidget()
        lineView_clone_layout = QtWidgets.QVBoxLayout(lineView_clone_container)
        lineView_clone_layout.setContentsMargins(0, 0, 0, 0)
        lineView_clone_layout.setSpacing(0)

        lineView_lbl_clone_container = QtWidgets.QWidget()
        lineView_lbl_clone_layout = QtWidgets.QHBoxLayout(lineView_lbl_clone_container)
        lineView_lbl_clone_layout.setContentsMargins(0, 0, 0, 0)
        lineView_lbl_clone_layout.setSpacing(0)
        lineView_clone_layout.addWidget(lineView_lbl_clone_container)

        # RIGHT 사각형 위젯 (lineView_clone 상단)
        lineView_clone_indicator = QtWidgets.QWidget()
        lineView_clone_indicator.setFixedWidth(10)
        lineView_clone_indicator.setFixedHeight(10)
        lineView_clone_indicator.setStyleSheet("background-color: blue;")
        lineView_lbl_clone_layout.addWidget(lineView_clone_indicator)

        # 라벨 추가 (lineView_clone 상단) - 새로 추가된 부분
        self.lable_lineView_clone = QtWidgets.QLabel("")
        self.lable_lineView_clone.setStyleSheet("color: black; padding: 2px; font-weight: bold;")
        self.lable_lineView_clone.setAlignment(Qt.AlignLeft)
        self.lable_lineView_clone.setMinimumWidth(50)
        lineView_lbl_clone_layout.addWidget(self.lable_lineView_clone)

        # lineView_clone (오른쪽) - read-only
        self.lineView_clone = DragDropCodeEditor()
        self.lineView_clone.setFont(QtGui.QFont(g_font_face, g_font_size))
        self.lineView_clone.setReadOnly(True)  # 읽기 전용
        #self.lineView_clone.fileDropped.connect(self.load_dropped_file)
        self.lineView_clone.cursorPositionChanged.connect(self.highlight_current_line_clone)
        # 북마크 변경 시그널 연결 추가
        self.lineView_clone.cursorPositionChanged.connect(self.update_bookmark_labels)

        lineView_clone_layout.addWidget(self.lineView_clone)

        # lineView 와 lineView_clone에 CurrentLine color 설정
        self.lineView.highlightCurrentLine()
        self.lineView_clone.highlightCurrentLine()

        # 가로 splitter에 컨테이너 추가
        splitter_horizontal.addWidget(lineView_container)
        splitter_horizontal.addWidget(lineView_clone_container)
        splitter_horizontal.setSizes([9990, 10])

        # =============================== Result Table ===============================
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
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive)
        self.tblResults.setColumnWidth(1, 1300)

        # 세로 splitter에 추가
        splitter_vertical.addWidget(splitter_horizontal)
        splitter_vertical.addWidget(self.tblResults)
        splitter_vertical.setStretchFactor(0, 3)
        splitter_vertical.setStretchFactor(1, 1)

        # 상태바
        self.status_widget = QtWidgets.QWidget()
        status_layout = QtWidgets.QHBoxLayout(self.status_widget)
        status_layout.setContentsMargins(0, 0, 0, 0)

        self.lbl_status = QtWidgets.QLabel("")
        status_layout.addWidget(self.lbl_status, 1)

        # 우측: 폰트 사이즈 라벨
        self.lable_tblResults = QtWidgets.QLabel("")
        self.lable_tblResults.setStyleSheet("color: #404040;")
        status_layout.addWidget(self.lable_tblResults)

        # 초기 폰트 사이즈 및 북마크 표시
        self.update_lineview_font_label(self.lineView.font().pointSize())
        self.update_tbl_font_label(self.tblResults.font().pointSize())
        self.update_bookmark_labels()  # 초기 북마크 개수 표시

        # 폰트 변경 시 라벨 업데이트 연결
        self.lineView.fontSizeChanged.connect(self.update_lineview_font_label)
        self.lineView_clone.fontSizeChanged.connect(self.update_lineview_font_label)
        self.tblResults.fontSizeChanged.connect(self.update_tbl_font_label)

        # ===== 변경: main_vertical_splitter에 top_widget와 splitter_vertical 추가 =====
        main_vertical_splitter.addWidget(top_widget)
        main_vertical_splitter.addWidget(splitter_vertical)
        # top_widget는 작게, splitter_vertical은 크게
        main_vertical_splitter.setStretchFactor(0, 1)
        main_vertical_splitter.setStretchFactor(1, 10)

        # 중앙 위젯 구성
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(main_vertical_splitter, 1)  # 변경: top_widget 대신 main_vertical_splitter 추가
        layout.addWidget(self.status_widget)

        # 시그널
        self.btn_open.clicked.connect(self.open_file)
        self.btn_search.clicked.connect(self.do_search)
        self.btn_stop.clicked.connect(self.stop_search)
        self.btn_result_search_prev.clicked.connect(self.search_in_results_prev)
        self.btn_result_search_next.clicked.connect(self.search_in_results_next)

        self.on_mode_changed(1)

        # 즐겨찾기 콤보박스 초기 로딩
        self.refresh_favorite_combobox()

    # 폰트 라벨 업데이트
    def update_lineview_font_label(self, size: int):
        self.lable_lineView.setText(f"상단창: {size}pt")

    def update_tbl_font_label(self, size: int):
        self.lable_tblResults.setText(f"하단창: {size}pt")

    # 즐겨찾기 콤보박스 관련
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
            self.show_status_message("즐겨찾기 항목이 로드되었습니다.", 2000)
        else:
            QtWidgets.QMessageBox.warning(self, "경고", "선택한 항목의 값이 없습니다.")

    def highlight_current_line(self):
        extra_selections = []
        extra_selections.extend(self.lineView.color_highlight_selections)

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

    def highlight_current_line_clone(self):
        """lineView_clone의 current line을 연한 green으로 하이라이트"""
        extraSelections = []
        extraSelections.extend(self.lineView_clone.color_highlight_selections)

        # lineView_clone은 read-only이므로 항상 연한 green 배경 표시
        selection = QtWidgets.QTextEdit.ExtraSelection()
        lineColor = QtGui.QColor(200, 255, 200)  # 연한 green
        selection.format.setBackground(lineColor)
        selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
        selection.cursor = self.lineView_clone.textCursor()
        selection.cursor.clearSelection()
        extraSelections.append(selection)

        self.lineView_clone.setExtraSelections(extraSelections)

    def show_status_message(self, message: str, timeout: int = 0):
        """상태바 메시지 표시"""
        main_window = self.window()
        # MainWindow 클래스명 문자열 비교로 변경 (순환 참조 방지)
        if main_window.__class__.__name__ == 'MainWindow':
            main_window.statusBar().showMessage(message, timeout)

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

        self.show_status_message(
            f"라인 {start_line}~{end_line} 복사됨 ({len(selected_lines)}줄)",
            3000
        )

    # 마킹 관련 메서드
    def goto_next_marked_result_from_table(self):
        """tblResults에서 F2: 다음 마킹된 결과로 이동"""
        if not self.resultsModel.marked_rows:
            self.show_status_message("마킹된 항목이 없습니다", 2000)
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
            self.show_status_message("다음 마킹된 항목이 없습니다", 2000)

    def goto_prev_marked_result_from_table(self):
        """tblResults에서 Shift+F2: 이전 마킹된 결과로 이동"""
        if not self.resultsModel.marked_rows:
            self.show_status_message("마킹된 항목이 없습니다", 2000)
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
            self.show_status_message("이전 마킹된 항목이 없습니다", 2000)

    def on_table_double_clicked(self, index: QModelIndex):
        """테이블 왼쪽 더블클릭: lineView로 이동만"""
        self.goto_result_from_table(index)

    def toggle_result_mark(self, row: int):
        """테이블 오른쪽 더블클릭: 마킹 토글만"""
        if row < 0 or row >= self.resultsModel.rowCount():
            return
        self.resultsModel.toggle_mark(row)
        self.update_bookmark_labels()  # 추가
        self.show_status_message(f"Row {row + 1} marking toggled", 2000)

    # 즐겨찾기 파일 로드/저장 헬퍼
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

    # 즐겨찾기 관련
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

    # 기존 기능들
    def on_mode_changed(self, index):
        mode = self.cmb_mode.currentText()
        if mode == "일반":
            self.chk_case.setEnabled(True)
        else:
            self.chk_case.setEnabled(False)

    def on_text_changed(self):
        self.is_modified = True
        # 탭 제목에 * 표시 (MainWindow에서 처리)
        main_window = self.window()
        if main_window.__class__.__name__ == 'MainWindow':
            main_window.mark_tab_modified(self)

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
        self.lineView_clone.setEnabled(False)

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
            # 탭 제목에서 * 제거 (MainWindow에서 처리)
            main_window = self.window()
            if main_window.__class__.__name__ == 'MainWindow':
                main_window.unmark_tab_modified(self)

            self.show_status_message("파일 저장 완료: " + self.current_file_path, 3000)
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

        # 변경: lbl_file에 파일명 표시
        file_name = os.path.basename(self.current_file_path) if self.current_file_path else "Unknown"
        self.lbl_file.setText(f"파일명: {file_name} | {len(content)} chars, 인코딩: {encoding}, 라인: {len(content.split(chr(10)))}")

        # lbl_status에 로딩 시간 표시
        self.lbl_status.setText(f"Loading duration : {duration:.2f} sec(s)")
        self.show_status_message("파일 로딩 완료", 3000)

        self.resultsModel.set_results([])
        self.current_results = []
        self.current_result_index = -1
        self.prog.setValue(0)

        self.result_search_query = ""
        self.result_search_index = -1
        self.result_search_matches = []
        self.lbl_result_search_status.setText("")

        self.is_modified = False

        # MainWindow에서 탭 제목 업데이트
        main_window = self.window()
        if main_window.__class__.__name__ == 'MainWindow':
            main_window.update_tab_title(self)

        if self.color_keywords:
            self.apply_color_highlights()

    def close_current_file(self):
        self.resultsModel.set_results([])
        self.current_results = []
        self.current_result_index = -1
        self.content = ""
        self.lineView.clear()
        self.lineView_clone.clear()
        self.lineView.bookmarks.clear()
        self.lineView_clone.bookmarks.clear()
        self.current_file_path = ""
        self.is_modified = False
        self.result_search_query = ""
        self.result_search_index = -1
        self.result_search_matches = []
        self.lbl_result_search_status.setText("")

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
        self.show_status_message("검색 중...")
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
        self.show_status_message("검색 실패: " + msg, 5000)

    def on_search_finished(self, results: List[SearchResult], duration: float):
        """검색 완료"""
        self.stop_search()
        self.current_results = results

        self.apply_context_snippets_to_current_results()
        self.resultsModel.set_results(results)

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
            self.show_status_message(f"검색 완료: {len(results)}건", 8000)
        else:
            self.current_result_index = -1
            self.show_status_message("검색 결과 없음", 5000)

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
        self.show_status_message(f"Color 설정 적용: {len(keywords)}개 키워드", 3000)

    def on_color_clear_clicked(self):
        self.color_keywords = []
        self.edt_color_keywords.clear()
        self.lineView.color_highlight_selections = []
        self.lineView_clone.color_highlight_selections = []

        if self.current_result_index >= 0 and self.current_result_index < len(self.current_results):
            result = self.current_results[self.current_result_index]
            self.update_all_highlights(result)
        else:
            self.lineView.highlightCurrentLine()

        self.show_status_message("Color 설정 초기화", 3000)

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

    # 설정 저장/불러오기를 위한 메서드
    def get_config(self) -> dict:
        """현재 탭의 설정을 딕셔너리로 반환"""
        return {
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
            'marked_rows': list(self.resultsModel.marked_rows),
        }

    def apply_config(self, config: dict):
        """설정을 탭에 적용"""
        try:
            # 검색 모드
            search_mode = config.get('search_mode')
            if search_mode:
                idx = self.cmb_mode.findText(search_mode)
                if idx >= 0:
                    self.cmb_mode.setCurrentIndex(idx)

            # 대소문자
            if 'case_sensitive' in config:
                self.chk_case.setChecked(bool(config.get('case_sensitive', False)))

            # 쿼리/검색결과 검색
            self.edt_query.setText(config.get('query', ''))
            self.edt_result_search.setText(config.get('result_search', ''))

            # 되돌이 검색
            self.chk_recursive_search.setChecked(bool(config.get('recursive_search', False)))

            # 컨텍스트 라인 수
            if 'prev_lines' in config:
                self.edt_prev_lines.setText(str(config.get('prev_lines')))
            if 'next_lines' in config:
                self.edt_next_lines.setText(str(config.get('next_lines')))

            # 폰트 사이즈
            lv_pt = config.get('lineView_font_pt')
            if isinstance(lv_pt, int) and lv_pt > 0:
                f = QtGui.QFont(g_font_face, lv_pt)
                self.lineView.setFont(f)
                self.lineView_clone.setFont(f)
                self.update_lineview_font_label(lv_pt)

            tbl_pt = config.get('tblResults_font_pt')
            if isinstance(tbl_pt, int) and tbl_pt > 0:
                f2 = QtGui.QFont(g_font_face, tbl_pt)
                self.tblResults.setFont(f2)
                self.update_tbl_font_label(tbl_pt)

            # Color 키워드
            color_text = config.get('color_keywords', '')
            self.edt_color_keywords.setText(color_text)
            if color_text:
                self.on_color_settings_clicked()

            # 마킹된 행
            marked_rows = config.get('marked_rows', [])
            self.resultsModel.marked_rows = set(marked_rows)
            if marked_rows:
                self.resultsModel.dataChanged.emit(
                    self.resultsModel.index(0, 0),
                    self.resultsModel.index(self.resultsModel.rowCount() - 1,
                                            self.resultsModel.columnCount() - 1)
                )

        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "경고", f"설정 적용 중 일부 오류가 발생했습니다: {e}")

    def copy_lines_range_remove_nul(self, start_line: int, end_line: int):
        """
        start_line부터 end_line까지의 내용을 클립보드에 복사
        NUL 문자를 제거하여 복사
        (start_line, end_line 모두 포함)
        """
        if start_line == end_line:
            # 한 줄만 복사
            content = self.lineView.toPlainText()
            lines = content.split('\n')

            if start_line < 1 or start_line > len(lines):
                QtWidgets.QMessageBox.warning(self, "경고", "라인 번호가 범위를 벗어났습니다.")
                return

            selected_text = lines[start_line - 1]
        else:
            # 범위 복사
            if start_line > end_line:
                start_line, end_line = end_line, start_line

            content = self.lineView.toPlainText()
            lines = content.split('\n')

            if start_line < 1 or end_line > len(lines):
                QtWidgets.QMessageBox.warning(self, "경고", "라인 번호가 범위를 벗어났습니다.")
                return

            selected_lines = lines[start_line - 1:end_line]
            selected_text = '\n'.join(selected_lines)

        # NUL 문자 제거
        selected_text = selected_text.replace('\x00', '')

        try:
            # 클립보드에 복사
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(selected_text)

            line_count = end_line - start_line + 1
            self.show_status_message(
                f"라인 {start_line}~{end_line} 복사됨 ({line_count}줄) [NUL 문자 제거됨]",
                3000
            )
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "경고", f"복사 중 오류 발생: {e}")

    def copy_lines_to_end_remove_nul(self, start_line: int):
        """
        start_line부터 파일 끝까지의 내용을 클립보드에 복사
        NUL 문자를 제거하여 복사
        """
        content = self.lineView.toPlainText()
        lines = content.split('\n')

        if start_line < 1 or start_line > len(lines):
            QtWidgets.QMessageBox.warning(self, "경고", "라인 번호가 범위를 벗어났습니다.")
            return

        # start_line부터 끝까지 추출
        selected_lines = lines[start_line - 1:]
        selected_text = '\n'.join(selected_lines)

        # NUL 문자 제거
        selected_text = selected_text.replace('\x00', '')

        try:
            # 클립보드에 복사
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(selected_text)

            line_count = len(selected_lines)
            self.show_status_message(
                f"라인 {start_line}~끝 복사됨 ({line_count}줄) [NUL 문자 제거됨]",
                3000
            )
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "경고", f"복사 중 오류 발생: {e}")

    def update_bookmark_labels(self):
        """lineView, lineView_clone, tblResults의 북마크 개수를 라벨에 표시"""
        lineview_bookmarks = len(self.lineView.bookmarks)
        lineview_clone_bookmarks = len(self.lineView_clone.bookmarks)
        tblresults_marks = len(self.resultsModel.marked_rows)

        # lable_lineView: lineView 북마크 개수 표시
        self.lable_lineView.setText(f"Left Viewer (BM:{lineview_bookmarks}) | {self.lineView.font().pointSize()}pt")

        # lable_lineView_clone: lineView_clone 북마크 개수 표시
        self.lable_lineView_clone.setText(f"Right Viewer (BM:{lineview_clone_bookmarks}) | {self.lineView_clone.font().pointSize()}pt")

        # lable_tblResults: tblResults 마킹 개수 표시
        self.lable_tblResults.setText(f"Results (Mark:{tblresults_marks}) | {self.tblResults.font().pointSize()}pt")

    def update_lineview_font_label(self, size: int):
        """폰트 변경 시 라벨 업데이트"""
        self.update_bookmark_labels()

    def update_tbl_font_label(self, size: int):
        """폰트 변경 시 라벨 업데이트"""
        self.update_bookmark_labels()
