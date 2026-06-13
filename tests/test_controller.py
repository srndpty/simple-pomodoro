"""Qt の :class:`PomodoroController` のテスト。

``QApplication`` が必要(pytest-qt の ``qapp`` フィクスチャが提供する)。
クロックを差し替え可能な :class:`FakeClock` に注入することで、実時間の経過を
待たずに高速かつ決定的にテストできる。
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


class FakeClock:
    """テストが任意に時刻を進められる、単調増加クロックの代用。"""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def notifier() -> FakeNotifier:
    return FakeNotifier()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def controller(qapp: object, notifier: FakeNotifier, clock: FakeClock) -> PomodoroController:
    del qapp  # QApplication が存在することを保証する
    return PomodoroController(
        PomodoroConfig(work_seconds=2, break_seconds=1), notifier, clock=clock
    )


def _advance(controller: PomodoroController, clock: FakeClock, seconds: int) -> None:
    # クロックを 1 秒ずつ進めながら、QTimer 相当のポーリングを発火させる。
    for _ in range(seconds):
        clock.now += 1.0
        controller._on_timeout()


def test_toggle_starts_and_stops_the_qtimer(controller: PomodoroController) -> None:
    controller.toggle()
    assert controller._timer.isActive() is True
    controller.toggle()
    assert controller._timer.isActive() is False


def test_state_changed_is_emitted_on_tick(controller: PomodoroController, clock: FakeClock) -> None:
    controller.toggle()
    received: list[tuple[int, float, Phase, bool]] = []
    controller.state_changed.connect(lambda *args: received.append(args))
    _advance(controller, clock, 1)
    assert received[-1][0] == 1  # 残り秒数


def test_phase_completion_notifies_once(
    controller: PomodoroController, clock: FakeClock, notifier: FakeNotifier
) -> None:
    completed: list[Phase] = []
    controller.phase_completed.connect(completed.append)
    controller.toggle()
    _advance(controller, clock, 2)  # work フェーズを終わらせる
    assert completed == [Phase.WORK]
    assert notifier.count == 1
    assert controller.model.phase is Phase.BREAK


def test_large_time_jump_notifies_once(
    controller: PomodoroController, clock: FakeClock, notifier: FakeNotifier
) -> None:
    # スリープ復帰などで一度に大きく時間が飛んでも、通知音は 1 回だけ。
    completed: list[Phase] = []
    controller.phase_completed.connect(completed.append)
    controller.toggle()
    clock.now += 10  # work(2)+break(1) の 3 秒周期を何度もまたぐ
    controller._on_timeout()
    assert notifier.count == 1
    assert len(completed) >= 2


def test_reset_stops_timer_and_restores_work(
    controller: PomodoroController, clock: FakeClock
) -> None:
    controller.toggle()
    _advance(controller, clock, 3)  # break フェーズまで進める
    controller.reset()
    assert controller._timer.isActive() is False
    assert controller.model.phase is Phase.WORK
    assert controller.model.remaining == 2
