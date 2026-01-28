# macOS Installer Build Scripts

This directory contains scripts to build a macOS installer package (.pkg) or disk image (.dmg) for BIOS Tool.

## Overview

Creates a macOS installer that:
- Installs BT CLI tool to `/usr/local/opt/biostool/`
- Installs GUI tool
- Creates symlink: `/usr/local/bin/bt`
- Auto-detects and installs VS Code extension
- Requires Python 3.8+

## Prerequisites

- macOS 10.15 (Catalina) or later
- Xcode Command Line Tools
- Python 3.8+
- Node.js/npm (for VS Code extension)

```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install pkgbuild (usually included with Xcode)
which pkgbuild
```

## Building

### Build .pkg Installer

```bash
cd installers/macos
./build-pkg.sh
```

Output: `build/BIOSTool-X.Y.Z.pkg`

### Build .dmg Disk Image

```bash
cd installers/macos
./build-dmg.sh
```

Output: `build/BIOSTool-X.Y.Z.dmg`

## Distribution Requirements

### Code Signing (Optional but Recommended)

For distribution outside your organization:

```bash
# Sign the package
productsign --sign "Developer ID Installer: Your Name" \
  build/BIOSTool-X.Y.Z.pkg \
  build/BIOSTool-X.Y.Z-signed.pkg

# Notarize with Apple
xcrun notarytool submit build/BIOSTool-X.Y.Z-signed.pkg \
  --apple-id your@email.com \
  --team-id TEAMID \
  --password @keychain:AC_PASSWORD
```

### Without Code Signing

Users will need to:
1. Right-click the installer
2. Select "Open"
3. Confirm security prompt

## Installation Locations

- **CLI Tool**: `/usr/local/opt/biostool/`
- **GUI Tool**: `/usr/local/opt/biostool/.gui/`
- **Symlink**: `/usr/local/bin/bt`
- **GUI Wrapper**: `/usr/local/bin/btgui`
- **VS Code Extension**: Auto-detected VS Code installation

## Testing

Test on a clean macOS installation:

```bash
# Install
sudo installer -pkg build/BIOSTool-X.Y.Z.pkg -target /

# Verify
bt --help
btgui &

# Uninstall
sudo /usr/local/opt/biostool/uninstall.sh
```

## Structure

```
installers/macos/
├── build-pkg.sh          # Build .pkg installer
├── build-dmg.sh          # Build .dmg disk image
├── scripts/
│   ├── postinstall       # Post-installation script
│   └── uninstall.sh      # Uninstallation script
├── resources/
│   ├── background.png    # DMG background image
│   └── icon.icns         # Application icon
└── build/                # Output directory
```

## Limitations

- Requires Python 3.8+ pre-installed
- macOS 10.15+ only
- Intel and Apple Silicon (universal binary for GUI if using PyInstaller)

## Future Enhancements

- Bundle Python interpreter (like Windows installer)
- Universal binary support
- Automatic updates framework
- Homebrew formula as alternative distribution
