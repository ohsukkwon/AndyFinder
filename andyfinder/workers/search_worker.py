# -*- coding: utf-8 -*-
import re
import time
from typing import List, Tuple
from dataclasses import dataclass
from PySide6 import QtCore
from PySide6.QtCore import QObject, Signal


@dataclass
class SearchResult:
    """검색 결과 데이터 클래스"""
    line: int
    snippet: str
    matches: List[Tuple[int, int]]  # (start, end) in snippet string


class SearchWorker(QObject):
    """검색을 백그라운드에서 수행하는 워커 클래스"""
    progress = Signal(int)
    finished = Signal(list, float)  # results, duration
    failed = Signal(str)
    message = Signal(str)

    def __init__(self, content: str, query: str, mode: str, case_sensitive: bool):
        super().__init__()
        self.content = content
        self.lines = content.split('\n')
        self.query = query
        self.mode = mode
        self.case_sensitive = case_sensitive
        self._stop = False

    def stop(self):
        """작업 중지"""
        self._stop = True

    def build_matcher(self):
        """검색 모드에 따라 매칭 함수를 생성"""
        text = self.query.strip()
        if not text:
            return None

        flags = 0 if self.case_sensitive else re.IGNORECASE

        if self.mode == 'regex':
            try:
                regex = re.compile(text, flags)
            except re.error as e:
                raise ValueError(f'정규식 오류: {e}')

            def fn_regex(s, rx=regex):
                return [(m.start(), m.end()) for m in rx.finditer(s)]

            return fn_regex
        else:
            needle = text if self.case_sensitive else text.lower()

            def fn_plain(s, n=needle, cs=self.case_sensitive):
                hay = s if cs else s.lower()
                spans = []
                start = 0
                ln = len(n)
                if ln == 0:
                    return spans
                while True:
                    pos = hay.find(n, start)
                    if pos == -1:
                        break
                    spans.append((pos, pos + ln))
                    start = pos + ln if ln > 0 else pos + 1
                return spans

            return fn_plain

    @QtCore.Slot()
    def run(self):
        """검색 실행"""
        start_time = time.time()
        try:
            matcher = self.build_matcher()
            if not matcher:
                duration = time.time() - start_time
                self.finished.emit([], duration)
                return

            results: List[SearchResult] = []
            total = len(self.lines)

            for idx, line_idx in enumerate(range(0, total)):
                if self._stop:
                    break

                s = self.lines[line_idx]
                spans = matcher(s)
                if spans:
                    results.append(SearchResult(line=line_idx, snippet=s, matches=spans))

                if idx % 1000 == 0:
                    self.progress.emit(int((idx / max(1, total)) * 100))

            self.progress.emit(100)
            duration = time.time() - start_time
            self.finished.emit(results, duration)
        except Exception as e:
            self.failed.emit(str(e))
