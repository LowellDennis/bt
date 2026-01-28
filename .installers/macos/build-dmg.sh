#!/bin/bash
# Build macOS .dmg disk image for BIOS Tool

set -e

echo "Building macOS .dmg disk image for BIOS Tool..."

# Configuration
VERSION="1.0.0"
PACKAGE_NAME="BIOSTool"

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"
DMG_DIR="$BUILD_DIR/dmg"

# Ensure .pkg is built
if [ ! -f "$BUILD_DIR/${PACKAGE_NAME}-${VERSION}.pkg" ]; then
    echo "Building .pkg first..."
    "$SCRIPT_DIR/build-pkg.sh"
fi

# Clean DMG directory
rm -rf "$DMG_DIR"
mkdir -p "$DMG_DIR"

# Copy .pkg to DMG directory
cp "$BUILD_DIR/${PACKAGE_NAME}-${VERSION}.pkg" "$DMG_DIR/"

# Create symlink to Applications (optional, for drag-and-drop installers)
# ln -s /Applications "$DMG_DIR/Applications"

# Create README
cat > "$DMG_DIR/README.txt" << EOF
BIOS Tool v${VERSION}

Installation:
1. Double-click ${PACKAGE_NAME}-${VERSION}.pkg
2. Follow the installation wizard
3. Open Terminal and run: bt --help

For more information, visit:
https://github.com/YOUR_ORG/bt

To uninstall:
sudo /usr/local/opt/biostool/uninstall.sh
EOF

echo "Creating disk image..."

# Create the .dmg
hdiutil create -volname "${PACKAGE_NAME}-${VERSION}" \
               -srcfolder "$DMG_DIR" \
               -ov \
               -format UDZO \
               "$BUILD_DIR/${PACKAGE_NAME}-${VERSION}.dmg"

echo ""
echo "Build successful!"
echo "Disk Image: $BUILD_DIR/${PACKAGE_NAME}-${VERSION}.dmg"

# Show file size
ls -lh "$BUILD_DIR/${PACKAGE_NAME}-${VERSION}.dmg" | awk '{print "Size:", $5}'
