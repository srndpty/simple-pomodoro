""":mod:`pomodoro.config` のテスト。"""

from __future__ import annotations

import pytest

from pomodoro.config import PomodoroConfig


def test_defaults_are_25_and_5_minutes() -> None:
    config = PomodoroConfig()
    assert config.work_seconds == 25 * 60
    assert config.break_seconds == 5 * 60


def test_from_minutes_rounds_to_seconds() -> None:
    config = PomodoroConfig.from_minutes(0.5, 1.0)
    assert config.work_seconds == 30
    assert config.break_seconds == 60


@pytest.mark.parametrize(
    ("work", "rest"),
    [(0, 60), (-1, 60), (60, 0), (60, -5)],
)
def test_non_positive_durations_are_rejected(work: int, rest: int) -> None:
    with pytest.raises(ValueError):
        PomodoroConfig(work_seconds=work, break_seconds=rest)


def test_config_is_frozen() -> None:
    config = PomodoroConfig()
    with pytest.raises(AttributeError):
        config.work_seconds = 10  # type: ignore[misc]
