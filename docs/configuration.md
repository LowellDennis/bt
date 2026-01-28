# Configuration Guide

Understanding BT's configuration system.

## Configuration Files

BT uses two configuration files:

### global.txt
System-wide settings that apply across all projects.

**Location:**
- Windows: `%USERPROFILE%\.bt\global.txt`
- Linux: `~/.bt/global.txt`

### local.txt
Project-specific settings (gitignored by default).

**Location:**
- In your project's root directory

## Configuration Format

Configuration files use a simple `KEY = VALUE` format:

```
# Comments start with #
BIOS_SOURCE = /path/to/bios
BUILD_TARGET = Release

# Variable expansion
BUILD_DIR = ${BIOS_SOURCE}/build
OUTPUT_DIR = ${BUILD_DIR}/output
```

## Variable Expansion

Use `${VAR}` syntax to reference other variables:

```
BASE_PATH = /home/user/projects
BIOS_SOURCE = ${BASE_PATH}/bios
BUILD_DIR = ${BIOS_SOURCE}/build
```

Variables are expanded recursively.

## Common Configuration Keys

### BIOS_SOURCE
Path to BIOS source code repository.

```
BIOS_SOURCE = /path/to/bios/source
```

### BUILD_TARGET
Default build target (Debug, Release, etc.).

```
BUILD_TARGET = Release
```

### EDITOR
Text editor to use for editing files.

```
EDITOR = code           # VS Code
EDITOR = vim            # Vim
EDITOR = notepad++      # Notepad++
```

### JUMP_SERVER
Jump station configuration for remote builds.

```
JUMP_SERVER = user@jumpstation.example.com
```

### Build Configuration

```
BUILD_THREADS = 8
BUILD_OPTIONS = -j8 -O2
```

## Managing Configuration

### View All Settings

```bash
bt config --show
```

### Get a Value

```bash
bt config BIOS_SOURCE
```

### Set a Value

```bash
bt config BIOS_SOURCE /new/path
```

### Edit in Text Editor

```bash
bt config --edit
```

This opens the configuration file in your configured editor.

## Configuration Hierarchy

Settings are resolved in this order:

1. Command-line arguments (highest priority)
2. Environment variables
3. Local configuration (`local.txt`)
4. Global configuration (`global.txt`)
5. Built-in defaults (lowest priority)

## Best Practices

### Use Global for User Preferences

```
# ~/.bt/global.txt
EDITOR = code
JUMP_SERVER = user@jumpstation
```

### Use Local for Project Settings

```
# project/local.txt
BIOS_SOURCE = /path/to/this/project
BUILD_TARGET = Debug
```

### Don't Commit local.txt

The `local.txt` file should be in `.gitignore` to avoid committing personal paths.

## Examples

### Basic Setup

```bash
# Set BIOS source
bt config BIOS_SOURCE /home/user/bios

# Set editor
bt config EDITOR code

# Set build target
bt config BUILD_TARGET Release
```

### Jump Station Setup

```bash
# Configure jump station
bt config JUMP_SERVER user@jumpstation.example.com

# Test connection
bt jump hostname
```

### Advanced Variable Expansion

```
# Base paths
PROJECT_ROOT = /home/user/projects
BIOS_ROOT = ${PROJECT_ROOT}/bios

# Build paths
BUILD_DIR = ${BIOS_ROOT}/build
OUTPUT_DIR = ${BUILD_DIR}/${BUILD_TARGET}
LOG_DIR = ${BUILD_DIR}/logs

# Tools
COMPILER = ${BIOS_ROOT}/tools/compiler/bin/gcc
```
