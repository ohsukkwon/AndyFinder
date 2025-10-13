# -*- coding: utf-8 -*-
"""AndyFinder 애플리케이션 패키지"""

from andyfinder.version import gCurVerInfo, gCurVerDesc, MyVersionHistory
from andyfinder.constants import *
from andyfinder.models import SearchResult
from andyfinder.main_window import MainWindow
from andyfinder.tab_content import TabContent
from andyfinder.theme import apply_light_theme

__version__ = gCurVerInfo
__all__ = [
    'MainWindow',
    'TabContent',
    'SearchResult',
    'apply_light_theme',
    'gCurVerInfo',
    'gCurVerDesc',
]
