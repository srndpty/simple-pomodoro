"""中央に残り時間を表示する円形プログレスウィジェット。"""

from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QWidget

from ..formatting import format_mmss
from ..model import Phase

# フェーズごとの円弧の色。
_PHASE_COLORS: dict[Phase, QColor] = {
    Phase.WORK: QColor("#e2584d"),
    Phase.BREAK: QColor("#43a047"),
}
_TRACK_COLOR = QColor("#3a3a3a")
_TIME_COLOR = QColor("#f5f5f5")
_LABEL_COLOR = QColor("#9e9e9e")

_FULL_CIRCLE_DEG = 360
_TWELVE_OCLOCK_DEG = 90  # Qt は角度を 3 時方向から反時計回りに測る。


class CircularTimer(QWidget):
    """フェーズの進行に応じて減っていくリングを描画する。

    状態は外部から :meth:`set_state` で与えられる。このウィジェットはタイマーも
    モデルも持たず、最後に渡された内容をそのまま描画するだけ。
    """

    _ARC_WIDTH = 12

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._remaining = 0
        self._progress = 0.0
        self._phase = Phase.WORK
        self.setMinimumSize(220, 220)

    def set_state(self, remaining: int, progress: float, phase: Phase) -> None:
        """表示内容を更新し、再描画を要求する。"""
        self._remaining = remaining
        self._progress = max(0.0, min(1.0, progress))
        self._phase = phase
        self.update()

    def paintEvent(self, event: object) -> None:  # noqa: N802 (Qt のオーバーライド)
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        side = min(self.width(), self.height())
        margin = self._ARC_WIDTH
        rect = QRectF(
            (self.width() - side) / 2 + margin,
            (self.height() - side) / 2 + margin,
            side - 2 * margin,
            side - 2 * margin,
        )

        self._draw_track(painter, rect)
        self._draw_progress_arc(painter, rect)
        self._draw_centre_text(painter, rect)
        painter.end()

    def _draw_track(self, painter: QPainter, rect: QRectF) -> None:
        pen = QPen(_TRACK_COLOR, self._ARC_WIDTH)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 0, _FULL_CIRCLE_DEG * 16)

    def _draw_progress_arc(self, painter: QPainter, rect: QRectF) -> None:
        remaining_fraction = 1.0 - self._progress
        if remaining_fraction <= 0:
            return
        pen = QPen(_PHASE_COLORS[self._phase], self._ARC_WIDTH)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        # Qt の角度は 1/16 度単位。12 時方向から開始し、残り割合の分だけ
        # 時計回り(負の方向)に描く。
        span = int(-remaining_fraction * _FULL_CIRCLE_DEG * 16)
        painter.drawArc(rect, _TWELVE_OCLOCK_DEG * 16, span)

    def _draw_centre_text(self, painter: QPainter, rect: QRectF) -> None:
        time_font = QFont(self.font())
        time_font.setPointSize(max(18, int(rect.height() * 0.18)))
        time_font.setBold(True)
        painter.setFont(time_font)
        painter.setPen(_TIME_COLOR)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, format_mmss(self._remaining))

        label_font = QFont(self.font())
        label_font.setPointSize(max(9, int(rect.height() * 0.07)))
        painter.setFont(label_font)
        painter.setPen(_LABEL_COLOR)
        label_rect = QRectF(rect)
        label_rect.translate(0, rect.height() * 0.22)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, self._phase.label)
