# Contributing to BIOS Tool (BT)

Thank you for your interest in contributing to the BIOS Tool project! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Code Style Guidelines](#code-style-guidelines)
- [Project Structure](#project-structure)
- [Version Management](#version-management)

## Code of Conduct

This project follows standard open-source community guidelines. Be respectful, constructive, and professional in all interactions.

## Getting Started

### Prerequisites

- Python 3.6 or higher
- Git
- (Optional) Virtual environment tool (venv, conda, etc.)
- (Windows) PowerShell or Command Prompt
- (Linux) Bash shell

### First-Time Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/bt.git
   cd bt
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # Linux/macOS
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Test your installation:**
   ```bash
   python bt.py --help
   ```

## Development Setup

### Project Components

The BT project has three main components:

1. **Base CLI Tool** (root directory) - Core command-line functionality
2. **GUI Tool** (`.gui/`) - Tkinter-based graphical interface
3. **VS Code Extension** (`.vscode-extension/`) - Visual Studio Code integration

### Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following the guidelines below

3. Test your changes (see [Testing](#testing))

4. Commit with descriptive messages

5. Push to your fork and submit a pull request

## Making Changes

### Adding a New Command

1. **Create command directory:**
   ```bash
   mkdir <command-name>
   cd <command-name>
   ```

2. **Create required files:**
   - `<command-name>.py` - Implementation
   - `terse.txt` - One-line description
   - `details.txt` - Detailed help text
   - `needs.vcs` - (Optional) If command requires Git

3. **Implement command logic:**
   ```python
   # <command-name>.py
   import run
   import logger
   
   def execute(args):
       """Execute the command.
       
       Args:
           args: Parsed command-line arguments
           
       Returns:
           int: Exit code (0 for success, non-zero for error)
       """
       logger.info(f"Executing {args.command}")
       
       # Your implementation here
       
       return 0  # Success
   ```

4. **Test the command:**
   ```bash
   python bt.py <command-name> --help
   python bt.py <command-name>
   ```

### Modifying Core Modules

When modifying core modules (`run.py`, `vcs.py`, `data.py`, etc.):

1. **Update the module** in the root directory

2. **Sync to VS Code extension:**
   ```bash
   # Copy to extension's bundled tool
   cp <module>.py .vscode-extension/bt-tool/<module>.py
   ```

3. **Test both standalone and extension usage**

### Updating Documentation

- **README.md** - User-facing documentation
- **CHANGELOG.md** - Version history (use Keep a Changelog format)
- **docs/** - Developer documentation
- **Command help** - Update `terse.txt` and `details.txt`

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit/
pytest tests/integration/

# Run with coverage
pytest --cov=. --cov-report=html

# View coverage report
# Open htmlcov/index.html in browser
```

### Writing Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Use fixtures from `tests/conftest.py`
- Follow naming convention: `test_<functionality>()`

Example:
```python
def test_config_get_existing_key(temp_config):
    """Test retrieving an existing configuration key."""
    # Arrange
    set('TEST_KEY', 'test_value')
    
    # Act
    result = get('TEST_KEY')
    
    # Assert
    assert result == 'test_value'
```

### Manual Testing

Test on both platforms when possible:
- Windows (PowerShell, Command Prompt)
- Linux (Bash)

## Submitting Changes

### Pull Request Process

1. **Verify version consistency:**
   ```bash
   python scripts/verify-version.py
   ```

2. **Run tests:**
   ```bash
   pytest
   ```

3. **Update CHANGELOG.md** with your changes

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Add feature: brief description"
   ```

5. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request** on GitHub

### Pull Request Checklist

- [ ] Code follows style guidelines (see below)
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version consistency verified
- [ ] Tested on target platforms (Windows/Linux)
- [ ] No merge conflicts with main branch
- [ ] Descriptive PR title and description

## Code Style Guidelines

### Python Style

Follow **PEP 8** with these specifics:

- **Line length:** 100 characters (not strict 79)
- **Indentation:** 4 spaces (no tabs)
- **Imports:** Group stdlib, third-party, local
- **Docstrings:** Google or NumPy style
- **Type hints:** Encouraged but not required

### Code Organization

```python
# Module-level docstring
"""Brief module description.

Detailed explanation if needed.
"""

# Imports
import os
import sys
from pathlib import Path

import third_party

import run
import logger

# Constants
DEFAULT_VALUE = 42

# Functions
def public_function(arg: str) -> int:
    """Brief description.
    
    Args:
        arg: Description of argument
        
    Returns:
        Description of return value
    """
    return 0

# Private helpers
def _private_helper():
    """Private functions start with underscore."""
    pass
```

### Error Handling

- Return error codes (0=success, 1=error)
- Don't use `sys.exit()` in library code
- Provide meaningful error messages
- Log errors at appropriate level

```python
def execute(args):
    try:
        # Operation
        result = perform_action()
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1
    
    return 0
```

### Logging

Use the `logger` module:
- **ERROR**: Critical failures
- **WARNING**: Important but non-fatal issues
- **INFO**: High-level operation progress
- **DEBUG**: Detailed diagnostic information
- **TRACE**: Very detailed debug output

```python
logger.error("Failed to connect to server")
logger.warning("Using default configuration")
logger.info("Building BIOS...")
logger.debug(f"Processing file: {filename}")
logger.trace(f"Variable value: {var}")
```

## Project Structure

```
bt/
├── bt.py                    # Main entry point
├── run.py                   # Command dispatcher
├── vcs.py                   # Version control services
├── data.py                  # Configuration management
├── logger.py                # Logging framework
├── <command>/               # Command directories
│   ├── <command>.py
│   ├── terse.txt
│   ├── details.txt
│   └── needs.vcs (optional)
├── .gui/                    # GUI tool
├── .vscode-extension/       # VS Code extension
├── installers/              # Installer scripts
├── scripts/                 # Utility scripts
├── tests/                   # Test suite
├── docs/                    # Documentation
└── README.md
```

## Version Management

### Automated Version Updates

Use the version bump script:
```bash
python scripts/bump-version.py 1.2.0
```

This updates:
- README.md
- .vscode-extension/package.json
- installers/windows/biostool.iss
- installers/linux/debian/changelog

### Commit Messages

Follow this format:

- **Version bumps:** `V1.2.0: Brief description`
- **Features:** `Add support for new feature`
- **Fixes:** `Fix issue with command execution`
- **Docs:** `Update installation instructions`
- **Refactor:** `Refactor configuration system`
- **Tests:** `Add tests for data module`

### Changelog Format

Follow [Keep a Changelog](https://keepachangelog.com/):

```markdown
## [1.2.0] - 2026-01-28

### Added
- New feature description

### Changed
- Modification description

### Fixed
- Bug fix description
```

## Building Installers

### Windows Installer

Prerequisites:
- Inno Setup 6+
- Node.js/npm

Build:
```powershell
cd installers/windows
.\build-installer.ps1
```

### Linux Installer

Prerequisites:
- dpkg-dev, debhelper
- Node.js/npm
- python3-tk

Build:
```bash
cd installers/linux
./build-deb.sh
```

## Getting Help

- **Questions:** Open a GitHub Discussion
- **Bugs:** Open a GitHub Issue
- **Security:** Email maintainers directly

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to BIOS Tool!
