# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

AndyFinder는 PySide6 기반의 데스크톱 애플리케이션으로, 대용량 텍스트 파일(특히 Android dumpstate 로그)을 검색하고 분석하는 도구입니다. 정규식 지원, 멀티 탭, 북마크, 즐겨찾기, 색상 강조 등 고급 검색 기능을 제공합니다.

## 개발 환경

- **Python 버전**: 3.13.2
- **가상 환경**: `.venv/` (표준 Python venv)
- **주요 프레임워크**: PySide6 (Qt for Python)
- **핵심 의존성**: chardet (문자 인코딩 감지)

## 빌드 및 실행 명령어

### 실행 파일 빌드
```bash
pyinstaller --onefile --noconsole --icon=app_andy.ico --add-data=app.png;. AndyFinderTab.py
```
커스텀 빌드를 위한 `AndyFinderTab.spec` 파일이 제공됩니다.

### 소스에서 실행
```bash
python AndyFinderTab.py
```

## 아키텍처 개요

### 주요 애플리케이션 파일

- **AndyFinderTab.py**: 멀티 탭을 지원하는 현재 메인 애플리케이션 (~4600줄)
- **AndyFinder.py**: 이전 싱글 탭 버전 (~4200줄)
- **AndyFinderBig.py**: 대용량 파일 처리를 위한 변형 버전 (~3800줄)

애플리케이션은 여러 버전을 거쳐 발전했으며, `AndyFinderTab.py`가 최신 구현입니다.

### 핵심 컴포넌트

#### 1. **MainWindow** (3932줄+)
모든 UI 컴포넌트와 기능을 조율하는 메인 애플리케이션 윈도우. 관리 항목:
- 탭 관리 (다중 파일/검색 컨텍스트)
- 메뉴바 및 툴바
- 설정 영속성 (latest_config.json)
- 윈도우 상태 (크기/위치, 항상 위에 표시)

#### 2. **TabContent** (2333줄+)
각 탭은 완전한 검색 컨텍스트를 포함:
- CodeEditor 인스턴스 (메인 뷰 + 클론 뷰)
- 검색 결과 테이블 (DragTableView)
- 검색 설정 (쿼리, 모드, 컨텍스트 라인)
- 탭별 독립적인 북마크 및 마킹된 행

#### 3. **CodeEditor / DragDropCodeEditor** (1197줄+, 1588줄+)
커스텀 QPlainTextEdit:
- 북마크 지원하는 라인 번호 영역
- 검색 결과 구문 강조
- 라인 범위 복사를 위한 드래그 앤 드롭 지원
- 폰트 확대/축소 (Ctrl+마우스휠)
- 내부 검색 다이얼로그 (Ctrl+F)
- 북마크 이동 (F2/Shift+F2)

#### 4. **DragTableView** (1847줄+)
검색 결과용 커스텀 QTableView:
- 행 마킹/강조 (더블클릭 또는 F2/Shift+F2)
- 라인 번호에 대한 드래그 소스 (에디터로 범위 복사 가능)
- 커스텀 키보드 단축키 (Ctrl+Shift+C로 복사)

#### 5. **SearchWorker** (스레드)
진행 상황 보고 기능이 있는 정규식/일반 텍스트 검색 작업을 위한 백그라운드 스레드.

### 설정 및 데이터

#### 설정 파일 (`config/`)
- **latest_config.json**: 종료 시 자동 저장, 시작 시 로드
  - 탭별 저장 항목: query, search_mode, case_sensitive, result_search, color_keywords, context lines, fonts, marked_rows
  - 윈도우 크기/위치 및 상태
  - 항상 위에 표시 설정

#### 즐겨찾기 (`fav/`)
- **edit_query.json**: 즐겨찾기 검색 쿼리 (폴더 구조 포함)
- **edt_result_search.json**: 즐겨찾기 결과 필터
- **edt_color_keywords.json**: 즐겨찾기 색상 강조 키워드

즐겨찾기는 계층적 폴더 구조를 지원합니다 (type: "folder" vs "item").

### 주요 기능 아키텍처

#### 검색 시스템
- **모드**: 일반 텍스트 또는 정규식
- **대소문자 구분**: 일반 텍스트에서 선택 가능
- **컨텍스트 라인**: 매칭 전후 라인 수 설정 가능
- **결과 필터링**: 결과 내 2차 검색
- **스레딩**: 진행률 표시 및 취소 지원이 있는 비동기 검색

#### 북마크 시스템
- 탭별 북마크는 라인 번호 set으로 저장
- 토글: 라인 번호 영역 더블클릭
- 이동: F2 (다음), Shift+F2 (이전)
- 라인 번호 영역에 시각적 표시

#### 즐겨찾기 시스템
- LineEdit 위젯에서 롱클릭(500ms)하면 즐겨찾기 팝업 표시
- 드롭박스에서 F5를 누르면 선택된 즐겨찾기 값을 쿼리 필드에 로딩
- 계층적 폴더 구조 지원
- 마우스 오버 시 툴팁으로 전체 값 표시

#### 드래그 앤 드롭 라인 범위 복사
- DragTableView의 라인 번호 컬럼에서 드래그
- CodeEditor의 라인 번호 영역에 드롭
- 소스에서 타겟 위치로 라인 범위를 자동 복사

#### 멀티 윈도우 뷰
- 각 탭은 메인 에디터 + 클론 에디터 보유
- 내용 동기화, 커서 위치는 독립적
- 대용량 파일의 다른 부분을 볼 때 유용

### 버전 히스토리
`MyVersionHistory` 클래스(19줄+)에서 버전 추적. 현재 버전: `ver_1_251004_1930`

주요 버전 마일스톤:
- v1.251001_0140: 초기 기능 세트 (북마크, 즐겨찾기, 설정 저장)
- v1.251001_1600: 빠른 즐겨찾기 접근을 위한 드롭박스/콤보박스
- v1.251003_2000: LineViewSearchDialog의 전체 검색
- v1.251004_1930: 멀티 탭 지원, 대용량 파일 처리 개선

### UI 단축키

#### 전역
- **F5**: 검색 실행 (edt_query에서) 또는 색상 키워드 적용
- **Ctrl+F**: 내부 검색 다이얼로그 열기
- **F3/F4**: 내부 검색 결과 이동 (다음/이전)
- **F2/Shift+F2**: 북마크 또는 마킹된 행 이동

#### CodeEditor 내부
- **Ctrl+마우스휠**: 폰트 확대/축소
- **라인 번호 더블클릭**: 북마크 토글
- **라인 번호 드래그**: 범위 복사 시작

#### 결과 테이블 내부
- **행 더블클릭**: 행 마킹 토글 (연한 녹색 강조)
- **Ctrl+Shift+C**: 선택된 내용 복사 (null 값 제외)

## 개발 시 유의사항

### 대용량 파일 처리
애플리케이션은 대용량 파일용으로 설계되었습니다 (dumpstate 로그는 10+ MB 가능). `MIN_BUF_LOAD_SIZE = 1MB`가 정의되어 있지만 실제 구현은 파일 버전에 따라 다릅니다.

### 문자 인코딩
파일 로딩 시 자동 인코딩 감지를 위해 `chardet` 라이브러리를 사용합니다.

### 스레딩
SearchWorker는 QThread에서 실행되어 검색 작업 중 UI가 블로킹되지 않습니다. 새로운 검색을 시작하기 전에 항상 stop_search()를 호출해야 합니다.

### 설정 영속성
`save_latest_config()`는 파일 저장 여부와 관계없이 `closeEvent`에서 호출됩니다. 각 탭의 상태는 독립적으로 보존됩니다.
