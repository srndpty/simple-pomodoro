# -*- mode: python ; coding: utf-8 -*-
"""単一ファイルの Windows 実行ファイルをビルドするための PyInstaller spec。

次のコマンドでビルドする::

    pyinstaller packaging/simple-pomodoro.spec

成果物は ``dist/simple-pomodoro.exe`` に出力される。
"""

from pathlib import Path

from PyInstaller.building.api import COLLECT, EXE, PYZ  # noqa: F401
from PyInstaller.building.build_main import Analysis

# SPECPATH は PyInstaller がこの spec の置かれたディレクトリとして注入する。
# 実行時の cwd に依存しないよう、ここから絶対パスを組み立てる。
ROOT = Path(SPECPATH).parent  # noqa: F821 (SPECPATH は PyInstaller が注入)
SRC = ROOT / "src"

a = Analysis(
    [str(SRC / "pomodoro" / "__main__.py")],
    pathex=[str(SRC)],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="simple-pomodoro",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI アプリ: コンソールウィンドウを出さない。
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
