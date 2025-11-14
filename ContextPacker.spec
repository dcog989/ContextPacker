# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

app_assets = [
    ('assets/icons/ContextPacker.ico', 'assets/icons'),
    ('assets/icons/copy.svg', 'assets/icons'),
    ('assets/icons/paint-bucket.svg', 'assets/icons'),
    ('assets/icons/arrow-up.svg', 'assets/icons'),
    ('assets/icons/arrow-down.svg', 'assets/icons'),
    ('assets/icons/checkmark.svg', 'assets/icons'),
    ('assets/fonts/SourceCodePro-VariableFont_wght.ttf', 'assets/fonts'),
    ('assets/fonts/SourceCodePro-Italic-VariableFont_wght.ttf', 'assets/fonts'),
]

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=app_assets,
    hiddenimports=['tiktoken_ext.openai_public'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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