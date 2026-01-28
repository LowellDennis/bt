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
PACKAGE_DIR="$BUILD_DIR/biostool-1.0.0"
mkdir -p "$PACKAGE_DIR"

# Copy source files
echo "Copying source files..."
cd "$PROJECT_ROOT"
cp *.py *.sh *.txt *.md "$PACKAGE_DIR/" 2>/dev/null || true
cp -r attach build cleanup config create remove detach init merge move fetch push select status use top worktrees "$PACKAGE_DIR/"
# Copy GUI application
if [ -d "$PROJECT_ROOT/.gui" ]; then
    echo "Copying GUI application..."
    cp -r "$PROJECT_ROOT/.gui" "$PACKAGE_DIR/"
fi

# Copy debian directory
echo "Copying debian package files..."
cp -r "$SCRIPT_DIR/debian" "$PACKAGE_DIR/"

# Make sure debian files have correct permissions
chmod 755 "$PACKAGE_DIR/debian/rules"
chmod 755 "$PACKAGE_DIR/debian/postinst"
chmod 755 "$PACKAGE_DIR/debian/postrm"

# Copy pre-built VS Code extension if it exists
VSCODE_EXT_DIR="$PROJECT_ROOT/.vscode-extension"
if [ -f "$VSCODE_EXT_DIR/BIOSTool-1.0.0.vsix" ]; then
    echo "Copying VS Code extension..."
    cp "$VSCODE_EXT_DIR/BIOSTool-1.0.0.vsix" "$PACKAGE_DIR/"
else
    echo "Warning: Pre-built VS Code extension not found. Skipping."
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
echo "  sudo dpkg -i $BUILD_DIR/biostool_1.0.0-1_all.deb"
echo "  sudo apt-get install -f  # To fix any dependency issues"
