
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app.py', '.'),
        ('README.md', '.'),
        ('.streamlit/config.toml', '.streamlit'),
        ('assets/*', 'assets'),
        ('lib/*.py', 'lib'),
        ('pages/*.py', 'pages'),
    ],
    hiddenimports=['streamlit', 'pandas', 'openpyxl', 'reportlab', 'PIL', 'sqlalchemy', 'passlib', 'numpy', 'plotly'],
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
    name='FluxoPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,   # janela oculta; se quiser logs, mude para True
    icon=None
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FluxoPro'
)
