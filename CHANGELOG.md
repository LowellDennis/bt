# Changelog

All notable changes to BIOS Tool (BT) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-01-28

### Added
- **GUI Modularization**
  - Refactored btgui.py (2906 lines) into focused modules
  - widgets/console.py - InteractiveConsole (407 lines)
  - widgets/workspace_tab.py - WorkspaceTab (490 lines)
  - core/workspace_discovery.py - Repository discovery (252 lines)
  - ui/main_window.py - Main window (1722 lines)
  - btgui.py - Minimal entry point (90 lines)
  - Improved maintainability and code navigation
- **Icon Integration**
  - Window icon support for GUI (upper left corner)
  - Taskbar icon support (Windows, Linux, macOS)
  - Windows installer icon integration
  - Linux desktop entry with icon (.desktop file)
  - macOS .icns format support
  - Icon converter script for macOS
- **Comprehensive Test Suite for evaluate.py**
  - 58 comprehensive tests covering all operators and edge cases
  - Tests for arithmetic, bitwise, logical, and comparison operators
  - Parentheses and precedence tests
  - Variable and constant handling tests
  - Real-world use case tests
- **Comprehensive Documentation Website** (Sphinx-based)
  - Getting started guide
  - Complete command reference
  - Configuration guide
  - Development guide
  - API documentation structure
  - Auto-deployment to GitHub Pages
- **GUI Standalone Packaging** (PyInstaller)
  - Windows and Linux build scripts
  - ~50-100MB standalone executables
  - No Python installation required for end users
- **Pre-commit Hooks System**
  - Version consistency checks before commits
  - Quick test runs on pre-commit
  - Full test suite on pre-push
  - Installation scripts for Windows and Linux
- **Code Coverage Infrastructure**
  - Codecov integration
  - Multi-platform testing (Windows, Linux)
  - Multi-Python version support (3.8, 3.9, 3.10, 3.11)
  - Coverage badges in README
- **macOS Installer Support**
  - .pkg package builder
  - .dmg disk image builder
  - Auto-install VS Code extension
  - Uninstall script included
- **Project Organization**
  - Testing framework with pytest
  - Unit and integration test templates
  - Shared test fixtures (conftest.py)
  - Documentation directory structure
- **GitHub Templates**
  - Bug report template
  - Feature request template

### Changed
- GUI architecture improved with modular design
- Import strategy changed to absolute imports for better compatibility
  - Question template
  - Pull request template with checklist
- **CONTRIBUTING.md**
  - Comprehensive contributor guidelines
  - Development setup instructions
  - Code style standards

### Changed
- **Refactored evaluate.py** (252 lines saved, ~40% reduction)
  - Reduced from 636 lines to 384 lines using data-driven operator registry
  - Replaced 28+ operator classes with unified Operator class and registry pattern
  - Uses Python's standard `operator` module for built-in operations
  - Fixed OpBitwiseInvert bug (was evaluating operand twice)
  - Fixed OpLogicalNot bug (was evaluating operand twice)
  - Fixed bitwise operations (now properly converts floats to ints)
  - Fixed parentheses evaluation (nested parentheses now work correctly)
  - Fixed quoted boolean handling ("TRUE" remains string, TRUE becomes boolean)
  - Eliminated all SyntaxWarnings (now uses raw strings)
  - All 58 tests passing (56 passed + 2 xpassed for fixed bugs)
- **Directory Structure Optimization**
  - Renamed `docs/` → `.docs/` for faster command discovery
  - Renamed `tests/` → `.tests/` for faster command discovery
  - Renamed `packaging/` → `.packaging/` for faster command discovery
  - Renamed `scripts/` → `.scripts/` for faster command discovery
  - Renamed `installers/` → `.installers/` for faster command discovery
  - Updated all references across documentation, scripts, and CI/CD workflows
  - bt.py now skips directories with `.` prefix during command scanning
- **Documentation Improvements**
  - Clarified `terse.txt` must be exactly one line (no options mentioned)
  - Simplified README.md to reference CHANGELOG.md instead of duplicating version history
  - Updated all documentation to reflect new directory structure
  - Testing guidelines
  - Pull request process
- **Code Quality Standards**
  - .editorconfig for consistent formatting
  - .gitattributes for line ending consistency
  - Flake8, Black, isort integration
  - Security scanning with Bandit
  - Dependency safety checks

### Removed
- **Cleaned up .history directories** (~74 MB saved)
  - Removed .history/ (280 files, 13.17 MB)
  - Removed .gui/.history/ (376 files, 29.83 MB)
  - Removed .vscode-extension/.history/ (64 files, 1.39 MB)
  - Added .history/ patterns to .gitignore to prevent future accumulation

### Changed
- **Enhanced CI/CD Workflows**
  - Automated testing workflow
  - Code quality checks (linting, formatting, security)
  - Documentation build and deployment
  - Dependency update monitoring
- **Version Management**
  - Automated version bump script
  - Version consistency verification script
  - All version references now centrally managed
- **README Improvements**
  - Added status badges (tests, coverage, code quality)
  - Added Python version badge
  - Improved documentation links

### Infrastructure
- Complete test infrastructure ready for implementation
- Pre-commit hooks to catch issues early
- Professional development workflow established
- Multi-platform installer support (Windows, Linux, macOS)

## [1.0.0] - 2026-01-28

### Added
- **Jump Station Redesign**: Mapped drive + RDP workflow (no SSH required)
  - Hash-based incremental sync (only changed files transferred)
  - PowerShell script to configure jump server settings
  - Automatic COM port detection for Intel ITP debugging
- **Worktrees Command**: List all git worktrees with detailed information (branch, commit, status)
- **Linux Installer Improvements**:
  - Added GUI application (`btgui` command)
  - Added VS Code extension to package
  - Removed pybuild dependency (now uses direct file copying)
  - Added python3-tk dependency for GUI support
- **Installer Documentation**: Comprehensive build and troubleshooting guides
- **Auto-sync for VS Code Extension**: Watch mode for automatic bundling during development
- **First-run Experience**: Automatic repository selection prompts when no repos attached
- **SVN Support Documentation**: Documented Subversion compatibility

### Changed
- **Command Renames** (breaking changes):
  - `destroy` → `remove` (delete a worktree)
  - `switch` → `use` (change active worktree)
  - `clean` → `cleanup` (clean build artifacts)
  - `pull` → `fetch` (update from remote)
- **Improved Table Formatting**: Better alignment and readability across all commands
- **GUI Improvements**:
  - Split-button Jump control for sync/open actions
  - Compact button labels for better layout
  - Centered window positioning on startup
  - Unicode encoding fixes
- **Build Process**: Streamlined installer builds with proper artifact management

### Fixed
- Windows installer now correctly bundles all three components (CLI, GUI, VS Code extension)
- Linux installer debian/rules now uses proper TAB characters (required by Make)
- VS Code extension bundled tool directory now properly ignored in git
- Build artifacts properly excluded from version control

## [0.9.0] - 2025

### Added
- Linux and macOS support
- Cross-platform shell script launcher (`bt.sh`)

### Fixed
- Various bug fixes for cross-platform compatibility

## [0.8.0] - 2025

### Changed
- GUI improvements and refinements

## [0.7.0] - 2025

### Added
- Windows installer (Inno Setup)
- Linux Debian package installer
- Automated installer build scripts

## [0.6.0] - 2024

### Added
- VS Code extension with command palette integration
- Interactive configuration UI
- Intel ITP debugger support via Jump Station

## [0.5.0] - 2024

### Added
- Build progress tracking with real-time updates
- Progress percentage display during compilation

## [0.4.0] - 2024

### Added
- Enhanced help system with command-specific documentation
- Wake lock to prevent system sleep during builds
- BMC upload support for firmware deployment

### Changed
- Improved command documentation structure

## [0.3.0] - 2024

### Fixed
- Various bug fixes and stability improvements

## [0.2.0] - 2024

### Added
- Team release with collaborative features

### Fixed
- Git worktree handling improvements
- Path resolution fixes

## [0.1.0] - 2024

### Added
- Initial release
- Core command-line tool
- Basic git worktree support
- Build and clean commands
- Configuration management
- Build completion notifications via SMS/email

---

## Release Links

- [1.0.0] - Current release
- Windows Installer: `.installers/windows/output/BIOSTool-1.0.0-Setup.exe`
- Linux Installer: `.installers/linux/build/biostool_1.0.0-1_all.deb`

## Version Format

- **Major.Minor.Patch** (e.g., 1.0.0)
- Major: Breaking changes
- Minor: New features, backward compatible
- Patch: Bug fixes, backward compatible
