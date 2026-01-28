#!/bin/bash
# Build macOS .pkg installer for BIOS Tool

set -e

echo "Building macOS .pkg installer for BIOS Tool..."

# Configuration
VERSION="1.0.0"
PACKAGE_NAME="BIOSTool"
IDENTIFIER="com.hpe.biostool"
INSTALL_ROOT="/usr/local/opt/biostool"

# Directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/../.."
BUILD_DIR="$SCRIPT_DIR/build"
PAYLOAD_DIR="$BUILD_DIR/payload"
SCRIPTS_DIR="$BUILD_DIR/scripts"

# Clean previous build
rm -rf "$BUILD_DIR"
mkdir -p "$PAYLOAD_DIR$INSTALL_ROOT"
mkdir -p "$SCRIPTS_DIR"

echo "Copying files..."

# Copy base tool
cp -r "$PROJECT_ROOT"/*.py "$PAYLOAD_DIR$INSTALL_ROOT/"
cp "$PROJECT_ROOT"/bt.sh "$PAYLOAD_DIR$INSTALL_ROOT/"
cp "$PROJECT_ROOT"/global.txt "$PAYLOAD_DIR$INSTALL_ROOT/"

# Copy command directories
for cmd_dir in "$PROJECT_ROOT"/*/; do
    cmd_name=$(basename "$cmd_dir")
    # Skip special directories
    if [[ "$cmd_name" != "." && "$cmd_name" != ".."  && "$cmd_name" != "installers" && "$cmd_name" != "tests" && "$cmd_name" != "docs" && "$cmd_name" != "packaging" && "$cmd_name" != ".vscode-extension" && "$cmd_name" != ".gui" && "$cmd_name" != "scripts" && "$cmd_name" != ".github" && "$cmd_name" != ".githooks" ]]; then
        if [ -f "$cmd_dir/${cmd_name}.py" ]; then
            cp -r "$cmd_dir" "$PAYLOAD_DIR$INSTALL_ROOT/"
        fi
    fi
done

# Copy GUI
cp -r "$PROJECT_ROOT/.gui" "$PAYLOAD_DIR$INSTALL_ROOT/"

# Build VS Code extension
echo "Building VS Code extension..."
cd "$PROJECT_ROOT/.vscode-extension"
npm install
npm run package
VSIX_FILE=$(ls -t biostool-*.vsix | head -1)
cp "$VSIX_FILE" "$BUILD_DIR/"

# Copy post-install script
cp "$SCRIPT_DIR/scripts/postinstall" "$SCRIPTS_DIR/"
chmod +x "$SCRIPTS_DIR/postinstall"

# Create uninstall script
cat > "$PAYLOAD_DIR$INSTALL_ROOT/uninstall.sh" << 'EOF'
#!/bin/bash
# Uninstall BIOS Tool

echo "Uninstalling BIOS Tool..."

# Remove symlinks
rm -f /usr/local/bin/bt
rm -f /usr/local/bin/btgui

# Remove installation directory
rm -rf /usr/local/opt/biostool

echo "BIOS Tool uninstalled successfully!"
EOF
chmod +x "$PAYLOAD_DIR$INSTALL_ROOT/uninstall.sh"

echo "Building package..."

# Build the package
pkgbuild --root "$PAYLOAD_DIR" \
         --identifier "$IDENTIFIER" \
         --version "$VERSION" \
         --scripts "$SCRIPTS_DIR" \
         --install-location "/" \
         "$BUILD_DIR/${PACKAGE_NAME}-${VERSION}.pkg"

echo ""
echo "Build successful!"
echo "Package: $BUILD_DIR/${PACKAGE_NAME}-${VERSION}.pkg"

# Show file size
ls -lh "$BUILD_DIR/${PACKAGE_NAME}-${VERSION}.pkg" | awk '{print "Size:", $5}'
