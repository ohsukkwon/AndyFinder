# -*- coding: utf-8 -*-
from PySide6 import QtWidgets, QtGui
from PySide6.QtCore import Qt


class CustomTabBar(QtWidgets.QTabBar):
    """탭별 색상을 지원하는 커스텀 TabBar"""

    def __init__(self, parent=None):
        super().__init__(parent)
        # 탭별 색상 정의 (focus 없을 때 / focus 있을 때)
        self.tab_colors = [
            (QtGui.QColor("#BCC2C2"), QtGui.QColor("#C11B17")),         # Tab#1: 연한 빨강 / 진한 빨강
            (QtGui.QColor("#BCC2C2"), QtGui.QColor("#8D4004")),         # Tab#2: 연한 노랑 / 진한 노랑
            (QtGui.QColor("#BCC2C2"), QtGui.QColor("#32612D")),         # Tab#3: 연한 녹색 / 진한 녹색
        ]

    def tabSizeHint(self, index):
        """각 탭의 크기 힌트 - active tab은 200px, inactive tab은 70px"""
        size = super().tabSizeHint(index)

        # 현재 active tab인지 확인
        if index == self.currentIndex():
            # active tab (focus): 200px
            size.setWidth(200)
        else:
            # inactive tab (no focus): 70px
            size.setWidth(70)

        return size

    def paintEvent(self, event):
        """탭 그리기"""
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        option = QtWidgets.QStyleOptionTab()

        for i in range(self.count()):
            self.initStyleOption(option, i)

            # 탭 번호에 따른 색상 선택
            if i < len(self.tab_colors):
                bg_color, active_color = self.tab_colors[i]
            else:
                bg_color = QtGui.QColor(220, 220, 220)
                active_color = QtGui.QColor(100, 100, 100)

            # 현재 탭(focus)인지 확인
            is_current = (i == self.currentIndex())

            tab_rect = self.tabRect(i)

            # 배경 그리기
            if is_current:
                painter.fillRect(tab_rect, active_color)
            else:
                painter.fillRect(tab_rect, bg_color)

            # 외곽선 그리기
            painter.setBrush(Qt.NoBrush)
            if is_current:
                # active tab: 2px solid black
                pen = QtGui.QPen(QtGui.QColor(0, 0, 0), 2, Qt.SolidLine)
                painter.setPen(pen)
                # 외곽선이 잘리지 않도록 약간 안쪽으로 조정
                painter.drawRect(tab_rect.adjusted(1, 1, -2, -2))
            else:
                # inactive tab: 얇은 회색 외곽선 (탭 구분을 명확하게)
                pen = QtGui.QPen(QtGui.QColor(128, 128, 128), 1, Qt.SolidLine)
                painter.setPen(pen)
                painter.drawRect(tab_rect.adjusted(0, 0, -1, -1))

            # 텍스트 그리기
            font = painter.font()
            if is_current:
                font.setBold(True)
                text_color = QtGui.QColor(255, 255, 255)
            else:
                font.setBold(False)
                text_color = QtGui.QColor(0, 0, 0)

            painter.setFont(font)
            painter.setPen(text_color)
            painter.drawText(tab_rect, Qt.AlignCenter, self.tabText(i))
