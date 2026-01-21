# HPE Server BIOS Tool Installers

This directory contains installer configurations for multiple platforms.

## Available Installers

### Windows
- **Inno Setup** installer (`.exe`)
- Located in `windows/`
- See [windows/README.md](windows/README.md) for build instructions

### Linux
- **Debian** package (`.deb`)
- Located in `linux/debian/`
- See [linux/README.md](linux/README.md) for build instructions

## Quick Start

### Building Windows Installer
```powershell
cd windows
.\build-installer.ps1
```

Output: `windows/output/BIOSTool-0.7.0-Setup.exe`

### Building Debian Package
```bash
cd linux
chmod +x build-deb.sh
./build-deb.sh
```

Output: `linux/build/biostool_0.7.0-1_all.deb`

## What Gets Installed

All installers include:

1. **BT Command-Line Tool**
   - Core Python scripts
   - All command modules (build, clean, init, etc.)
   - Helper scripts (bt.cmd for Windows)

2. **VS Code Extension** (optional)
   - Integrated development environment support
   - Command palette integration
   - Configuration UI

3. **Documentation**
   - README.md
   - Command help files

## Version Management

Version is defined in multiple places and must be kept in sync:

- `bt.py` - Line 16: `print('BIOS Tool V0.7')`
- `README.md` - Current Version and Version History
- `windows/biostool.iss` - `#define MyAppVersion "0.7.0"`
- `linux/debian/changelog` - First entry
- `.vscode-extension/package.json` - `"version": "0.7.0"`

When updating version, update all these files.

## Prerequisites

### Windows Build System
- Inno Setup 6.0+
- Node.js + npm (for VS Code extension)
- PowerShell 5.1+

### Linux Build System
- dpkg-dev
- debhelper
- dh-python
- Python 3.7+
- Node.js + npm (for VS Code extension)

### User Runtime Requirements
- Python 3.7 or later
- Git (for version control features)
- VS Code (optional, for extension)

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Build Installers

on: [push, release]

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Windows Installer
        run: |
          cd installers/windows
          .\build-installer.ps1
      - uses: actions/upload-artifact@v3
        with:
          name: windows-installer
          path: installers/windows/output/*.exe

  build-linux:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Dependencies
        run: sudo apt-get install dpkg-dev debhelper dh-python
      - name: Build Debian Package
        run: |
          cd installers/linux
          chmod +x build-deb.sh
          ./build-deb.sh
      - uses: actions/upload-artifact@v3
        with:
          name: debian-package
          path: installers/linux/build/*.deb
```

## Testing Installers

### Windows
1. Build installer
2. Test on clean Windows VM
3. Verify:
   - Installation completes
   - `bt --help` works
   - PATH is updated
   - VS Code extension installs (if selected)
   - Uninstaller works

### Linux
1. Build package
2. Test in Docker or VM:
   ```bash
   docker run -it ubuntu:22.04
   apt-get update && apt-get install -y ./biostool_0.7.0-1_all.deb
   bt --help
   ```
3. Verify:
   - Package installs
   - Dependencies resolved
   - `bt` command works
   - Extension available

## Distribution

### Internal Distribution
- Network share
- Internal package repository
- Email to team

### External Distribution
- GitHub Releases
- Download page
- Package managers (future)

### File Naming Convention
- Windows: `BIOSTool-<version>-Setup.exe` (e.g., `BIOSTool-0.7.0-Setup.exe`)
- Debian: `biostool_<version>-<revision>_all.deb` (e.g., `biostool_0.7.0-1_all.deb`)

## Troubleshooting

### Windows Build Issues
- Ensure Inno Setup is installed
- Check VS Code extension built successfully
- Verify all source files exist

### Linux Build Issues
- Install build dependencies
- Check file permissions on debian/ scripts
- Ensure Python 3 is available

### Installation Issues
- Windows: Run installer as administrator
- Linux: Use `sudo apt-get install -f` to fix dependencies
- Check Python installation exists

## Future Enhancements

- [ ] RPM package for RedHat/Fedora/CentOS
- [ ] macOS installer (if needed)
- [ ] Snap package for universal Linux
- [ ] Chocolatey package for Windows
- [ ] Homebrew formula for macOS
- [ ] Docker container
- [ ] Auto-update mechanism

## Support

For issues with installers:
- Check platform-specific README
- Review build logs
- Contact: Lowell Dennis <lowell.dennis@hpe.com>
