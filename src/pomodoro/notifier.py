"""フェーズ遷移時の音による通知。

:class:`Notifier` プロトコルにより、コントローラを具体的なサウンド実装から
切り離せる。これによりテストでのモック化が容易になり、後からよりリッチな実装
(独自の wav、システムトースト通知など)への差し替えもしやすくなる。
"""

from __future__ import annotations

import sys
from typing import Protocol, runtime_checkable


@runtime_checkable
class Notifier(Protocol):
    """フェーズ終了をユーザーに知らせられるものすべてを表す。"""

    def notify(self) -> None: ...


class SoundNotifier:
    """短いシステム音を鳴らす。

    Windows では :mod:`winsound` を使用し、それ以外のプラットフォームでは
    Qt アプリケーションのビープ音にフォールバックする。これにより、アプリの
    他の部分はプラットフォーム非依存に保たれる。
    """

    def notify(self) -> None:
        if sys.platform == "win32":
            import winsound

            winsound.MessageBeep(winsound.MB_ICONASTERISK)
            return

        # Windows 以外のプラットフォーム向けのフォールバック(主に開発/CI 用)。
        try:
            from PyQt6.QtWidgets import QApplication

            app = QApplication.instance()
            if app is not None:
                app.beep()
        except ImportError:
            pass
