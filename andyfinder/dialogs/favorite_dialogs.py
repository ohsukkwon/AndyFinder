# -*- coding: utf-8 -*-
import os
import json
from typing import List, Optional
from PySide6 import QtGui, QtWidgets
from PySide6.QtCore import Qt, Signal


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


class FavoritesTree(QtWidgets.QTreeWidget):
    """즐겨찾기 트리 위젯 (드래그 앤 드롭 내부 이동 전용)"""

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
