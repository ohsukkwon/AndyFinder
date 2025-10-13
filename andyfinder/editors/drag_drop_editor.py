# -*- coding: utf-8 -*-
"""
DragDropCodeEditor - Drag & Drop과 내부 검색을 지원하는 CodeEditor
"""
import re
from PySide6 import QtGui, QtWidgets
from PySide6.QtCore import Qt, Signal

from andyfinder.editors.code_editor import CodeEditor


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
            # viewer_name 결정: TabContent에서 lineView인지 lineView_clone인지 확인
            viewer_name = ""
            tab_content = self.parent()
            while tab_content and (not hasattr(tab_content, '__class__') or \
                  tab_content.__class__.__name__ != 'TabContent'):
                tab_content = tab_content.parent()

            if tab_content and hasattr(tab_content, 'lineView') and hasattr(tab_content, 'lineView_clone'):
                if self is tab_content.lineView:
                    viewer_name = "left"
                elif self is tab_content.lineView_clone:
                    viewer_name = "right"

            # 부모를 TabContent로 설정
            parent_widget = tab_content if tab_content else self.window()

            # LineViewSearchDialog는 AndyFinderTab.py에 정의되어 있으므로 동적으로 import
            # 순환 참조를 피하기 위해 여기서 import
            try:
                from AndyFinderTab import LineViewSearchDialog
                self.search_dialog = LineViewSearchDialog(self, parent_widget, viewer_name)
            except ImportError:
                # LineViewSearchDialog를 찾을 수 없는 경우 처리
                return

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
                tab_content = self.parent()
                while tab_content and (not hasattr(tab_content, '__class__') or \
                      tab_content.__class__.__name__ != 'TabContent'):
                    tab_content = tab_content.parent()
                if tab_content and hasattr(tab_content, 'append_text_to_lineedit'):
                    if event.key() == Qt.Key_1 and hasattr(tab_content, 'edt_query'):
                        tab_content.append_text_to_lineedit(tab_content.edt_query, selected_text)
                        tab_content.edt_query.setFocus()
                        event.accept()
                        return
                    elif event.key() == Qt.Key_2 and hasattr(tab_content, 'edt_result_search'):
                        tab_content.append_text_to_lineedit(tab_content.edt_result_search, selected_text)
                        tab_content.edt_result_search.setFocus()
                        event.accept()
                        return
                    elif event.key() == Qt.Key_3 and hasattr(tab_content, 'edt_color_keywords'):
                        tab_content.append_text_to_lineedit(tab_content.edt_color_keywords, selected_text)
                        tab_content.edt_color_keywords.setFocus()
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
        # 부모를 TabContent로 설정
        tab_content = self.parent()
        while tab_content and (not hasattr(tab_content, '__class__') or \
              tab_content.__class__.__name__ != 'TabContent'):
            tab_content = tab_content.parent()

        parent_widget = tab_content if tab_content else self.window()

        # GoToLineDialog는 AndyFinderTab.py에 정의되어 있으므로 동적으로 import
        try:
            from AndyFinderTab import GoToLineDialog
            dialog = GoToLineDialog(self, parent_widget)
            if dialog.exec() == QtWidgets.QDialog.Accepted and dialog.line_number > 0:
                self.gotoLine(dialog.line_number)
        except ImportError:
            # GoToLineDialog를 찾을 수 없는 경우 처리
            pass
