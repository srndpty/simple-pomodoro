"""純粋な :class:`PomodoroModel` と Qt UI をつなぐ橋渡し役。

コントローラは 1 秒間隔の :class:`QTimer` でポーリングし、単調増加クロック
(既定では :func:`time.monotonic`)から実際の経過秒数を求めてモデルを進める。
これにより、スリープ復帰やイベントループの遅延があっても実時間とズレにくい。
フェーズ遷移時に音を鳴らし、ビューが描画に使えるシグナルを発行する。ウィジェット
を一切保持しないため、UI は差し替え可能であり、独立してテストできる。
"""

from __future__ import annotations

import time
from collections.abc import Callable

from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal

from .config import PomodoroConfig
from .model import Phase, PomodoroModel
from .notifier import Notifier, SoundNotifier

_TICK_INTERVAL_MS = 1000


class PomodoroController(QObject):
    """タイマーでポモドーロモデルを駆動し、その状態をシグナルで公開する。"""

    #: 毎ティックおよび制御変更時に発行: (remaining_seconds, progress, phase, running)。
    state_changed = pyqtSignal(int, float, Phase, bool)
    #: フェーズ終了時に、ちょうど完了したフェーズを載せて発行する。
    phase_completed = pyqtSignal(Phase)

    def __init__(
        self,
        config: PomodoroConfig | None = None,
        notifier: Notifier | None = None,
        clock: Callable[[], float] = time.monotonic,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._model = PomodoroModel(config)
        self._notifier = notifier or SoundNotifier()
        # 単調増加クロック(秒)。テストでは差し替えて決定的に駆動できる。
        self._clock = clock
        self._run_started_at: float | None = None
        self._consumed_seconds = 0
        self._timer = QTimer(self)
        self._timer.setInterval(_TICK_INTERVAL_MS)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.timeout.connect(self._on_timeout)

    @property
    def model(self) -> PomodoroModel:
        return self._model

    # -- 制御 ----------------------------------------------------------------
    def toggle(self) -> None:
        """カウントダウンを開始または一時停止する。"""
        if self._model.toggle():
            self._begin_run()
        else:
            self._timer.stop()
        self._emit_state()

    def reset(self) -> None:
        """停止し、フォーカスセッションの開始時点へ戻す。"""
        self._timer.stop()
        self._run_started_at = None
        self._model.reset()
        self._emit_state()

    def skip_to_remaining(self, seconds: int) -> None:
        """現在のフェーズを残り ``seconds`` 秒までジャンプさせる(デバッグ/テスト用ヘルパー)。"""
        self._model.skip_to_remaining(seconds)
        self._emit_state()

    def emit_initial_state(self) -> None:
        """生成直後のビューが自身を描画できるよう、現在の状態を送出する。"""
        self._emit_state()

    # -- 内部処理 ------------------------------------------------------------
    def _begin_run(self) -> None:
        # この実行(開始〜一時停止)の起点を記録し、経過秒の累計をリセットする。
        self._run_started_at = self._clock()
        self._consumed_seconds = 0
        self._timer.start()

    def _on_timeout(self) -> None:
        if self._run_started_at is None:
            return
        # 実行開始からの実経過秒(整数)と、未適用の差分を求める。floor で
        # 数えるため丸め誤差が累積しない。
        total = int(self._clock() - self._run_started_at)
        delta = total - self._consumed_seconds
        if delta <= 0:
            return
        self._consumed_seconds = total

        completed = self._model.advance(delta)
        if completed:
            # 大きく時間が飛んでも(スリープ復帰など)通知音は 1 回だけ鳴らす。
            self._notifier.notify()
            for phase in completed:
                self.phase_completed.emit(phase)
        self._emit_state()

    def _emit_state(self) -> None:
        self.state_changed.emit(
            self._model.remaining,
            self._model.progress,
            self._model.phase,
            self._model.running,
        )
