# -*- coding: utf-8 -*-
import os
from PySide6 import QtWidgets


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
