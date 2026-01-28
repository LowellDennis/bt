# Getting Started

This guide will help you get up and running with BIOS Tool (BT).

## Prerequisites

- Python 3.6 or higher
- Git (for version control features)
- Windows 10/11 or Ubuntu 20.04+

## Installation

### Windows

1. Download the installer: `BIOSTool-X.Y.Z-Setup.exe`
2. Run the installer
3. Follow the installation wizard
4. Open a new terminal and verify: `bt --help`

### Linux (Debian/Ubuntu)

```bash
# Download the .deb package
wget https://github.com/YOUR_ORG/bt/releases/download/VX.Y.Z/biostool_X.Y.Z-1_all.deb

# Install
sudo dpkg -i biostool_X.Y.Z-1_all.deb

# Verify installation
bt --help
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_ORG/bt.git
cd bt

# (Optional) Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Test
python bt.py --help
```

## First Steps

### 1. Initialize Configuration

```bash
bt init
```

This creates configuration files in your home directory.

### 2. Set Your BIOS Source Path

```bash
bt config BIOS_SOURCE /path/to/bios/source
```

### 3. Configure Your Editor

```bash
bt config EDITOR "code"  # VS Code
# or
bt config EDITOR "vim"   # Vim
```

### 4. Check Status

```bash
bt status
```

## Common Workflows

### Building BIOS

```bash
# Simple build
bt build

# Build with specific target
bt build --target Release

# Upload to jump station
bt build --upload
```

### Managing Worktrees

```bash
# List worktrees
bt worktrees

# Create new worktree
bt create feature-branch /path/to/worktree

# Switch to worktree
bt select /path/to/worktree
```

### Configuration Management

```bash
# View all configuration
bt config --show

# Set a value
bt config KEY value

# Get a value
bt config KEY
```

## Next Steps

- Read the [Command Reference](commands.md)
- Learn about [Configuration](configuration.md)
- Explore [Development Guide](development.md)
