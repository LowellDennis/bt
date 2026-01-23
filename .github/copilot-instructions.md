# BIOS Tool (BT) - Copilot Instructions

## Project Overview

BIOS Tool (BT) is a command-line tool for working with HPE Server BIOS source code. It simplifies BIOS development workflows.

## Project Structure

This project has **three main components**:

### 1. Base BT Tool (Root Directory)
- The core command-line tool
- Main entry points: `bt.cmd` (Windows), `bt.ps1` (PowerShell), `bt.sh` (Linux/macOS), `bt.py`
- Commands are organized in subdirectories (e.g., `build/`, `clean/`, `config/`)
- Each command subdirectory contains:
  - `terse.txt` - Brief description
  - `details.txt` - Detailed description
  - `needs.vcs` - (optional) Indicates VCS services needed
  - `<command>.py` - The command implementation

### 2. GUI Tool (`.gui/` Directory)
- A graphical user interface version of the tool
- Main file: `.gui/btgui.py`

### 3. VS Code Extension (`.vscode-extension/` Directory)
- A VS Code extension providing full command support and interactive config UI
- **Contains a built-in copy of the base tool** that must be kept in sync with the root base tool
- Can be installed standalone or via the installers

## Installers

Located in `installers/` directory:

### Windows Installer (`installers/windows/`)
- Built with Inno Setup (`biostool.iss`)
- Installs: Base tool, GUI tool, Python (if needed)
- Auto-detects VS Code and installs the extension if available

### Linux Installer (`installers/linux/`)
- Debian package format
- Installs: Base tool, GUI tool
- Auto-detects VS Code and installs the extension if available

## Version Management

**IMPORTANT: When updating the version, ALL of the following must be updated:**

1. **README.md** - Update the version string (line ~6):
   ```markdown
   * Current Version is V0.X
   ```

2. **README.md** - Add an entry to the Version History table at the bottom of the file:
   ```markdown
   | V0.X   | Description of changes                                                              |
   |        | - Bullet point details                                                              |
   |--------|--------------------------------------------------------------------------------------|
   ```

3. **Sync the VS Code extension's built-in base tool** - When base tool files change, the copy in `.vscode-extension/bt-tool/` needs to be updated to match.

## Key Files to Keep in Sync

When modifying these base tool files, remember to sync to `.vscode-extension/bt-tool/`:
- `run.py`
- `vcs.py`
- `logger.py`
- `data.py`
- `misc.py`
- `evaluate.py`
- `announce.py`
- `cmdline.py`
- `command.py`
- `error.py`
- And any command subdirectories used by the extension

## Commit Guidelines

- Version bump commits should include all version-related changes
- Use format: `V0.X: Brief description of main changes`
- Include version history table updates in the same commit as version bumps
