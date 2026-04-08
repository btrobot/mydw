# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for DewuGoJin backend."""

import os
import sys
from pathlib import Path

block_cipher = None

# Collect migration modules
migrations = [
    f'migrations.{p.stem}'
    for p in Path('migrations').glob('*.py')
    if p.stem != '__init__'
]

a = Analysis(
    ['pyinstaller_entry.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('migrations', 'migrations'),
    ],
    hiddenimports=[
        # migrations (dynamic imports)
        *migrations,
        # uvicorn internals
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.http.httptools_impl',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.wsproto_impl',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        # async db
        'aiosqlite',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.dialects.sqlite.aiosqlite',
        # cryptography
        'cryptography.hazmat.primitives.ciphers.aead',
        'cryptography.hazmat.backends.openssl',
        # pydantic
        'pydantic',
        'pydantic_settings',
        'pydantic.deprecated.decorator',
        # fastapi / starlette
        'fastapi',
        'starlette.responses',
        'starlette.routing',
        'starlette.middleware',
        'starlette.middleware.cors',
        'multipart',
        'multipart.multipart',
        # httpx
        'httpx',
        'httpcore',
        'h11',
        # loguru
        'loguru',
        # apscheduler
        'apscheduler',
        'apscheduler.schedulers.asyncio',
        'apscheduler.triggers.cron',
        'apscheduler.triggers.interval',
        # dotenv
        'dotenv',
        # email (used by pydantic)
        'email_validator',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'patchright',
        'playwright',
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'test',
        'unittest',
    ],
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
    name='backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='backend',
)
