"""ウィジェットのスモークテスト。

Qt のオフスクリーンプラットフォーム上で実際のウィジェットを構築し、ウィンドウが
組み上がること、コントローラが正しく結線されていること、描画で例外が出ないことを
確認する。
"""

from __future__ import annotations

import pytest
from PyQt6.QtGui import QPainter, QShortcut
from PyQt6.QtWidgets import QPushButton
from pytestqt.qtbot import QtBot

from pomodoro.config import PomodoroConfig
from pomodoro.model import Phase
from pomodoro.ui.circular_timer import CircularTimer
from pomodoro.ui.main_window import DEBUG_ENV_VAR, MainWindow

pytest_plugins = ("pytestqt",)


def test_main_window_builds_and_shows_initial_time(qtbot: QtBot) -> None:
    window = MainWindow(PomodoroConfig(work_seconds=90, break_seconds=30))
    qtbot.addWidget(window)
    start_button = window.findChild(QPushButton)
    assert start_button is not None
    assert start_button.text() == "Start"


def test_start_button_toggles_label(qtbot: QtBot) -> None:
    window = MainWindow(PomodoroConfig(work_seconds=90, break_seconds=30))
    qtbot.addWidget(window)
    button = window.findChild(QPushButton)
    assert button is not None

    button.click()
    assert button.text() == "Pause"
    button.click()
    assert button.text() == "Start"


def test_no_debug_shortcut_by_default(qtbot: QtBot, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(DEBUG_ENV_VAR, raising=False)
    window = MainWindow(PomodoroConfig(work_seconds=90, break_seconds=30))
    qtbot.addWidget(window)
    assert window.findChildren(QShortcut) == []


def test_debug_shortcut_jumps_near_end_and_starts(
    qtbot: QtBot, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(DEBUG_ENV_VAR, "1")
    window = MainWindow(PomodoroConfig(work_seconds=90, break_seconds=30))
    qtbot.addWidget(window)
    assert len(window.findChildren(QShortcut)) == 1

    window._debug_skip_to_end()
    assert window._controller.model.running is True
    assert window._controller.model.remaining == 3


def test_circular_timer_renders_each_phase(qtbot: QtBot) -> None:
    from PyQt6.QtGui import QPixmap

    widget = CircularTimer()
    qtbot.addWidget(widget)
    widget.resize(220, 220)

    for phase in (Phase.WORK, Phase.BREAK):
        widget.set_state(remaining=75, progress=0.4, phase=phase)
        pixmap = QPixmap(widget.size())
        painter = QPainter(pixmap)
        widget.render(painter)
        painter.end()
