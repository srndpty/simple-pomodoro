"""ポモドーロサイクルの純粋な(Qt 非依存の)状態機械。

このモジュールは PyQt やタイマー機構に一切依存しないように作ってあり、
タイマーロジック全体を単独でユニットテストできる。1 秒ごとに
:meth:`PomodoroModel.tick` を呼び出すのは UI 層の責務。
"""

from __future__ import annotations

from enum import Enum

from .config import PomodoroConfig


class Phase(Enum):
    """ポモドーロサイクルの 2 つのフェーズ。"""

    WORK = "work"
    BREAK = "break"

    @property
    def label(self) -> str:
        """表示用の人間向けラベル。"""
        return {Phase.WORK: "Focus", Phase.BREAK: "Break"}[self]


class PomodoroModel:
    """ポモドーロサイクルの現在のフェーズと残り時間を管理する。

    モデルは自身では進行しない。所有者が :attr:`running` が真の間、
    1 秒ごとに :meth:`tick` を呼び出して駆動する必要がある。
    """

    def __init__(self, config: PomodoroConfig | None = None) -> None:
        self._config = config or PomodoroConfig()
        self._phase = Phase.WORK
        self._remaining = self._config.work_seconds
        self._running = False
        self._completed_work_sessions = 0

    # -- 読み取り専用の状態 --------------------------------------------------
    @property
    def config(self) -> PomodoroConfig:
        return self._config

    @property
    def phase(self) -> Phase:
        return self._phase

    @property
    def remaining(self) -> int:
        """現在のフェーズの残り秒数(整数)。"""
        return self._remaining

    @property
    def running(self) -> bool:
        return self._running

    @property
    def completed_work_sessions(self) -> int:
        """これまでに完了したフォーカスセッションの数。"""
        return self._completed_work_sessions

    @property
    def phase_duration(self) -> int:
        """現在のフェーズの総時間(秒)。"""
        return self._duration_for(self._phase)

    @property
    def progress(self) -> float:
        """現在のフェーズの経過割合(``[0.0, 1.0]`` の範囲)。"""
        total = self.phase_duration
        return (total - self._remaining) / total

    # -- 制御 ----------------------------------------------------------------
    def start(self) -> None:
        self._running = True

    def pause(self) -> None:
        self._running = False

    def toggle(self) -> bool:
        """実行中と一時停止を切り替え、切り替え後の ``running`` 状態を返す。"""
        self._running = not self._running
        return self._running

    def reset(self) -> None:
        """フォーカスセッションの開始時点まで戻し、停止状態にする。"""
        self._phase = Phase.WORK
        self._remaining = self._config.work_seconds
        self._running = False
        self._completed_work_sessions = 0

    def skip_to_remaining(self, seconds: int) -> None:
        """現在のフェーズの残り時間を設定する(例: フェーズ終了時の遷移を
        待たずにテストするため)。フェーズ総時間で上限がかかり、実行状態は
        変更しない。
        """
        if seconds <= 0:
            raise ValueError("seconds must be positive")
        self._remaining = min(seconds, self.phase_duration)

    def tick(self) -> Phase | None:
        """時計を 1 秒進める。

        フェーズ遷移を引き起こして *ちょうど完了した* フェーズを返す。
        フェーズを完了せずに 1 秒経過した場合、または一時停止中の場合は
        ``None`` を返す。
        """
        if not self._running or self._remaining <= 0:
            return None

        self._remaining -= 1
        if self._remaining > 0:
            return None

        completed = self._phase
        self._advance()
        return completed

    # -- 内部処理 ------------------------------------------------------------
    def _duration_for(self, phase: Phase) -> int:
        return self._config.work_seconds if phase is Phase.WORK else self._config.break_seconds

    def _advance(self) -> None:
        """次のフェーズへ移行する。work -> break -> work を無限にループする。"""
        if self._phase is Phase.WORK:
            self._completed_work_sessions += 1
            self._phase = Phase.BREAK
        else:
            self._phase = Phase.WORK
        self._remaining = self._duration_for(self._phase)
