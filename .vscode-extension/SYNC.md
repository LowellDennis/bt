# Auto-Syncing BT Tool

The extension bundles a copy of the BT Python scripts. This ensures users without a system-installed version can still use all features.

## Manual Sync

To manually sync the latest BT tool:

```bash
npm run bundle-bt
```

## Auto-Sync (Development)

For active development, enable auto-sync to automatically re-bundle whenever Python files change:

```bash
npm run sync-bt
```

This watches the parent directory (`../`) for changes to `.py` files and automatically re-bundles them into `bt-tool/`.

**Note:** Auto-sync includes a 2-second debounce to avoid excessive rebuilds during rapid changes.

## How It Works

1. **`bundle-bt.ps1`** - Copies Python files from parent directory to `bt-tool/`
2. **`sync-bt.ps1`** - Watches for file changes and triggers `bundle-bt.ps1`
3. **`vscode:prepublish`** - Automatically bundles before publishing to marketplace

## Structure

```
bt/                          ← Main BT tool repository
└── .vscode-extension/       ← Extension project
    ├── bt-tool/             ← Bundled copy (auto-synced)
    ├── bundle-bt.ps1        ← Manual bundler
    └── sync-bt.ps1          ← Auto-sync watcher
```

## Version Tracking

The bundled version shows in [bt.py](bt-tool/bt.py) as `BIOS Tool V0.7`.

When the main tool updates its version, re-bundle to pick up changes:
- New commands
- New options (e.g., `/itp`)
- Bug fixes
- Format changes (e.g., progress output)
