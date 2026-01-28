# PyInstaller spec file for BT GUI

import sys
from pathlib import Path

# Paths
gui_path = Path('../../.gui')
root_path = Path('../..')

block_cipher = None

a = Analysis(
    [str(gui_path / 'btgui.py')],
    pathex=[str(root_path)],
    binaries=[],
    datas=[
        # Include BT modules needed by GUI
        (str(root_path / 'run.py'), '.'),
        (str(root_path / 'data.py'), '.'),
        (str(root_path / 'logger.py'), '.'),
        (str(root_path / 'misc.py'), '.'),
        (str(root_path / 'evaluate.py'), '.'),
        (str(root_path / 'bt.py'), '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BTGui' if sys.platform == 'win32' else 'btgui',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if sys.platform == 'win32' else None,
)

# On macOS, create an app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='BTGui.app',
        icon='icon.icns',
        bundle_identifier='com.hpe.biostool.gui',
    )
