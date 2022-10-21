# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

binaries = [
    ('C:\\Windows\\System32\\libusb0.dll', '.'),
    ('C:\\Windows\\System32\\libusb-1.0.dll', '.'),
    ('C:\\Windows\\System32\\libusbk.dll', '.')
]

datas = [
    ('C:\\path_to_thermy\\thermy\\img\\logotext.png', 'img'), 
    ('C:\\path_to_thermy\\thermy\\img\\print.ico', 'img'), 
    ('C:\\path_to_thermy\\thermy\\lib\\site-packages\\escpos\\capabilities.json', 'escpos'),
    ('C:\\path_to_thermy\\thermy\\.env', '.'),
    ('C:\\path_to_thermy\\thermy\\qrcontent.txt', '.')
]

a = Analysis(
    ['thermy.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=['usb'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='thermy',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='thermy',
)
