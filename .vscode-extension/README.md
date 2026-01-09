# BIOS Tool Integration for VS Code

VS Code extension for integrating HPE Server BIOS Tool (bt) into Visual Studio Code.

## Features

### 🌳 Platform Tree View
- Displays all BIOS platforms found in your workspace
- Shows the currently active platform
- Quick access to build and manage platforms

### 📊 Status Bar Integration
- Shows current platform in the status bar
- Click to quickly switch platforms

### ⚡ Command Palette
Access all BT commands from the command palette (`Ctrl+Shift+P`):
- **BT: Build** - Build the current platform
- **BT: Clean** - Clean build artifacts
- **BT: Status** - Show repository status
- **BT: Switch Platform** - Switch to a different platform
- **BT: Refresh Platforms** - Refresh the platform list

### 🔍 Problem Matching
Build errors and warnings automatically populate the VS Code Problems panel with clickable file links.

### 📈 Progress Tracking
Real-time build progress shown in notifications with module counts and percentage completion.

### 📝 Output Channel
Dedicated "BIOS Tool" output channel showing all command output with syntax highlighting.

## Requirements

- **VS Code 1.107.0 or higher**
- **Python 3.x** (for running bt commands)
- **UEFI development workspace** with `hpbuild.bat` or `hpbuild.sh` in the root

**Note:** The BT tool is bundled with this extension - no separate installation required!

## Usage

### Opening a BIOS Workspace
1. Open a UEFI development worktree (containing `hpbuild.bat` or `hpbuild.sh`) in VS Code
2. The extension will automatically activate and detect platforms containing `PlatformPkg.dsc`
3. The "BIOS Tool" icon will appear in the Activity Bar

### Building a Platform
**From Tree View:**
1. Click the BIOS Tool icon in the Activity Bar
2. Click the build icon (⚙) next to a platform

**From Command Palette:**
1. Press `Ctrl+Shift+P`
2. Type "BT: Build"
3. Press Enter

### Switching Platforms
**From Status Bar:**
1. Click the platform name in the status bar
2. Select a platform from the quick pick menu

**From Command Palette:**
1. Press `Ctrl+Shift+P`
2. Type "BT: Switch Platform"
3. Select a platform

## Extension Settings

This extension does not currently contribute any VS Code settings.

## Known Issues

- Problem matching requires bt to output errors in a specific format
- Some bt commands may not be fully integrated yet

## Release Notes

### 0.0.1
Initial release with core functionality:
- Platform discovery and tree view
- Build command integration
- Status bar integration
- Basic progress tracking

---

## Development
### Building the Extension

The extension bundles the BT tool automatically. To build:

1. Bundle BT tool:
```bash
npm run bundle-bt
```

2. Compile TypeScript:
```bash
npm run compile
```

Or do both with:
```bash
npm run vscode:prepublish
```

### Testing

To run the extension in development mode:

1. Open this folder in VS Code
2. Run `npm run bundle-bt` to bundle the bt tool
3. Press `F5` to launch Extension Development Host
4. Open a UEFI workspace in the new window
5. Test the extension features

To watch for changes:
```bash
npm run watch
```

### Packaging

To create a .vsix package:
```bash
npm run vscode:prepublish
vsce package
npm run watch
```

## License

This extension is for internal HPE use.
