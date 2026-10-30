# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\multi-remote\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('D:\\multi-remote\\app\\check.svg', 'app')],
    hiddenimports=['PyQt5.QAxContainer', 'PyQt5.QtCore', 'PyQt5.QtWidgets', 'PyQt5.QtGui', 'app', 'app.styles', 'app.models', 'app.rdp_widget', 'app.screen_capture_widget', 'app.connection_panel', 'app.multiview_window', 'app.about_dialog', 'app.main_window', 'app.rdp_launcher', 'app.embedded_mstsc'],
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
    a.binaries,
    a.datas,
    [],
    name='MultiRemoteDesktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
