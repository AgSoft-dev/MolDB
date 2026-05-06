# -*- mode: python ; coding: utf-8 -*-
# Build: cd build && pyinstaller moldb.spec --clean
# Output: ../dist/MolDB.exe

block_cipher = None

a = Analysis(
    ['../run.py'],
    pathex=['..'],
    binaries=[],
    datas=[
        ('../ui/static',    'ui/static'),
        ('../ui/templates', 'ui/templates'),
    ],
    hiddenimports=[
        'rdkit',
        'rdkit.Chem',
        'rdkit.Chem.Draw',
        'rdkit.Chem.AllChem',
        'rdkit.Chem.rdMolDescriptors',
        'rdkit.Chem.inchi',
        'rdkit.Chem.Draw.rdMolDraw2D',
        'sqlmodel',
        'sqlalchemy',
        'sqlalchemy.dialects.sqlite',
        'fastapi',
        'fastapi.staticfiles',
        'fastapi.templating',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'anyio',
        'anyio._backends._asyncio',
        'rapidfuzz',
    ],
    hookspath=['hooks'],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MolDB',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,           # no console window on Windows
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='../assets/moldb.ico',   # uncomment once you have an icon
)
