#!/bin/bash
# Convert biostool.ico to macOS .icns format
# Requires ImageMagick

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ICO_FILE="$SCRIPT_DIR/../../.gui/biostool.ico"
ICONSET_DIR="$SCRIPT_DIR/biostool.iconset"
ICNS_FILE="$SCRIPT_DIR/../../.gui/biostool.icns"

if [ ! -f "$ICO_FILE" ]; then
    echo "Error: biostool.ico not found at $ICO_FILE"
    exit 1
fi

# Check for ImageMagick
if ! command -v convert &> /dev/null; then
    echo "Error: ImageMagick is required. Install with: brew install imagemagick"
    exit 1
fi

echo "Creating iconset directory..."
mkdir -p "$ICONSET_DIR"

# Extract and convert to required sizes for macOS
convert "$ICO_FILE" -resize 16x16 "$ICONSET_DIR/icon_16x16.png"
convert "$ICO_FILE" -resize 32x32 "$ICONSET_DIR/icon_16x16@2x.png"
convert "$ICO_FILE" -resize 32x32 "$ICONSET_DIR/icon_32x32.png"
convert "$ICO_FILE" -resize 64x64 "$ICONSET_DIR/icon_32x32@2x.png"
convert "$ICO_FILE" -resize 128x128 "$ICONSET_DIR/icon_128x128.png"
convert "$ICO_FILE" -resize 256x256 "$ICONSET_DIR/icon_128x128@2x.png"
convert "$ICO_FILE" -resize 256x256 "$ICONSET_DIR/icon_256x256.png"
convert "$ICO_FILE" -resize 512x512 "$ICONSET_DIR/icon_256x256@2x.png"
convert "$ICO_FILE" -resize 512x512 "$ICONSET_DIR/icon_512x512.png"
convert "$ICO_FILE" -resize 1024x1024 "$ICONSET_DIR/icon_512x512@2x.png"

echo "Converting to .icns format..."
iconutil -c icns "$ICONSET_DIR" -o "$ICNS_FILE"

echo "Cleaning up..."
rm -rf "$ICONSET_DIR"

echo "Created: $ICNS_FILE"
