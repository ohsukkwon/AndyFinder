# -*- coding: utf-8 -*-
from PySide6 import QtGui, QtWidgets
from PySide6.QtCore import Qt


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
