# simple-pomodoro

**PyQt6** で作った、小さくシンプルな Windows 向けポモドーロタイマー。

- ⏱️ 25 分の円形フォーカスタイマー、中央に残り時間を表示
- ▶️ 開始 / 一時停止・リセットの操作
- 🔔 フェーズ終了時に音で通知
- ☕ 5 分の休憩を自動で開始し、その後フォーカスへ戻る — これを無限にループ
- 🪟 小さめの固定サイズウィンドウ

タイマーのロジックは **Qt 非依存で完全にユニットテスト済み**、PyQt6 は描画と入力だけを
担当するよう、意図的に分離している。これにより、今はシンプルに保ちつつ、将来の拡張
(時間のカスタマイズ、ロングブレイク、設定、通知など)も容易にしている。

## アーキテクチャ

```
src/pomodoro/
├── config.py          # PomodoroConfig: 各種時間(純粋・イミュータブル)
├── model.py           # PomodoroModel: work→break→work の状態機械(純粋)
├── formatting.py      # MM:SS 整形ヘルパー(純粋)
├── notifier.py        # Notifier プロトコル + SoundNotifier(Windows では winsound)
├── controller.py      # QTimer ↔ model ↔ notifier の橋渡し、Qt シグナルを公開
├── app.py             # QApplication の起動処理
├── __main__.py        # `python -m pomodoro` のエントリポイント
└── ui/
    ├── circular_timer.py  # 自前描画の円形プログレスウィジェット
    └── main_window.py     # ウィンドウのレイアウト + シグナル結線
```

依存方向は一方向: `ui → controller → model → config`。
`model` / `config` / `formatting` は Qt を一切 import しないため、どこでも動作し、
テストも容易。

## はじめに

Python 3.10 以上が必要。

```bash
python -m venv .venv
.venv\Scripts\activate           # PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

### 実行

```bash
python -m pomodoro
# またはインストール後は単に:
simple-pomodoro
```

### デバッグモード(通知音を手早く確認する)

`POMODORO_DEBUG` を設定すると **Ctrl+D** のショートカットが有効になる。押すと
(必要ならタイマーを開始したうえで)現在のフェーズの残り 3 秒へジャンプするので、
フェーズ終了音と work↔break の遷移をほぼ即座に確認できる:

```bash
# PowerShell
$env:POMODORO_DEBUG=1; python -m pomodoro
# bash
POMODORO_DEBUG=1 python -m pomodoro
```

Ctrl+D を 1 回押すと focus→break のチャイム、もう 1 回押すと break→focus を確認できる。
通常の実行時にはこのショートカットは存在しない。

## 開発

品質ツールはすべて `pyproject.toml` に設定済み。

```bash
ruff check .            # lint
ruff format .           # フォーマット
mypy                    # 厳格な型チェック
pytest                  # テスト + カバレッジ(ターミナル + coverage.xml)
```

ヘッドレス環境(および CI)では、Qt のオフスクリーンバックエンドが必要:

```bash
QT_QPA_PLATFORM=offscreen pytest     # PowerShell: $env:QT_QPA_PLATFORM="offscreen"
```

## Windows 実行ファイルのビルド

バージョン管理された PyInstaller spec で、単一ファイルの windowed exe を生成する:

```bash
pyinstaller packaging/simple-pomodoro.spec
# → dist/simple-pomodoro.exe
```

## CI

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) は、Python 3.10〜3.12 で
ruff・mypy・pytest(カバレッジ付き)を実行し、その後 Windows 実行ファイルをビルドして
アーティファクトとしてアップロードする。

## 拡張のヒント

- **時間の変更 / ロングブレイク** — `PomodoroConfig` と `model.py` の `_advance`
  ロジックを拡張する。単純な時間調整なら UI とコントローラの変更は不要。
- **カスタム音** — `Notifier` プロトコルを実装し、`PomodoroController` に渡す。
- **設定・履歴・テーマ** — コントローラの `state_changed` / `phase_completed`
  シグナルが、きれいなフック地点になる。
