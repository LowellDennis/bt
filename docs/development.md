# Development Guide

Guide for developers contributing to BIOS Tool (BT).

## Development Setup

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed setup instructions.

### Quick Start

```bash
# Clone repository
git clone https://github.com/YOUR_ORG/bt.git
cd bt

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest
```

## Architecture

### Component Overview

```
bt/
├── bt.py              # Main entry point
├── run.py             # Command dispatcher
├── vcs.py             # Git operations
├── data.py            # Configuration
├── logger.py          # Logging
├── <command>/         # Command modules
├── .gui/              # GUI application
└── .vscode-extension/ # VS Code extension
```

### Command Execution Flow

1. User runs `bt <command> [args]`
2. `bt.py` calls `run.main()`
3. `run.py` discovers and loads command module
4. Command's `execute()` function is called
5. Result is returned to user

### Adding a New Command

See [CONTRIBUTING.md](../CONTRIBUTING.md#adding-a-new-command) for detailed instructions.

## Testing

### Running Tests

```bash
# All tests
pytest

# Specific tests
pytest tests/unit/test_data.py
pytest tests/integration/

# With coverage
pytest --cov=. --cov-report=html
```

### Writing Tests

Use fixtures from `tests/conftest.py`:

```python
def test_config_in_temp_dir(temp_config):
    """Test configuration with temporary files."""
    # temp_config provides isolated config files
    pass

def test_git_operations(mock_git_repo):
    """Test Git operations in mock repository."""
    # mock_git_repo provides a test Git repository
    pass
```

## Code Style

### Python Style Guide

- Follow PEP 8
- Line length: 100 characters
- Use 4 spaces for indentation
- Add docstrings to all public functions
- Use type hints where appropriate

### Running Linters

```bash
# Check style
flake8 .

# Auto-format
black .
```

## Building Installers

### Windows Installer

```powershell
cd installers/windows
.\build-installer.ps1
```

### Linux Installer

```bash
cd installers/linux
./build-deb.sh
```

### VS Code Extension

```bash
cd .vscode-extension
npm install
npm run package
```

## Version Management

### Bumping Version

```bash
# Update to new version
python scripts/bump-version.py 1.1.0

# Verify consistency
python scripts/verify-version.py

# Tag release
git tag -a V1.1.0 -m "Version 1.1.0"
git push origin V1.1.0
```

## Debugging

### Enable Verbose Logging

```bash
bt <command> -v      # Verbose
bt <command> -vv     # Very verbose
bt <command> -vvv    # Trace level
```

### Python Debugger

```python
import pdb; pdb.set_trace()
```

### VS Code Debugging

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "BT Command",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/bt.py",
      "args": ["<command>"],
      "console": "integratedTerminal"
    }
  ]
}
```

## Synchronizing VS Code Extension

When modifying core modules, sync to extension:

```bash
# Copy module to extension
cp run.py .vscode-extension/bt-tool/run.py

# Or copy entire command directory
cp -r build/ .vscode-extension/bt-tool/build/
```

## CI/CD

### GitHub Actions Workflows

- **Build Installers**: Triggered on version tags
- **Version Check**: Runs on PRs and main branch pushes
- **Tests**: Runs on all PRs

### Local CI Simulation

```bash
# Run what CI runs
python scripts/verify-version.py
pytest
flake8 .
```

## Release Process

1. Update CHANGELOG.md
2. Bump version: `python scripts/bump-version.py X.Y.Z`
3. Commit: `git commit -m "VX.Y.Z: Release description"`
4. Tag: `git tag -a VX.Y.Z -m "Version X.Y.Z"`
5. Push: `git push origin main --tags`
6. GitHub Actions builds installers automatically
7. Create GitHub Release with installers

## Common Development Tasks

### Adding a Configuration Key

1. Document in `docs/configuration.md`
2. Add default in `data.py`
3. Add to `global.txt` template

### Modifying Git Operations

1. Update `vcs.py`
2. Add tests in `tests/unit/test_vcs.py`
3. Test with real repositories
4. Update documentation

### Adding Dependencies

1. Add to `requirements.txt`
2. Update installer scripts
3. Test fresh installations
4. Document in README.md
