# Changelog

All notable changes to BIOS Tool (BT) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-01-28

### Added
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
  - Question template
  - Pull request template with checklist
- **CONTRIBUTING.md**
  - Comprehensive contributor guidelines
  - Development setup instructions
  - Code style standards
  - Testing guidelines
  - Pull request process
- **Code Quality Standards**
  - .editorconfig for consistent formatting
  - .gitattributes for line ending consistency
  - Flake8, Black, isort integration
  - Security scanning with Bandit
  - Dependency safety checks

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
- Windows Installer: `installers/windows/output/BIOSTool-1.0.0-Setup.exe`
- Linux Installer: `installers/linux/build/biostool_1.0.0-1_all.deb`

## Version Format

- **Major.Minor.Patch** (e.g., 1.0.0)
- Major: Breaking changes
- Minor: New features, backward compatible
- Patch: Bug fixes, backward compatible
