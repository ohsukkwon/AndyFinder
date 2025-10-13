# -*- coding: utf-8 -*-
"""
AndyFinder - 대용량 텍스트 파일 검색 및 분석 도구

PySide6 기반의 데스크톱 애플리케이션으로,
정규식 검색, 북마크, 즐겨찾기 등 다양한 기능을 제공합니다.
"""

import sys
from PySide6 import QtWidgets
from andyfinder import MainWindow, apply_light_theme


def main():
    """메인 애플리케이션 진입점"""
    app = QtWidgets.QApplication(sys.argv)
    apply_light_theme(app)

    win = MainWindow()
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
