# -*- coding: utf-8 -*-
"""메인 윈도우 모듈"""
import sys
import os
import json
import subprocess
from datetime import datetime
from typing import Optional

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon

from andyfinder.version import gCurVerInfo
from andyfinder.constants import (
    g_pgm_name,
    g_win_size_w,
    g_win_size_h,
    g_icon_name
)
from andyfinder.widgets.tab_bar import CustomTabBar
from andyfinder.dialogs.config_dialogs import ConfigSaveDialog, ConfigLoadDialog


# TabContent는 아직 분리되지 않았으므로 임시로 TYPE_CHECKING 사용
# TODO: TabContent를 별도 모듈로 분리 후 실제 import로 변경
if False:  # TYPE_CHECKING과 유사하게 사용
    from AndyFinderTab import TabContent


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

        # F11 전체화면 토글용 상태 저장
        self._previous_window_state = Qt.WindowNoState
        self._previous_geometry = None

        self._create_menus()
        self._build_main_ui()

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
        tab = self.get_current_tab()
        if not tab:
            QtWidgets.QMessageBox.information(self, "안내", "활성 탭이 없습니다.")
            return

        if not tab.current_file_path:
            QtWidgets.QMessageBox.information(self, "안내", "로드된 파일이 없습니다.")
            return

        if not os.path.exists(tab.current_file_path):
            QtWidgets.QMessageBox.warning(self, "경고", "파일이 존재하지 않습니다.")
            return

        folder_path = os.path.dirname(os.path.abspath(tab.current_file_path))

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

    def _build_main_ui(self):
        """UI 구성"""
        # ===== 추가: Menu와 tab 사이에 1px 검은색 위젯 =====
        yellow_spacer = QtWidgets.QWidget()
        yellow_spacer.setFixedHeight(1)
        yellow_spacer.setStyleSheet("background-color: #000000;")

        # QTabWidget 생성
        self.tab_widget = QtWidgets.QTabWidget()
        self.tab_widget.setTabBar(CustomTabBar(self.tab_widget))
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.setMovable(False)

        # 초기 탭 생성 (3개)
        # NOTE: TabContent import는 실제 사용 시점에 필요
        # 현재는 AndyFinderTab.py에서 직접 import 필요
        from AndyFinderTab import TabContent
        for i in range(3):
            tab_content = TabContent(i + 1, self)
            self.tab_widget.addTab(tab_content, f"Tab#{i + 1}")

        # ===== 변경: 중앙 위젯을 컨테이너로 구성 =====
        central_widget = QtWidgets.QWidget()
        central_layout = QtWidgets.QVBoxLayout(central_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)

        central_layout.addWidget(yellow_spacer)
        central_layout.addWidget(self.tab_widget)

        self.setCentralWidget(central_widget)

    def get_current_tab(self) -> Optional['TabContent']:
        """현재 활성 탭 반환"""
        current = self.tab_widget.currentWidget()
        # TabContent 타입 체크는 런타임에 수행
        if current and hasattr(current, 'tab_number'):
            return current
        return None

    def mark_tab_modified(self, tab: 'TabContent'):
        """탭 제목에 * 표시"""
        index = self.tab_widget.indexOf(tab)
        if index >= 0:
            text = self.tab_widget.tabText(index)
            if not text.endswith('*'):
                self.tab_widget.setTabText(index, text + '*')

    def unmark_tab_modified(self, tab: 'TabContent'):
        """탭 제목에서 * 제거"""
        index = self.tab_widget.indexOf(tab)
        if index >= 0:
            text = self.tab_widget.tabText(index)
            if text.endswith('*'):
                self.tab_widget.setTabText(index, text[:-1])

    def update_tab_title(self, tab: 'TabContent'):
        """탭 제목 업데이트"""
        index = self.tab_widget.indexOf(tab)
        if index >= 0:
            base_title = f"Tab#{tab.tab_number}"
            if tab.is_modified:
                base_title += "*"
            self.tab_widget.setTabText(index, base_title)

    # 메뉴 액션들은 active tab에 위임
    def open_file(self):
        tab = self.get_current_tab()
        if tab:
            tab.open_file()

    def save_file(self):
        tab = self.get_current_tab()
        if tab:
            tab.save_file()

    def save_config(self):
        """현재 활성 탭의 설정 저장"""
        tab = self.get_current_tab()
        if not tab:
            QtWidgets.QMessageBox.information(self, "안내", "활성 탭이 없습니다.")
            return

        dialog = ConfigSaveDialog(self)
        if dialog.exec() != QtWidgets.QDialog.Accepted:
            return

        config_name = dialog.config_name
        config = tab.get_config()

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
            self.statusBar().showMessage(f"설정 저장 완료: {filename}", 5000)
            QtWidgets.QMessageBox.information(self, "완료", f"설정이 저장되었습니다.\n{filename}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"설정 저장 실패: {e}")

    def load_config(self):
        """설정을 현재 활성 탭에 불러오기"""
        tab = self.get_current_tab()
        if not tab:
            QtWidgets.QMessageBox.information(self, "안내", "활성 탭이 없습니다.")
            return

        config_dir = "./config"
        dialog = ConfigLoadDialog(config_dir, self)
        if dialog.exec() != QtWidgets.QDialog.Accepted or not dialog.selected_file:
            return

        filepath = dialog.selected_file

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)

            tab.apply_config(config)

            self.statusBar().showMessage(f"설정 불러오기 완료: {os.path.basename(filepath)}", 5000)
            QtWidgets.QMessageBox.information(self, "완료", "설정을 불러왔습니다.")

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"설정 불러오기 실패: {e}")

    def all_data_clear(self):
        """현재 활성 탭의 데이터 초기화"""
        tab = self.get_current_tab()
        if not tab:
            QtWidgets.QMessageBox.information(self, "안내", "활성 탭이 없습니다.")
            return

        try:
            # 검색 중이면 중지
            tab.stop_search()
            # 현재 파일/결과/상태 초기화
            tab.close_current_file()
            # 파일 라벨/상태/프로그레스/테이블 선택 초기화
            tab.lbl_file.setText("파일 없음")
            tab.lbl_status.setText("")
            tab.prog.setValue(0)
            tab.tblResults.clearSelection()

            self.statusBar().showMessage("All data cleared", 3000)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "오류", f"초기화 중 오류: {e}")

    # 최신 설정 (모든 탭의 설정 저장)
    def latest_config_file_path(self) -> str:
        return os.path.join(".", "config", "latest_config.json")

    def build_latest_config(self) -> dict:
        """모든 탭의 설정 + 윈도우 상태 저장"""
        tabs_config = []
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if tab and hasattr(tab, 'get_config'):
                tabs_config.append(tab.get_config())

        cfg = {
            'tabs': tabs_config,
            'current_tab': self.tab_widget.currentIndex(),
            'always_on_top': self.always_on_top_action.isChecked(),
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
        """저장된 설정 적용 (모든 탭 + 윈도우 상태)"""
        try:
            # 탭별 설정 적용
            tabs_config = cfg.get('tabs', [])
            for i, tab_cfg in enumerate(tabs_config):
                if i < self.tab_widget.count():
                    tab = self.tab_widget.widget(i)
                    if tab and hasattr(tab, 'apply_config'):
                        tab.apply_config(tab_cfg)

            # 현재 탭 설정
            current_tab = cfg.get('current_tab', 0)
            if 0 <= current_tab < self.tab_widget.count():
                self.tab_widget.setCurrentIndex(current_tab)

            # 항상 위
            if 'always_on_top' in cfg:
                self.always_on_top_action.setChecked(bool(cfg.get('always_on_top', False)))

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
            self.statusBar().showMessage("최신 설정을 불러왔습니다.", 3000)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "경고", f"최신 설정 불러오기 실패: {e}")

    def keyPressEvent(self, event):
        # F11: 전체화면 토글
        if event.key() == Qt.Key_F11:
            self.toggle_fullscreen()
            event.accept()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event):
        # 모든 탭의 수정 여부 확인
        modified_tabs = []
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if tab and hasattr(tab, 'is_modified') and tab.is_modified:
                modified_tabs.append(i + 1)

        if modified_tabs:
            tab_names = ", ".join([f"Tab#{i}" for i in modified_tabs])
            reply = QtWidgets.QMessageBox.question(
                self, '확인',
                f'다음 탭에 변경사항이 있습니다: {tab_names}\n저장하지 않고 종료하시겠습니까?',
                QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel,
                QtWidgets.QMessageBox.Save
            )

            if reply == QtWidgets.QMessageBox.Save:
                # 모든 수정된 탭 저장
                for i in modified_tabs:
                    tab = self.tab_widget.widget(i - 1)
                    if tab and hasattr(tab, 'save_file'):
                        tab.save_file()
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

            self.statusBar().showMessage("전체화면 종료", 2000)
        else:
            # 현재 상태 저장
            self._previous_geometry = self.geometry()
            self._previous_window_state = Qt.WindowMaximized if self.isMaximized() else Qt.WindowNoState

            # 전체화면으로 전환
            self.showFullScreen()
            self.statusBar().showMessage("전체화면 모드 (F11: 종료)", 2000)
