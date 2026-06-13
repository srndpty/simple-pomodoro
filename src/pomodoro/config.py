"""ポモドーロタイマーの設定。

テストや将来の拡張(設定ファイルや環境変数からの読み込みなど)を容易にするため、
Qt 非依存かつイミュータブルに保っている。
"""

from __future__ import annotations

from dataclasses import dataclass

_SECONDS_PER_MINUTE = 60


@dataclass(frozen=True, slots=True)
class PomodoroConfig:
    """タイマーを駆動する各時間(秒単位)。

    分単位で指定したい一般的なケースでは :meth:`from_minutes` を使う。
    """

    work_seconds: int = 25 * _SECONDS_PER_MINUTE
    break_seconds: int = 5 * _SECONDS_PER_MINUTE

    def __post_init__(self) -> None:
        if self.work_seconds <= 0:
            raise ValueError("work_seconds must be positive")
        if self.break_seconds <= 0:
            raise ValueError("break_seconds must be positive")

    @classmethod
    def from_minutes(cls, work_minutes: float, break_minutes: float) -> PomodoroConfig:
        """分単位の指定から設定を生成する(秒に丸める)。"""
        return cls(
            work_seconds=round(work_minutes * _SECONDS_PER_MINUTE),
            break_seconds=round(break_minutes * _SECONDS_PER_MINUTE),
        )
