"""Qt の :class:`PomodoroController` のテスト。

``QApplication`` が必要(pytest-qt の ``qapp`` フィクスチャが提供する)。
QTimer は使わず、プライベートなタイムアウトハンドラを直接呼ぶことで、実時間の
経過を待たずに高速かつ決定的にテストする。
"""

from __future__ import annotations

import pytest

from pomodoro.config import PomodoroConfig
from pomodoro.controller import PomodoroController
from pomodoro.model import Phase

pytest_plugins = ("pytestqt",)


class FakeNotifier:
    """コントローラがユーザーへの通知を要求した回数を記録する。"""

    def __init__(self) -> None:
        self.count = 0

    def notify(self) -> None:
        self.count += 1


@pytest.fixture
def notifier() -> FakeNotifier:
    return FakeNotifier()


@pytest.fixture
def controller(qapp: object, notifier: FakeNotifier) -> PomodoroController:
    del qapp  # QApplication が存在することを保証する
    return PomodoroController(PomodoroConfig(work_seconds=2, break_seconds=1), notifier)


def _advance(controller: PomodoroController, seconds: int) -> None:
    # QTimer を待たず、コントローラを決定的に駆動する。
    for _ in range(seconds):
        controller._on_timeout()


def test_toggle_starts_and_stops_the_qtimer(controller: PomodoroController) -> None:
    controller.toggle()
    assert controller._timer.isActive() is True
    controller.toggle()
    assert controller._timer.isActive() is False


def test_state_changed_is_emitted_on_tick(controller: PomodoroController, qtbot: object) -> None:
    controller.toggle()
    received: list[tuple[int, float, Phase, bool]] = []
    controller.state_changed.connect(lambda *args: received.append(args))
    _advance(controller, 1)
    assert received[-1][0] == 1  # 残り秒数


def test_phase_completion_notifies_once(
    controller: PomodoroController, notifier: FakeNotifier
) -> None:
    completed: list[Phase] = []
    controller.phase_completed.connect(completed.append)
    controller.toggle()
    _advance(controller, 2)  # work フェーズを終わらせる
    assert completed == [Phase.WORK]
    assert notifier.count == 1
    assert controller.model.phase is Phase.BREAK


def test_reset_stops_timer_and_restores_work(controller: PomodoroController) -> None:
    controller.toggle()
    _advance(controller, 3)  # break フェーズまで進める
    controller.reset()
    assert controller._timer.isActive() is False
    assert controller.model.phase is Phase.WORK
    assert controller.model.remaining == 2
