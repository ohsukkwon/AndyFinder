# -*- coding: utf-8 -*-
"""버전 관리 모듈"""


class MyVersionHistory:
    VER_INFO__ver_1_251001_0140 = "ver_1_251001_0140"
    VER_DESC__ver_1_251001_0140 = '''
1. Highlight Color 유지 기능 추가 - lineView의 mouse event에도 Color 하이라이트 유지.
2. 프로그램 Title에 버전 정보 추가.
3. 북마크 기능 추가 - Line Number 더블클릭으로 북마크 토글, F2/Shift+F2로 이동.
4. 설정 저장/불러오기 기능 추가.
5. 즐겨찾기 기능 추가 (edt_query, edt_result_search, edt_color_keywords).
6. F5 단축키 추가 (edt_query: 검색, edt_color_keywords: 설정).
7. lineView 내부 검색 기능 추가 (Ctrl+F, F3/F4로 이동).
8. Long Click시 바로 입력 UI 제공 후 즐겨찾기 목록 표시.
9. lineView 검색 다이얼로그 Modeless 변경.
10. Ctrl+F 실행시 선택된 텍스트를 검색어로 자동 입력.
11. tblResults row 더블클릭으로 Light Green 마킹 토글 기능 추가.
12. tblResults에서 F2/Shift+F2로 마킹된 row 이동 기능 추가.
13. tblResults LineNumber를 lineView LineNumber로 Drag&Drop하여 범위 복사 기능 추가.
14. 즐겨찾기 Category(폴더 구조) 지원: 세 가지 즐겨찾기(기본 검색어/결과내 검색/Color 키워드)에 폴더 생성/이동/선택 기능 추가.
'''
    VER_INFO__ver_1_251005_0000 = "ver_1_251005_0000"
    VER_DESC__ver_1_251005_0000 = '''
- Multiple Tab UI 지원 (최대 3개 탭)
- 각 탭별 독립적인 설정 및 상태 관리
- 탭별 색상 구분 (Tab#1: 빨강, Tab#2: 주황, Tab#3: 노랑)
- Focus 상태에 따른 탭 색상 변경
'''

    VER_INFO__ver_1_251006_1210 = "ver_1_251006_1210"
    VER_DESC__ver_1_251006_1210 = '''
- DragTableView에 Ctrl+Shift+C 단축키 처리 추가
'''

    VER_INFO__ver_1_251006_1250 = "ver_1_251006_1250"
    VER_DESC__ver_1_251006_1250 = '''
- DragTableView에 Ctrl+Shift+C 단축키 처리시 nul 처리 수정(nul은 제거)
'''

    VER_INFO__ver_1_251007_0100 = "ver_1_251007_0100"
    VER_DESC__ver_1_251007_0100 = '''
- Bookmark label 추가
'''
    VER_INFO__ver_1_251008_1500 = "ver_1_251008_1500"
    VER_DESC__ver_1_251008_1500 = '''
- DragTableView의 header 의 width 수정
'''
    VER_INFO__ver_1_251013_2250 = "ver_1_251013_2250"
    VER_DESC__ver_1_251013_2250 = '''
- 투명도 슬라이더 아래에 파일 경로 표시용 file_path_lbl QLabel 추가
- Ctrl+F로 검색 다이얼로그 열 때 현재 탭의 파일 경로를 자동으로 표시
'''

    VER_INFO__ver_1_251014_1555 = "ver_1_251014_1555"
    VER_DESC__ver_1_251014_1555 = '''
- 사용자가 Ctrl+클릭 또는 Shift+클릭으로 여러 행을 선택한 후 Ctrl+C를 누르면 
선택된 모든 행이 탭으로 구분된 형식(LineNumber + 내용)으로 클립보드에 복사
'''

    def __init__(self):
        pass

    def get_version_info(self):
        return self.VER_INFO__ver_1_251014_1555, self.VER_DESC__ver_1_251014_1555


# 전역 버전 인스턴스
g_my_version_info = MyVersionHistory()
gCurVerInfo, gCurVerDesc = g_my_version_info.get_version_info()
