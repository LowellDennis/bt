# Windows Installer for HPE Server BIOS Tool

This directory contains the Inno Setup installer configuration for Windows.

## Prerequisites

1. **Inno Setup 6.0 or later**
   - Download from: https://jrsoftware.org/isinfo.php
   - Install using default settings

2. **Node.js and npm** (for VS Code extension)
   - Download from: https://nodejs.org/
   - Required to build the VS Code extension

3. **Python** (runtime requirement)
   - The installer will check for Python but won't install it
   - Users need Python installed to run BT

## Building the Installer

### Using PowerShell Script (Recommended)

```powershell
.\build-installer.ps1
```

Options:
- `-SkipVSCodeExtension`: Skip building the VS Code extension
- `-Configuration Release`: Build configuration (default)

### Manual Build

1. Build VS Code extension first:
   ```powershell
   cd ..\..\vscode-extension
   npm install
   npm run compile
   npx @vscode/vsce package --out .
   ```

2. Compile installer:
   ```powershell
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" biostool.iss
   ```

3. Find output in `.\output\`

## Installer Features

### Components
- **Core BT Tool** (required): Command-line tool and all modules
- **VS Code Extension** (optional): Integrated development environment support
- **GUI Application** (optional): Future graphical interface

### Installation Options
- Add BT to system PATH
- Install VS Code extension automatically (if VS Code detected)
- Create desktop shortcuts (for GUI)

### Detection
- Checks for Python installation
- Detects VS Code installation
- Warns if prerequisites are missing

## Testing

1. Build installer
2. Run on clean Windows VM
3. Verify:
   - Files installed to `C:\Program Files\HPE\BIOSTool`
   - PATH updated correctly
   - `bt --help` works from command prompt
   - VS Code extension installed (if selected)

## Customization

Edit `biostool.iss` to:
- Change default installation directory
- Add/remove files
- Modify registry entries
- Customize installer appearance
- Add post-install actions

## Troubleshooting

### Build fails with "File not found"
- Ensure all source files exist in parent directories
- Check that VS Code extension is built (`.vsix` file exists)

### Extension not installing
- VS Code must be installed before running installer
- Try manual install: `code --install-extension BIOSTool-0.6.0.vsix`

### PATH not updating
- Installer requires admin privileges
- Log out/in or restart for PATH changes to take effect

## Distribution

Upload installer to:
- GitHub Releases
- Internal distribution server
- Network share for team access

Filename format: `BIOSTool-<version>-Setup.exe`
