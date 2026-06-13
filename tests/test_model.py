"""純粋な :class:`PomodoroModel` 状態機械のテスト。"""

from __future__ import annotations

import pytest

from pomodoro.config import PomodoroConfig
from pomodoro.model import Phase, PomodoroModel


def _run_seconds(model: PomodoroModel, seconds: int) -> list[Phase]:
    """``seconds`` 回ティックし、完了したフェーズを集めて返す。"""
    completed: list[Phase] = []
    for _ in range(seconds):
        result = model.tick()
        if result is not None:
            completed.append(result)
    return completed


@pytest.fixture
def model() -> PomodoroModel:
    # 短い時間にしておくと、テストが速く挙動も追いやすい。
    return PomodoroModel(PomodoroConfig(work_seconds=3, break_seconds=2))


def test_starts_paused_in_work_phase(model: PomodoroModel) -> None:
    assert model.phase is Phase.WORK
    assert model.remaining == 3
    assert model.running is False
    assert model.completed_work_sessions == 0


def test_tick_does_nothing_while_paused(model: PomodoroModel) -> None:
    assert model.tick() is None
    assert model.remaining == 3


def test_tick_counts_down_while_running(model: PomodoroModel) -> None:
    model.start()
    assert model.tick() is None
    assert model.remaining == 2


def test_work_completes_then_switches_to_break(model: PomodoroModel) -> None:
    model.start()
    completed = _run_seconds(model, 3)
    assert completed == [Phase.WORK]
    assert model.phase is Phase.BREAK
    assert model.remaining == 2
    assert model.completed_work_sessions == 1


def test_full_cycle_loops_back_to_work(model: PomodoroModel) -> None:
    model.start()
    completed = _run_seconds(model, 3 + 2)
    assert completed == [Phase.WORK, Phase.BREAK]
    assert model.phase is Phase.WORK
    assert model.remaining == 3
    assert model.completed_work_sessions == 1


def test_multiple_cycles_accumulate_sessions(model: PomodoroModel) -> None:
    model.start()
    _run_seconds(model, (3 + 2) * 2 + 3)  # 2 サイクル分 + さらにもう 1 回の work フェーズ
    assert model.completed_work_sessions == 3


def test_toggle_flips_running(model: PomodoroModel) -> None:
    assert model.toggle() is True
    assert model.running is True
    assert model.toggle() is False
    assert model.running is False


def test_reset_returns_to_initial_state(model: PomodoroModel) -> None:
    model.start()
    _run_seconds(model, 4)  # break フェーズまで進める
    model.reset()
    assert model.phase is Phase.WORK
    assert model.remaining == 3
    assert model.running is False
    assert model.completed_work_sessions == 0


def test_advance_does_nothing_while_paused(model: PomodoroModel) -> None:
    assert model.advance(100) == []
    assert model.remaining == 3


def test_advance_ignores_non_positive(model: PomodoroModel) -> None:
    model.start()
    assert model.advance(0) == []
    assert model.remaining == 3


def test_advance_crosses_multiple_phases_in_one_step(model: PomodoroModel) -> None:
    model.start()
    completed = model.advance(3 + 2 + 1)  # フルサイクル + work へ 1 秒入る
    assert completed == [Phase.WORK, Phase.BREAK]
    assert model.phase is Phase.WORK
    assert model.remaining == 2
    assert model.completed_work_sessions == 1


def test_skip_to_remaining_then_tick_triggers_transition(model: PomodoroModel) -> None:
    model.start()
    model.skip_to_remaining(1)
    assert model.remaining == 1
    assert model.tick() is Phase.WORK
    assert model.phase is Phase.BREAK


def test_skip_to_remaining_is_capped_at_phase_duration(model: PomodoroModel) -> None:
    model.skip_to_remaining(999)
    assert model.remaining == model.phase_duration


def test_skip_to_remaining_rejects_non_positive(model: PomodoroModel) -> None:
    with pytest.raises(ValueError):
        model.skip_to_remaining(0)


def test_progress_reflects_elapsed_fraction(model: PomodoroModel) -> None:
    model.start()
    assert model.progress == pytest.approx(0.0)
    model.tick()
    assert model.progress == pytest.approx(1 / 3)


def test_phase_label() -> None:
    assert Phase.WORK.label == "Focus"
    assert Phase.BREAK.label == "Break"
