# Linux Installer for HPE Server BIOS Tool

This directory contains Debian package configuration for Linux distributions.

## Prerequisites

### Build System Requirements
```bash
sudo apt-get install dpkg-dev debhelper dh-python python3 python3-dev
```

### For VS Code Extension (optional)
```bash
sudo apt-get install nodejs npm
npm install -g @vscode/vsce
```

### Runtime Requirements (installed automatically)
- Python 3.7 or later
- Git

## Building the Debian Package

### Using Build Script (Recommended)

```bash
chmod +x build-deb.sh
./build-deb.sh
```

This will:
1. Create a clean build directory
2. Copy all necessary files
3. Build the VS Code extension (if Node.js/npm available)
4. Build the `.deb` package
5. Output the package to `./build/`

### Manual Build

```bash
# Create working directory
mkdir -p build/biostool-0.6.0
cd build/biostool-0.6.0

# Copy source files
cp -r ../../*.py ../../*.txt .
cp -r ../../attach ../../build ../../clean ../../config ../../create .
cp -r ../../destroy ../../detach ../../init ../../merge ../../move .
cp -r ../../pull ../../push ../../select ../../status ../../switch ../../top .

# Copy debian control files
cp -r ../debian .

# Build package
dpkg-buildpackage -us -uc -b

# Package will be in ../
```

## Installing the Package

### Standard Install
```bash
sudo dpkg -i biostool_0.7.0-1_all.deb
sudo apt-get install -f  # Fix any missing dependencies
```

### Install with VS Code Extension
```bash
# After installing the package
code --install-extension /usr/share/biostool/BIOSTool-0.7.0.vsix
```

## Package Contents

### Files Installed
- `/usr/bin/bt` - Main executable wrapper
- `/usr/share/biostool/` - Python modules and commands
- `/usr/share/doc/biostool/` - Documentation
- `/usr/share/biostool/*.vsix` - VS Code extension (if built)

### Post-Install Actions
- Checks for Python 3 installation
- Notifies about VS Code extension installation
- Displays getting started information

## Supported Distributions

Tested on:
- Ubuntu 20.04, 22.04, 24.04
- Debian 10, 11, 12
- Linux Mint 20, 21

Should work on any Debian-based distribution.

## Testing

### On a Clean System
```bash
# Build package
./build-deb.sh

# Install
sudo dpkg -i build/biostool_0.7.0-1_all.deb

# Test
bt --help
bt status

# Uninstall
sudo apt-get remove biostool

# Purge (remove all config)
sudo apt-get purge biostool
```

### In Docker Container
```bash
# Ubuntu container
docker run -it --rm -v $(pwd):/work ubuntu:22.04 bash
cd /work
apt-get update
apt-get install -y ./build/biostool_0.7.0-1_all.deb
bt --help
```

## Customization

### Modify Package Metadata
Edit `debian/control`:
- Change maintainer
- Update dependencies
- Modify package description

### Change Installation Paths
Edit `debian/rules`:
- Modify install directories
- Add/remove files
- Customize build process

### Update Changelog
Edit `debian/changelog`:
```bash
dch -v 0.7.0-2 "Your change description"
```

## Distribution

### Local Repository
```bash
# Create repository structure
mkdir -p repo/pool/main
cp build/biostool_0.7.0-1_all.deb repo/pool/main/

# Generate package list
cd repo
dpkg-scanpackages pool/ | gzip -9c > dists/stable/main/binary-amd64/Packages.gz

# Serve via HTTP
python3 -m http.server 8080
```

### Users can then add:
```bash
# Add repository
echo "deb [trusted=yes] http://your-server:8080 stable main" | sudo tee /etc/apt/sources.list.d/biostool.list

# Install
sudo apt-get update
sudo apt-get install biostool
```

## Troubleshooting

### Build Fails: Missing Dependencies
```bash
sudo apt-get install dpkg-dev debhelper dh-python
```

### Python Not Found After Install
```bash
sudo apt-get install python3
```

### Permission Denied on Scripts
```bash
chmod 755 debian/rules debian/postinst debian/postrm
```

### Package Won't Install
```bash
# Check dependencies
dpkg-deb -I biostool_0.7.0-1_all.deb

# Force install (not recommended)
sudo dpkg -i --force-depends biostool_0.7.0-1_all.deb
```

## Converting to Other Formats

### RPM (for RedHat/Fedora/CentOS)
```bash
sudo apt-get install alien
alien -r biostool_0.7.0-1_all.deb
```

### Snap Package
```bash
# Create snapcraft.yaml
snapcraft
```

## GitHub Integration

Add to `.github/workflows/build.yml`:
```yaml
- name: Build Debian Package
  run: |
    cd installers/linux
    chmod +x build-deb.sh
    ./build-deb.sh
    
- name: Upload Package
  uses: actions/upload-artifact@v3
  with:
    name: debian-package
    path: installers/linux/build/*.deb
```
