# BIOS Tool (BT) Documentation

Welcome to the BIOS Tool (BT) documentation!

```{toctree}
:maxdepth: 2
:caption: Contents:

getting-started
commands
configuration
development
api/index
```

## Overview

BIOS Tool (BT) is a command-line tool for working with HPE Server BIOS source code. It simplifies BIOS development workflows by providing a unified interface for common operations.

### Key Features

- **Command-line Interface**: Powerful CLI for BIOS development tasks
- **GUI Application**: Optional graphical interface
- **VS Code Extension**: Full integration with Visual Studio Code
- **Git Integration**: Built-in support for Git worktrees and version control
- **Jump Station Support**: Remote build infrastructure integration
- **Cross-platform**: Windows and Linux support

### Quick Links

- [Getting Started](getting-started.md)
- [Command Reference](commands.md)
- [Configuration Guide](configuration.md)
- [Development Guide](development.md)
- [API Documentation](api/index.md)

## Installation

### Windows Installer
Download and run `BIOSTool-X.Y.Z-Setup.exe`

### Linux (Debian/Ubuntu)
```bash
sudo dpkg -i biostool_X.Y.Z-1_all.deb
```

### Manual Installation
```bash
git clone https://github.com/YOUR_ORG/bt.git
cd bt
pip install -r requirements.txt
```

## Basic Usage

```bash
# Initialize BT configuration
bt init

# Configure settings
bt config

# Check status
bt status

# Build BIOS
bt build
```

## Components

### Base CLI Tool
Core command-line functionality for BIOS development workflows.

### GUI Tool
Tkinter-based graphical interface for visual command execution.

### VS Code Extension
Full Visual Studio Code integration with command palette and configuration UI.

## Indices and tables

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`
