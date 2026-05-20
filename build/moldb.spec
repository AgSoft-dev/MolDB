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
    ],
    hiddenimports=[
    'ui',
    'ui.app',
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
    'starlette',
    'starlette.routing',
    'starlette.middleware',
    'starlette.middleware.cors',
    'uvicorn',
    'uvicorn.main',
    'uvicorn.config',
    'uvicorn.server',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.loops.asyncio',        # ← missing
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.http.h11_impl',      # ← missing
    'uvicorn.protocols.websockets',         # ← missing
    'uvicorn.protocols.websockets.auto',    # ← missing
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'uvicorn.lifespan.off',                 # ← missing
    'anyio',
    'anyio._backends._asyncio',
    'h11',                                  # ← missing (uvicorn depends on it)
    'click',                                # ← missing (uvicorn CLI)
    'rapidfuzz',
],
    hookspath=['hooks'],
    hooksconfig={},
    runtime_hooks=['hooks/rthook_uvicorn.py'],
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
