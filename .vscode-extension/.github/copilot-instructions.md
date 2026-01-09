# BIOS Tool VS Code Extension

## ✅ Project Complete

VS Code extension for integrating HPE Server BIOS Tool (bt) into Visual Studio Code.

## Key Changes from Original Plan

**Workspace Detection**: Extension activates on UEFI development workspaces (with `hpbuild.bat` or `hpbuild.sh`), NOT on bt.py presence

**Bundled BT Tool**: BT Python scripts are bundled WITH the extension in `bt-tool/` directory - no separate installation required!

## Features Implemented

✅ **Auto-bundling** - `npm run bundle-bt` copies BT files into extension
✅ **Tree view** for BIOS platforms from PlatformPkg.dsc
✅ **Status bar** showing current platform
✅ **Command palette** integration (Build, Clean, Status, Switch)
✅ **Progress notifications** during builds
✅ **Output channel** for command execution
✅ **Problem matching** for errors/warnings

## Quick Start

1. **Bundle BT Tool**: `npm run bundle-bt`
2. **Compile**: `npm run compile`
3. **Test**: Press `F5` to launch Extension Development Host
4. **Open** a UEFI workspace (with hpbuild.bat/hpbuild.sh)

## How It Works

- Extension looks for bundled `bt-tool/bt.py` or `bt-tool/bt.ps1`
- Falls back to PATH if bt is separately installed
- Discovers platforms by searching for `PlatformPkg.dsc` files
- Parses `local.txt` to show current active platform
- Executes bt commands and streams output to VS Code

## Files Structure

```
.vscode-extension/
├── bt-tool/              ← Bundled BT scripts
│   ├── bt.py
│   ├── bt.ps1
│   └── [command modules]
├── src/
│   ├── extension.ts      ← Main activation
│   ├── platformProvider.ts   ← Tree view
│   ├── btRunner.ts       ← Command execution
│   └── statusBar.ts      ← Status bar
└── bundle-bt.ps1         ← Bundling script
```

## Next Steps

- Test with real UEFI workspace
- Add more bt commands
- Enhance error parsing
- Add extension icon
- Publish to marketplace
