#!/bin/bash
# Build Debian package for HPE Server BIOS Tool

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"

echo "Building BIOSTool Debian Package..."

# Check for required tools
if ! command -v dpkg-buildpackage &> /dev/null; then
    echo "Error: dpkg-buildpackage not found. Install with:"
    echo "  sudo apt-get install dpkg-dev debhelper dh-python"
    exit 1
fi

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found."
    exit 1
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Create build directory structure
PACKAGE_DIR="$BUILD_DIR/biostool-0.7.0"
mkdir -p "$PACKAGE_DIR"

# Copy source files
echo "Copying source files..."
cd "$PROJECT_ROOT"
cp -r *.py *.txt *.md "$PACKAGE_DIR/" 2>/dev/null || true
cp -r attach build clean config create destroy detach init merge move pull push select status switch top "$PACKAGE_DIR/"

# Copy debian directory
echo "Copying debian package files..."
cp -r "$SCRIPT_DIR/debian" "$PACKAGE_DIR/"

# Make sure debian files have correct permissions
chmod 755 "$PACKAGE_DIR/debian/rules"
chmod 755 "$PACKAGE_DIR/debian/postinst"
chmod 755 "$PACKAGE_DIR/debian/postrm"

# Build VS Code extension if it exists
VSCODE_EXT_DIR="$PROJECT_ROOT/.vscode-extension"
if [ -d "$VSCODE_EXT_DIR" ]; then
    echo "Building VS Code extension..."
    cd "$VSCODE_EXT_DIR"
    if [ -f "package.json" ]; then
        if command -v npm &> /dev/null; then
            npm install
            npm run compile
            npx @vscode/vsce package --out "$PACKAGE_DIR/"
        else
            echo "Warning: npm not found. Skipping VS Code extension build."
        fi
    fi
fi

# Build package
echo "Building Debian package..."
cd "$PACKAGE_DIR"
dpkg-buildpackage -us -uc -b

# Move .deb file to output
echo "Package built successfully!"
echo ""
echo "Output files:"
ls -lh "$BUILD_DIR"/*.deb 2>/dev/null || true
echo ""
echo "To install:"
echo "  sudo dpkg -i $BUILD_DIR/biostool_0.7.0-1_all.deb"
echo "  sudo apt-get install -f  # To fix any dependency issues"
