# -*- coding: utf-8 -*-
from typing import List, Tuple

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, QModelIndex


# ------------------------------ 데이터 구조 ------------------------------
from dataclasses import dataclass


@dataclass
class SearchResult:
    line: int
    snippet: str
    matches: List[Tuple[int, int]]  # (start, end) in snippet string


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
        """row 마킹 토글 - 변경 시 부모에 알림"""
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
