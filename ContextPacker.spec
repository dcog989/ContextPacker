# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

selenium_datas = collect_data_files('selenium')
app_assets = [
    ('assets/icons/ContextPacker.ico', 'assets/icons'),
    ('assets/icons/ContextPacker-x64.png', 'assets/icons'),
    ('assets/icons/ContextPacker-x128.png', 'assets/icons'),
    ('assets/icons/copy.png', 'assets/icons'),
    ('assets/fonts/SourceCodePro-Regular.ttf', 'assets/fonts')
]

all_datas = selenium_datas + app_assets

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=all_datas,
    hiddenimports=['tiktoken_ext.openai_public'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyi_rth_selenium.py'],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ContextPacker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icons/ContextPacker.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ContextPacker',
)
