"""アプリケーションの起動処理: QApplication を構築してメインウィンドウを表示する。"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from .config import PomodoroConfig
from .ui.main_window import MainWindow


def run(argv: list[str] | None = None, config: PomodoroConfig | None = None) -> int:
    """Qt アプリケーションを生成し、ウィンドウを表示してイベントループを実行する。"""
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("simple-pomodoro")

    window = MainWindow(config)
    window.show()

    return app.exec()
