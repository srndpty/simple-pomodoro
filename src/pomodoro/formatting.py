"""UI で共有する、小さく純粋な整形用ヘルパー。"""

from __future__ import annotations


def format_mmss(total_seconds: int) -> str:
    """非負の秒数を ``MM:SS`` 形式に整形する。

    分は 60 で頭打ちにしないため、90 分は ``90:00`` と表示される。
    """
    if total_seconds < 0:
        raise ValueError("total_seconds must be non-negative")
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"
