#!/bin/bash
# Build BT GUI standalone executable for Linux

echo "Building BT GUI standalone executable for Linux..."

# Check PyInstaller
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# Clean previous builds
rm -rf build dist

# Build with PyInstaller
echo "Running PyInstaller..."
pyinstaller btgui.spec --clean

if [ $? -eq 0 ]; then
    echo ""
    echo "Build successful!"
    echo "Executable: $(pwd)/dist/btgui"
    
    # Show file size
    size=$(du -h dist/btgui | cut -f1)
    echo "Size: $size"
    
    # Make executable
    chmod +x dist/btgui
else
    echo ""
    echo "Build failed!"
    exit 1
fi
