"""アプリケーションのメインウィンドウ。"""

from __future__ import annotations

import os

from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..config import PomodoroConfig
from ..controller import PomodoroController
from ..model import Phase
from .circular_timer import CircularTimer

#: この環境変数が設定されていると、Ctrl+D でフェーズの残り数秒へジャンプし、
#: 待たずにフェーズ終了音と遷移を確認できる。
DEBUG_ENV_VAR = "POMODORO_DEBUG"
_DEBUG_SKIP_SECONDS = 3

_STYLESHEET = """
QMainWindow, QWidget { background-color: #1e1e1e; }
QPushButton {
    background-color: #2d2d2d;
    color: #f5f5f5;
    border: 1px solid #3a3a3a;
    border-radius: 6px;
    padding: 8px 0;
    font-size: 13px;
}
QPushButton:hover { background-color: #383838; }
QPushButton:pressed { background-color: #444444; }
"""


class MainWindow(QMainWindow):
    """円形タイマーと、開始/一時停止・リセットの操作を載せるウィンドウ。"""

    def __init__(self, config: PomodoroConfig | None = None) -> None:
        super().__init__()
        self._controller = PomodoroController(config, parent=self)

        self.setWindowTitle("Pomodoro")
        self.setFixedSize(280, 360)
        self.setStyleSheet(_STYLESHEET)

        self._timer_widget = CircularTimer()
        self._start_button = QPushButton("Start")
        self._reset_button = QPushButton("Reset")

        self._build_layout()
        self._wire_signals()
        if os.environ.get(DEBUG_ENV_VAR):
            self._install_debug_shortcut()
        self._controller.emit_initial_state()

    def _build_layout(self) -> None:
        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addWidget(self._start_button)
        buttons.addWidget(self._reset_button)

        root = QVBoxLayout()
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)
        root.addWidget(self._timer_widget, stretch=1)
        root.addLayout(buttons)

        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)

    def _wire_signals(self) -> None:
        self._start_button.clicked.connect(self._controller.toggle)
        self._reset_button.clicked.connect(self._controller.reset)
        self._controller.state_changed.connect(self._on_state_changed)

    def _on_state_changed(
        self, remaining: int, progress: float, phase: Phase, running: bool
    ) -> None:
        self._timer_widget.set_state(remaining, progress, phase)
        self._start_button.setText("Pause" if running else "Start")

    # -- デバッグ用ヘルパー ----------------------------------------------------
    def _install_debug_shortcut(self) -> None:
        shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        shortcut.activated.connect(self._debug_skip_to_end)

    def _debug_skip_to_end(self) -> None:
        # ジャンプ後にフェーズ終了音と遷移までカウントダウンが進むよう、
        # 時計が動いている状態にしておく。
        if not self._controller.model.running:
            self._controller.toggle()
        self._controller.skip_to_remaining(_DEBUG_SKIP_SECONDS)
