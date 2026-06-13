# CLAUDE.md

このプロジェクトのガイドラインは [AGENTS.md](AGENTS.md) に集約しています。
作業を始める前に必ず目を通してください。

特に次の点に注意:

- `model` / `config` / `formatting` に Qt を import しない(ロジックは Qt 非依存に保つ)。
- 変更後は `ruff check .` / `ruff format .` / `mypy` / `pytest` をすべて通す。
- PyQt6 / Windows / 実時間タイマーまわりのハマりどころは AGENTS.md の該当節を参照。
