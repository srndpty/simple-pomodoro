# AGENTS.md

このリポジトリで作業するエージェント / 開発者向けのガイド。
人間にもそのまま読めるよう、プロジェクトの約束事と「ハマりどころ」をまとめている。

## プロジェクト概要

PyQt6 製の小さな Windows 向けポモドーロタイマー。25 分のフォーカス → 5 分の休憩を
無限ループし、フェーズ終了時に音で通知する。詳細な使い方は [README.md](README.md) を参照。

## アーキテクチャと依存方向

依存は一方向: **`ui → controller → model → config`**。

| モジュール | 役割 | Qt 依存 |
|---|---|---|
| `config.py` | 各種時間(frozen dataclass) | なし |
| `model.py` | `work→break→work` の状態機械 | なし |
| `formatting.py` | `MM:SS` 整形 | なし |
| `notifier.py` | `Notifier` プロトコル + `SoundNotifier` | なし(フォールバックのみ Qt) |
| `controller.py` | `QTimer` ↔ model ↔ notifier の橋渡し、シグナル公開 | あり |
| `ui/` | ウィジェット | あり |

**最重要の原則: `model` / `config` / `formatting` に Qt を import しないこと。**
ロジックを Qt から切り離しているからこそ、単体テストが速く・確実になる。新しい
ロジックは可能な限りこの「純粋」な層に置き、UI 層は薄く保つ。

## 開発コマンド

品質ツールはすべて `pyproject.toml` に設定済み。変更後は必ず次を通すこと:

```bash
ruff check .            # lint
ruff format .           # フォーマット(--check で確認のみ)
mypy                    # strict 型チェック
pytest                  # テスト + カバレッジ(80% 未満で失敗)
```

ヘッドレス環境では Qt にオフスクリーンバックエンドが必要(`tests/conftest.py` が
自動設定するが、手動実行時は明示する):

```bash
QT_QPA_PLATFORM=offscreen pytest   # PowerShell: $env:QT_QPA_PLATFORM="offscreen"
```

CI([.github/workflows/ci.yml](.github/workflows/ci.yml))は Linux で lint/型/テスト
(Python 3.10–3.12)、Windows で PyInstaller ビルド + 起動スモークを行う。

## コーディング規約

- `from __future__ import annotations` を全モジュール先頭に置く(`py310` ターゲット)。
- 型注釈は必須(mypy strict)。新規コードは型エラーゼロで通すこと。
- docstring・コメントは**日本語**で統一(コード識別子・例外メッセージは英語のまま)。
- 公開 API は最小限に。内部状態は `_` 始まりにし、プロパティで読み取り専用公開する。

## PyQt6 のハマりどころ(実際に踏んだもの)

- **mypy strict と `sys.platform` 分岐は両立しない。** `warn_unreachable` を有効に
  すると、解析中の単一 OS では必ず片方の分岐が「到達不能」と判定される。このため
  `warn_unreachable` はあえて**無効**にしている(`pyproject.toml` に注記あり)。
- **`QApplication.instance()` の戻り値は `QCoreApplication | None`。** `beep()` など
  `QApplication` 固有のメソッドを呼ぶ前に `isinstance(app, QApplication)` で絞り込む。
  `if app is not None:` だけだと **Linux CI でのみ** mypy が落ちる(Windows ローカルでは
  到達不能扱いでスキップされ気づけない)。
- **`QShortcut` は PyQt6 では `QtGui` にある**(Qt5 系の `QtWidgets` ではない)。
- **シグナル/スロットを介して UI とロジックをつなぐ。** ウィジェットがコントローラを
  直接 import するのではなく、コントローラのシグナル(`state_changed` /
  `phase_completed`)をビューが購読する形にする。
- **カスタム描画は `paintEvent` をオーバーライドし、末尾で `painter.end()` を呼ぶ。**
  Qt のオーバーライドはメソッド名が camelCase なので `# noqa: N802` を付ける。

## Windows 固有の注意点

- **通知音は `winsound.MessageBeep`**(`notifier.py`)。`winsound` は win32 限定なので
  必ず `if sys.platform == "win32":` ガード内で import する。それ以外の OS では Qt の
  `beep()` にフォールバックする(主に開発/CI 用)。
- **配布は単一ファイル exe**。`pyinstaller packaging/simple-pomodoro.spec` で
  `dist/simple-pomodoro.exe` を生成する(`console=False` の windowed ビルド)。
- **spec は cwd 非依存**にしてある。`Path(SPECPATH).parent` を起点に絶対パスを組み立てる
  ため、リポジトリルートからでも `packaging/` 配下からでもビルドできる。
- `*.spec` は `.gitignore` 対象だが、ビルド用 spec だけ `!packaging/simple-pomodoro.spec`
  で追跡している。

## このプロジェクト特有の事項

- **タイマーは実時間ベース。** `controller.py` は単調増加クロック(既定 `time.monotonic`)
  からの経過秒を `floor` で算出してモデルを進める。`QTimer` は 1 秒間隔の「ポーリング」
  に過ぎず、tick 回数には依存しない。スリープ復帰やイベントループ遅延でも実時間とズレない。
- **`PomodoroModel.advance(elapsed_seconds)` が正、`tick()` はその薄いラッパー。**
  経過秒を渡す設計なので、複数フェーズ境界を 1 回でまたげる。
- **大きな時間ジャンプでも通知音は 1 回だけ。** スリープから 1 時間後に復帰しても、
  音が何十回も鳴らないようにしている(`_on_timeout` のコメント参照)。
- **クロックは注入可能。** `PomodoroController(..., clock=...)` でテスト用 `FakeClock` を
  差し込み、実時間を待たずに決定的にテストする。
- **デバッグモード。** 環境変数 `POMODORO_DEBUG` を設定すると `Ctrl+D` で現在フェーズの
  残り 3 秒へジャンプし、通知音と遷移をすぐ確認できる(通常実行時はショートカット自体が
  存在しない)。
- **カバレッジ下限は 80%**(`--cov-fail-under=80`)。UI 描画コードはスモークテストで
  カバーする方針。下がったら CI で気づけるようにしている。

## 拡張のヒント

- 時間変更 / ロングブレイク → `PomodoroConfig` と `model._advance_phase` を拡張。
- 通知方法の差し替え → `Notifier` プロトコルを実装し `PomodoroController` に渡す。
- 設定・履歴・テーマ → コントローラのシグナルがフック地点になる。
