# BIOS Tool (BT) - GitHub Copilot Instructions

## Project Overview

BIOS Tool (BT) is a command-line tool for working with HPE Server BIOS source code. It simplifies BIOS development workflows by providing a unified interface for common operations like building, configuration management, version control integration, and Git worktree management.

**Current Version:** V1.0.0

---

## Architecture & Component Hierarchy

### 1. Base CLI Tool (Root Directory)

#### Purpose
Core command-line interface providing all BT functionality. This is a **collection of Python scripts**, not a formal Python package.

#### Structure
```
bt.py               # Main entry point (Python)
bt.cmd              # Windows batch wrapper
bt.ps1              # PowerShell wrapper
bt.sh               # Linux/macOS shell wrapper
run.py              # Command dispatcher
command.py          # Command loader/executor
cmdline.py          # Argument parser
<command>/          # Command subdirectories
  <command>.py      # Command implementation
  terse.txt         # Exactly one line: what the command does (no options)
  details.txt       # Detailed help text with usage and options
  needs.vcs         # (optional) VCS requirement marker
```

#### Key Modules
- **run.py**: Main dispatcher, handles command discovery and execution
- **vcs.py**: Version control services (Git operations)
- **logger.py**: Logging framework with verbosity levels
- **data.py**: Configuration and data persistence
- **misc.py**: Utility functions
- **evaluate.py**: Expression evaluator for config variables
- **announce.py**: User notification system
- **cmdline.py**: Command-line argument processing
- **command.py**: Command loading and validation
- **error.py**: Error handling and exit codes

#### Command Implementation Pattern
When adding/modifying commands:
1. Create directory named after command (e.g., `build/`)
2. Add `<command>.py` with main logic
3. Add `terse.txt` with exactly one line describing what the command does (no options/arguments)
4. Add `details.txt` with detailed help including usage examples, options, and arguments
5. If command needs VCS, add empty `needs.vcs` file
6. Import necessary modules: `run`, `vcs`, `logger`, `data`, `misc`
7. Follow error handling pattern: return error codes, don't use `sys.exit()`

#### Important Implementation Notes
- **Not a Python package**: Don't require setup.py or formal installation
- **Script collection**: Each command is independently executable
- **No dependencies between commands**: Commands should be loosely coupled
- **Shared services**: Use `run.py`, `vcs.py`, etc. for common functionality

#### Coding Standards for CLI
- Use Python 3.6+ features
- Follow PEP 8 style guide
- Keep functions focused and single-purpose
- Add docstrings to all public functions
- Use type hints where appropriate
- Handle errors gracefully with meaningful messages
- Log important operations at appropriate verbosity levels

---

### 2. GUI Tool (`.gui/` Directory)

#### Purpose
Tkinter-based graphical interface providing visual access to BT commands and configuration.

#### Structure
```
.gui/
  btgui.py          # Main GUI application
```

#### Key Features
- Visual command execution interface
- Configuration editor
- Status display
- Integration with base tool via subprocess calls

#### Implementation Guidelines
- **Tkinter dependency**: Requires `python3-tk` on Linux
- **Subprocess execution**: Calls `bt.py` commands, doesn't import them
- **Error handling**: Display errors in GUI dialogs
- **Configuration**: Read/write using `data.py` patterns
- **Platform compatibility**: Test on Windows and Linux

#### Coding Standards for GUI
- Use Tkinter best practices
- Implement proper event handling
- Provide clear user feedback
- Handle long-running operations with progress indicators
- Graceful degradation if base tool is unavailable

---

### 3. VS Code Extension (`.vscode-extension/` Directory)

#### Purpose
Full-featured VS Code extension providing command palette integration, configuration UI, and IntelliSense.

#### Structure
```
.vscode-extension/
  package.json              # Extension manifest
  extension.js              # Extension entry point
  bt-tool/                  # BUNDLED COPY of base tool
    (mirrors root structure)
```

#### Critical Synchronization Rule
**The `.vscode-extension/bt-tool/` directory contains a complete copy of the base CLI tool that MUST be kept in sync with the root.**

When modifying base tool files, sync these to `.vscode-extension/bt-tool/`:
- `run.py`, `vcs.py`, `logger.py`, `data.py`, `misc.py`, `evaluate.py`
- `announce.py`, `cmdline.py`, `command.py`, `error.py`
- All command subdirectories used by extension
- Entry point scripts: `bt.py`, `bt.cmd`, `bt.ps1`, `bt.sh`

#### Extension Development Guidelines
- **Node.js/npm**: Use standard VS Code extension development
- **Python integration**: Execute bundled `bt-tool/bt.py` via child_process
- **Command registration**: Register all BT commands in `package.json`
- **Configuration UI**: Provide webview-based config editor
- **Testing**: Test with bundled tool, not system-installed version

#### Build Process
1. Build with: `npm install && npm run package`
2. Produces: `biostool-X.Y.Z.vsix`
3. Install to VS Code: `code --install-extension biostool-X.Y.Z.vsix`

#### Coding Standards for Extension
- Follow VS Code extension API guidelines
- Use TypeScript/JavaScript ES6+
- Implement proper activation events
- Handle errors with VS Code notifications
- Test on Windows and Linux

---

## Version Management System

### Automated Versioning (V1.0+)

**Use the automated scripts for version management:**

#### Bump Version
```bash
python scripts/bump-version.py <new-version>
# Example: python scripts/bump-version.py 1.1.0
```

Updates all version references:
- `README.md` - Version string and history table
- `.vscode-extension/package.json` - Extension version
- `installers/windows/biostool.iss` - Windows installer version
- `installers/linux/debian/changelog` - Debian package changelog

#### Verify Version Consistency
```bash
python scripts/verify-version.py
```

Checks that all files have matching versions. Use in CI/CD and pre-commit hooks.

### Manual Version Update Checklist

If editing manually (not recommended):

1. **README.md** (line ~6):
   ```markdown
   * Current Version is V1.X
   ```

2. **README.md** (bottom, Version History table):
   ```markdown
   | V1.X   | Description of changes                                        |
   |        | - Bullet point details                                        |
   |--------|---------------------------------------------------------------|
   ```

3. **.vscode-extension/package.json**:
   ```json
   "version": "1.X.0"
   ```

4. **.installers/windows/biostool.iss**:
   ```ini
   #define MyAppVersion "1.X.0"
   ```

5. **.installers/linux/debian/changelog**:
   ```
   biostool (1.X.0-1) stable; urgency=low
   ```

6. **CHANGELOG.md**:
   Add new version section following Keep a Changelog format

7. **Sync VS Code extension's bundled tool**

### Version Format

- Use semantic versioning: `MAJOR.MINOR.PATCH`
- Tag releases: `git tag -a V1.0.0 -m "Version 1.0.0"`
- Update CHANGELOG.md with every version

---

## Building & Installation

### Windows Installer

**Prerequisites:**
- Inno Setup 6+
- Node.js/npm (for VS Code extension)
- Python 3.6+

**Build Process:**
```powershell
cd .installers/windows
.\build-installer.ps1
```

**Output:** `.installers/windows/output/BIOSTool-X.Y.Z-Setup.exe`

**What It Installs:**
- Base CLI tool → `C:\Program Files\BIOSTool\`
- GUI tool → `C:\Program Files\BIOSTool\.gui\`
- Python (if not present) → Embedded Python
- VS Code extension (if VS Code detected)

**Inno Setup Script (`biostool.iss`):**
- Uses preprocessor for version: `#define MyAppVersion "1.0.0"`
- Auto-detects VS Code installation
- Creates Start Menu shortcuts
- Adds to PATH

### Linux Installer (Debian Package)

**Prerequisites:**
- `dpkg-dev`, `debhelper` (NOT `dh-python`)
- Node.js/npm (for VS Code extension)
- Python 3.6+
- `python3-tk` (for GUI)

**Build Process:**
```bash
cd .installers/linux
./build-deb.sh
```

**Can build on Windows via WSL:**
```powershell
wsl -d Ubuntu -- bash -c "cd /mnt/d/path/to/bt/.installers/linux && ./build-deb.sh"
```

**Output:** `.installers/linux/build/biostool_X.Y.Z-1_all.deb`

**What It Installs:**
- Base CLI tool → `/opt/biostool/`
- GUI tool → `/opt/biostool/.gui/`
- GUI wrapper → `/usr/local/bin/btgui`
- VS Code extension (if VS Code detected)
- Symlink → `/usr/local/bin/bt`

**Debian Package Structure:**
- `debian/control`: Dependencies (python3, python3-tk)
- `debian/rules`: Build instructions (uses `dh` without `pybuild`)
- `debian/changelog`: Version history
- `debian/postinst`: Post-installation script (installs extension)

**Important:** BT is NOT a Python package, so we don't use `pybuild`. The `debian/rules` file manually copies files.

---

## Testing Strategy

### Current State
- Manual testing only
- No automated test suite yet

### Future Testing Framework (Planned)
- **Unit tests**: `pytest` for individual modules
- **Integration tests**: Command execution tests
- **GUI tests**: `pytest-qt` or similar
- **Extension tests**: VS Code extension test framework
- **Installer tests**: Verify installations on clean VMs

### Testing Guidelines
When adding tests:
- Place in `tests/` directory
- Mirror source structure
- Test both success and failure paths
- Mock VCS operations where appropriate
- Test cross-platform compatibility

---

## Documentation Hierarchy

### User Documentation

#### README.md
- Primary entry point for users
- Installation instructions
- Quick start guide
- Command reference
- Version history

#### CHANGELOG.md
- Detailed version history
- Follows Keep a Changelog format
- Categories: Added, Changed, Deprecated, Removed, Fixed, Security

#### Command Help Files
- `<command>/terse.txt`: Exactly one line describing what the command does (typically no mention of options/arguments)
- `<command>/details.txt`: Detailed usage examples, options, arguments, and behavior

### Developer Documentation

#### .installers/README.md
- Installer build instructions
- Prerequisites
- Platform-specific notes
- Troubleshooting

#### .github/copilot-instructions.md (This File)
- Architecture overview
- Development guidelines
- Coding standards
- Process documentation

### API Documentation (Future)
- Auto-generated from docstrings
- Module reference
- Command developer guide

---

## Git Workflow & VCS Integration

### Branch Strategy
- `main`: Stable releases
- Feature branches: `feature/<name>`
- Release tags: `V1.0.0` format

### Commit Guidelines
- **Version bumps**: `V1.X.0: Description`
- **Features**: `Add <feature>`
- **Fixes**: `Fix <issue>`
- **Docs**: `Update <documentation>`
- **Refactor**: `Refactor <component>`

### VCS Module (`vcs.py`)
Provides Git operations for BT commands:
- Repository detection
- Worktree management
- Branch operations
- Status queries
- Commit/push operations

When adding VCS operations:
- Check for Git availability first
- Handle errors gracefully
- Provide meaningful error messages
- Support both worktrees and standard repos

---

## CI/CD Pipeline

### GitHub Actions Workflows

#### Build Installers (`.github/workflows/build-installers.yml`)
**Triggers:** Push to tags matching `V*`

**Jobs:**
1. **Build Windows Installer**
   - Runs on: `windows-latest`
   - Installs Inno Setup
   - Builds VS Code extension
   - Builds Windows installer
   - Uploads artifact

2. **Build Linux Installer**
   - Runs on: `ubuntu-latest`
   - Installs Debian tools
   - Builds VS Code extension
   - Builds .deb package
   - Uploads artifact

3. **Create GitHub Release**
   - Creates release from tag
   - Attaches both installers
   - Extracts changelog from CHANGELOG.md

#### Version Check (`.github/workflows/version-check.yml`)
**Triggers:** Pull requests, pushes to main

**Purpose:** Verify version consistency across all files

**Process:**
- Runs `scripts/verify-version.py`
- Fails if versions don't match
- Prevents version inconsistencies

---

## Configuration System

### Configuration Files
- **global.txt**: System-wide settings
- **local.txt**: Repository-specific settings (gitignored)

### Configuration Format
```
KEY = VALUE
KEY2 = ${KEY}/subpath    # Variable expansion
```

### Key Configuration Variables
- `BIOS_SOURCE`: Path to BIOS source code
- `BUILD_TARGET`: Current build target
- `EDITOR`: Preferred text editor
- `JUMP_SERVER`: Jump station configuration

### Configuration API (`data.py`)
- `get(key)`: Retrieve configuration value
- `set(key, value)`: Set configuration value
- `expand(value)`: Expand variables in value
- `save()`: Persist configuration

---

## Jump Station System

### Purpose
Remote BIOS build infrastructure for resource-intensive builds.

### Configuration
- Jump station details in config
- SSH key management
- Build upload/download

### Commands
- `jump`: Execute commands on jump station
- `build --upload`: Build and upload to jump station

### Security
- SSH key-based authentication
- No password storage
- Configurable via `config` command

---

## Code Quality Standards

### Python Style
- **PEP 8 compliance**: Use `flake8` or `black`
- **Type hints**: Encouraged but not required
- **Docstrings**: Google or NumPy style
- **Line length**: 100 characters (not strict 79)

### File Organization
- Keep modules focused
- Avoid circular imports
- Use relative imports within commands
- Import shared services from root

### Error Handling
- Use specific exception types
- Provide context in error messages
- Log errors before raising
- Return error codes (0=success, 1=error)

### Logging
- Use `logger.py` framework
- Levels: ERROR, WARNING, INFO, DEBUG, TRACE
- Respect verbosity settings
- Don't use `print()` except for command output

---

## Platform Compatibility

### Supported Platforms
- Windows 10/11
- Ubuntu 20.04+
- Other Linux distributions (untested)
- macOS (untested)

### Platform-Specific Code
- Use `os.name` or `sys.platform` for detection
- Provide `bt.cmd`, `bt.ps1`, `bt.sh` wrappers
- Handle path separators correctly
- Test on both Windows and Linux

### Python Version
- Minimum: Python 3.6
- Recommended: Python 3.9+
- No Python 2 support

---

## Contributing Guidelines (Future)

### Development Setup
1. Clone repository
2. Install Python 3.6+
3. (Optional) Create virtual environment
4. Install dependencies: `pip install -r requirements.txt`
5. Test: `python bt.py --help`

### Making Changes
1. Create feature branch
2. Make changes
3. Test on Windows and Linux
4. Update documentation
5. Run `scripts/verify-version.py`
6. Submit pull request

### Pull Request Checklist
- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version consistency verified
- [ ] Tested on target platforms

---

## Troubleshooting

### Common Issues

#### "Command not found"
- Check PATH includes BT installation
- On Windows: Restart terminal after installation
- On Linux: Run `hash -r` or restart terminal

#### "Python not found"
- Windows installer includes Python
- Linux: Install `python3` package
- Check `python3 --version`

#### GUI doesn't start
- Linux: Install `python3-tk`
- Windows: Reinstall with Python option enabled

#### VS Code extension not working
- Verify installation: `code --list-extensions | grep biostool`
- Check Python is available
- Check workspace has BT configuration

#### Build failures
- Check prerequisites installed
- Windows: Verify Inno Setup in PATH
- Linux: Install `dpkg-dev`, `debhelper`

---

## Future Enhancements

### Planned Features
- Automated testing framework
- Documentation website
- GUI standalone packaging
- macOS installer
- Additional VCS providers (beyond Git)

### Maintenance Tasks
- Keep dependencies updated
- Monitor Python 3.x compatibility
- Review and update documentation
- Process user feedback

---

## Quick Reference

### Key Commands
- `bt init`: Initialize BT configuration
- `bt config`: Edit configuration
- `bt build`: Build BIOS
- `bt status`: Show repository status
- `bt worktrees`: Manage Git worktrees

### Important Files
- `run.py`: Main dispatcher
- `data.py`: Configuration manager
- `vcs.py`: Git operations
- `README.md`: User documentation
- `CHANGELOG.md`: Version history

### Build Outputs
- Windows: `.installers/windows/output/*.exe`
- Linux: `.installers/linux/build/*.deb`
- Extension: `.vscode-extension/*.vsix`

### Scripts
- `.scripts/bump-version.py`: Update version everywhere
- `.scripts/verify-version.py`: Check version consistency
- `.installers/windows/build-installer.ps1`: Build Windows installer
- `.installers/linux/build-deb.sh`: Build Linux installer
