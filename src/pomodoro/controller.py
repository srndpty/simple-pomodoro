"""純粋な :class:`PomodoroModel` と Qt UI をつなぐ橋渡し役。

コントローラは 1 秒間隔の :class:`QTimer` を保持してモデルを進め、フェーズ
遷移時に音を鳴らし、ビューが描画に使えるシグナルを発行する。ウィジェットを
一切保持しないため、UI は差し替え可能であり、独立してテストできる。
"""

from __future__ import annotations

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

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
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._model = PomodoroModel(config)
        self._notifier = notifier or SoundNotifier()
        self._timer = QTimer(self)
        self._timer.setInterval(_TICK_INTERVAL_MS)
        self._timer.setTimerType(self._timer.timerType().PreciseTimer)
        self._timer.timeout.connect(self._on_timeout)

    @property
    def model(self) -> PomodoroModel:
        return self._model

    # -- 制御 ----------------------------------------------------------------
    def toggle(self) -> None:
        """カウントダウンを開始または一時停止する。"""
        if self._model.toggle():
            self._timer.start()
        else:
            self._timer.stop()
        self._emit_state()

    def reset(self) -> None:
        """停止し、フォーカスセッションの開始時点へ戻す。"""
        self._timer.stop()
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
    def _on_timeout(self) -> None:
        completed = self._model.tick()
        if completed is not None:
            self._notifier.notify()
            self.phase_completed.emit(completed)
        self._emit_state()

    def _emit_state(self) -> None:
        self.state_changed.emit(
            self._model.remaining,
            self._model.progress,
            self._model.phase,
            self._model.running,
        )
