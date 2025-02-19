# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=['C:/Users/10650/pyprogram/miaomiao/venv/Lib/site-packages','C:/Users/10650/pyprogram/miaomiao/venv/Lib/site-packages/paddle/libs'],
    binaries=[('C:/Users/10650/pyprogram/miaomiao/venv/Lib/site-packages/paddle/libs', '.')],
    datas=[('C:/Users/10650/pyprogram/miaomiao/venv/Lib/site-packages/paddleocr/ppocr', 'paddleocr/ppocr'),('C:/Users/10650/pyprogram/miaomiao/venv/Lib/site-packages/paddleocr/tools', 'paddleocr/tools'),('C:/Users/10650/pyprogram/miaomiao/venv/Lib/site-packages/paddleocr/ppstructure', 'paddleocr/ppstructure'),
    ('C:/Users/10650/pyprogram/miaomiao/templates', 'templates'),

    ],

    #    ('C:/Users/10650/pyprogram/miaomiao/auction_data', 'auction_data'),
    #    ('C:/Users/10650/pyprogram/miaomiao/cleaned_data', 'cleaned_data'),
    hiddenimports=['jaraco.collections', 'shapely.geometry', 'pyclipper', 'skimage', 'skimage.morphology',
    'imgaug', 'albumentations', 'lmdb', 'docx'],
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
    name='妙妙工具箱',
    debug=False,  # 调试选项，False表示不启用调试模式。
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # 控制台窗口，False表示不显示控制台窗口（对于GUI应用）。
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='ico.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='妙妙工具箱',
)
