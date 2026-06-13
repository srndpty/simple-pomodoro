"""pytest 共通設定。

GUI テストがディスプレイサーバーなしの CI でもヘッドレスで動くよう、Qt を
オフスクリーンのプラットフォームプラグインに強制する。
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
