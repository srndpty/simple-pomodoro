""":mod:`pomodoro.formatting` のテスト。"""

from __future__ import annotations

import pytest

from pomodoro.formatting import format_mmss


@pytest.mark.parametrize(
    ("seconds", "expected"),
    [
        (0, "00:00"),
        (5, "00:05"),
        (60, "01:00"),
        (90, "01:30"),
        (25 * 60, "25:00"),
        (90 * 60, "90:00"),
    ],
)
def test_format_mmss(seconds: int, expected: str) -> None:
    assert format_mmss(seconds) == expected


def test_negative_seconds_rejected() -> None:
    with pytest.raises(ValueError):
        format_mmss(-1)
