# -*- mode: python ; coding: utf-8 -*-
"""
CYBER-IA // PyInstaller Build Specification
Compiles the FastAPI/PyTorch inference server into a standalone backend binary
bundled directly into Tauri v2 as a managed child process.
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Hidden imports required by dynamic reflection (uvicorn, fastapi, pydantic, diffusers)
hidden_imports = [
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'starlette',
    'pydantic',
    'pydantic_core',
    'torch',
    'diffusers',
    'transformers',
    'accelerate',
    'safetensors',
    'PIL',
    'psutil',
    'websockets',
    'app',
    'app.main',
    'app.api',
    'app.api.routes',
    'app.api.diffusion_routes',
    'app.core',
    'app.core.hardware',
    'app.core.api_tracker',
    'app.schemas',
    'app.schemas.chat',
    'app.services',
    'app.services.diffusion_engine',
    'app.services.model_scanner',
    'app.services.architectures',
    'app.services.architectures.base',
    'app.services.architectures.sd15',
    'app.services.architectures.sdxl',
    'app.services.architectures.anima',
    'app.services.architectures.auto_diffusers',
    'app.services.architectures.registry',
]

datas = []

a = Analysis(
    ['run.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter.test',
        'unittest',
        'pytest',
        'torch.testing',
        'torch.utils.benchmark',
        'test',
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
    name='cyber-ia-api',
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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='cyber-ia-api',
)
