# -*- coding: utf-8 -*-
import re
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt


class LineViewSearchDialog(QtWidgets.QDialog):
    """lineView 내부 검색 다이얼로그 (Modeless + 전체검색 기능)"""

    def __init__(self, editor, parent=None, viewer_name=""):
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
        elif event.key() == Qt.Key_F5:
            self.on_refresh_search()
            event.accept()
            return
        elif event.key() == Qt.Key_Escape:
            self.close()
            event.accept()
            return
        super().keyPressEvent(event)
