# -*- coding: utf-8 -*-
import os
import time
import chardet
from PySide6 import QtCore
from PySide6.QtCore import QObject, Signal

# 최소 버퍼 로드 크기
MIN_BUF_LOAD_SIZE = 1 * 1024 * 1024


class FileLoader(QObject):
    """파일을 백그라운드에서 로드하는 워커 클래스"""
    progress = Signal(int)
    finished = Signal(str, str, float)  # content, encoding, duration
    failed = Signal(str)

    def __init__(self, path: str):
        super().__init__()
        self.path = path
        self._stop = False

    def stop(self):
        """작업 중지"""
        self._stop = True

    def detect_encoding(self, sample: bytes) -> str:
        """파일의 인코딩을 감지"""
        try:
            guess = chardet.detect(sample)
            enc = guess.get('encoding') or 'utf-8'
            if enc and enc.lower() in ('ascii',):
                return 'utf-8'
            return enc or 'utf-8'
        except Exception:
            return 'utf-8'

    @QtCore.Slot()
    def run(self):
        """파일 로드 실행"""
        start_time = time.time()
        try:
            size = os.path.getsize(self.path)
            sample_size = min(MIN_BUF_LOAD_SIZE, size)
            with open(self.path, 'rb') as f:
                sample = f.read(sample_size)
            encoding = self.detect_encoding(sample)
            self.progress.emit(10)

            with open(self.path, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()

            self.progress.emit(100)
            duration = time.time() - start_time
            self.finished.emit(content, encoding, duration)
        except Exception as e:
            self.failed.emit(str(e))
