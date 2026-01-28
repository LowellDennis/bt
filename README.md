![BIOS Tool Image](https://github.com/LowellDennis/bt/blob/main/BiosTool.jpg)

# BIOS Tool (BT)

[![Tests](https://github.com/LowellDennis/bt/actions/workflows/test-and-coverage.yml/badge.svg)](https://github.com/LowellDennis/bt/actions/workflows/test-and-coverage.yml)
[![Code Quality](https://github.com/LowellDennis/bt/actions/workflows/code-quality.yml/badge.svg)](https://github.com/LowellDennis/bt/actions/workflows/code-quality.yml)
[![codecov](https://codecov.io/gh/LowellDennis/bt/branch/main/graph/badge.svg)](https://codecov.io/gh/LowellDennis/bt)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

A suite of tools for working with HPE Server BIOS source code, including a command-line interface, GUI application, and VS Code extension.

**Current Version:** V1.0

## Installation

### Using Installers (Recommended)

**Windows:**
- Download `installers/windows/output/BIOSTool-1.0.0-Setup.exe`
- Run the installer and follow the prompts
- The installer includes the command-line tool, GUI, and VS Code extension
- BT will be added to your PATH automatically

**Linux (Debian/Ubuntu):**
```bash
sudo dpkg -i installers/linux/build/biostool_1.0.0-1_all.deb
sudo apt-get install -f  # Fix any dependencies
```

Both installers include all three components:
- Command-line tool (`bt`)
- Graphical user interface (`btgui`)
- VS Code extension

### Manual Installation

Clone the repository:
```bash
git clone git@github.com:LowellDennis/bt.git
```

Requirements:
- Add the BT directory to your PATH
- Python 2.7+ installed (Python 3+ recommended)
  - Download from [python.org](https://www.python.org/)

### Building Installers

See [installers/README.md](installers/README.md) for instructions on building installers.

## Features

BIOS Tool simplifies HPE Server BIOS development with:

**Minimal Setup**
- Global settings apply to all worktrees (set once)
- Only a few local settings per worktree

**Smart Navigation**
- Automatic BIOS worktree detection
- Easy directory navigation with `bt top`

**Git/SVN Integration**
- Automatic git worktree detection
- Filtered status output (hides build artifacts)
- Simplified source updates and merging

**Build Management**
- Simple CLEAN and BUILD commands
- Automatic log file capture
- Smart filtering of ERROR and WARNING messages
- Optional SMS/email alerts on build completion

**Remote Debugging**
- Jump Station sync for Intel ITP debugging
- Hash-based incremental sync (only changed files)
- Mapped drive + RDP workflow (no SSH required)

## Commands

```
usage: bt <command> [param1 [param2 [...]]]

Available commands:
  attach    - Add a BIOS repository to the list
  build     - Build a BIOS for the current repository or worktree
  cleanup   - Clean the current repository or worktree
  config    - Get or set configuration settings
  create    - Create a new BIOS worktree
  detach    - Remove a BIOS repository from the list
  fetch     - Update local repository/worktree from remote
  init      - Initialize local settings for current worktree
  jump      - Sync source and build artifacts to Jump Station
  merge     - Merge upstream changes into local repository/worktree
  move      - Move a BIOS worktree
  push      - Push local changes to remote
  remove    - Delete a BIOS worktree
  select    - Select a BIOS repository from the list
  status    - Get status of current repository or worktree
  top       - Change directory to repository/worktree root
  use       - Switch to a different repository or worktree
  worktrees - List all worktrees with details

Note: Commands can be abbreviated (e.g., 'b' for build, 'st' for status)

For detailed help: bt help <command>
```

## Quick Start

### 1. Attach a Repository

After cloning a BIOS repository (using `git clone` or `svn checkout`), attach it to BT:

```bash
cd /path/to/bios/repo
bt attach
```

### 2. Create a Worktree

```bash
bt create [/repo <path>] <branch> <worktree> [<commit-ish>]
```

Parameters:
- `/repo <path>` - Repository path (default: current selected repo)
- `<branch>` - Branch name for new worktree
- `<worktree>` - Base directory for new worktree
- `<commit-ish>` - Starting commit/tag/branch (default: HEAD)

### 3. Initialize Worktree

```bash
cd <worktree>
bt init <platform-name>
```

Example platforms: U66, A55, R13

This will:
- Auto-detect platform directory, CPU name, and vendor
- Initialize alert, release, and warnings settings

### 4. Build

```bash
bt build
```

### Optional: Build Notifications

Configure SMS/email alerts for build completion:

```bash
bt config email <text-email-address>
bt config alert on
```

**Carrier Text-Email Formats:**

| Carrier           | Email Format                                         |
|-------------------|------------------------------------------------------|
| AT&T              | [10-digit-number]@txt.att.net                        |
| T-Mobile          | [10-digit-number]@tmomail.net                        |
| Verizon           | [10-digit-number]@vtext.com                          |
| Boost Mobile      | [10-digit-number]@myboostmobile.com                  |
| U.S. Cellular     | [10-digit-number]@email.uscc.net                     |
| Virgin Mobile     | [10-digit-number]@vmobl.com                          |
| Republic Wireless | [10-digit-number]@text.republicwireless.com          |

**Important:** Outlook and your command shell must run at the same privilege level for notifications to work.

### View Settings

```bash
bt config  # Show all global and local settings
```

## Extending BT

BT is easily extensible with a hierarchical design:

**Structure:**
1. Main program: `bt.cmd` (Windows) or `bt.sh` (Linux/macOS)
2. Python entry: `bt.py` scans for command subdirectories
3. Each command subdirectory contains:
   - `terse.txt` - Brief command description
   - `details.txt` - Detailed command documentation
   - `needs.vcs` - (optional) Indicates VCS requirements
   - `<command>.py` - Command implementation
   - Additional support files (e.g., `filter.txt`, `send.ps1`)

**Requirements:**
- Command subdirectory and Python file names must match (case-sensitive)
- Main function in Python file must match this name

## Contact

Maintained by [Lowell Dennis](mailto:lowell.dennis@hpe.com?subject="BIOS Tool")

## Version History

| Version  | Changes                                                          |
|----------|------------------------------------------------------------------|
| **V1.0** | Command renames (destroy→remove, switch→use, clean→cleanup,      |
|          | pull→fetch), Jump Station redesign (mapped drive+RDP, hash-based |
|          | sync), worktrees command, improved table formatting,             |
|          | GUI/extension updates                                            |
| **V0.9** | Linux/macOS support, bug fixes                                   |
| **V0.8** | GUI improvements                                                 |
| **V0.7** | Windows/Linux installers                                         |
| **V0.6** | VS Code extension, ITP debugger support                          |
| **V0.5** | Build progress tracking                                          |
| **V0.4** | Help system improvements, wake lock, BMC upload support          |
| **V0.3** | Bug fixes                                                        |
| **V0.2** | Team release, worktree fixes                                     |
| **V0.1** | Original release                                                 |
