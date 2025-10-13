# -*- coding: utf-8 -*-
"""데이터 모델"""

from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class SearchResult:
    """검색 결과 데이터 클래스"""
    line: int
    snippet: str
    matches: List[Tuple[int, int]]  # (start, end) in snippet string
