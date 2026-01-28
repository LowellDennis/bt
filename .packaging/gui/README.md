# GUI Standalone Packaging with PyInstaller

This directory contains scripts to package the BT GUI as a standalone executable.

## Overview

PyInstaller bundles the Python interpreter, GUI application, and all dependencies into a single executable that can run without Python installed.

## Prerequisites

```bash
pip install pyinstaller
```

## Building

### Windows

```powershell
cd packaging\gui
.\build-gui-windows.ps1
```

Output: `dist/BTGui.exe`

### Linux

```bash
cd packaging/gui
./build-gui-linux.sh
```

Output: `dist/btgui`

## Configuration

See `btgui.spec` for PyInstaller configuration:
- Entry point: `../../.gui/btgui.py`
- Icon: `icon.ico` (Windows) / `icon.png` (Linux)
- Hidden imports and data files

## Distribution

The standalone GUI can be distributed independently of the full installer for users who only need the graphical interface.

## Limitations

- Larger file size (~50-100 MB due to bundled Python)
- Slower startup than installed version
- Platform-specific (build on Windows for Windows, Linux for Linux)
