# Command Reference

Complete reference for all BT commands.

## Core Commands

### init
Initialize BT configuration files.

```bash
bt init
```

Creates `global.txt` and `local.txt` configuration files.

### config
View or modify configuration settings.

```bash
# Show all configuration
bt config --show

# Get a value
bt config KEY

# Set a value
bt config KEY value

# Edit in text editor
bt config --edit
```

**Common Configuration Keys:**
- `BIOS_SOURCE`: Path to BIOS source code
- `BUILD_TARGET`: Default build target
- `EDITOR`: Preferred text editor
- `JUMP_SERVER`: Jump station configuration

### status
Show Git repository status.

```bash
bt status
```

Displays current branch, uncommitted changes, and worktree information.

## Build Commands

### build
Build BIOS source code.

```bash
# Basic build
bt build

# Build specific target
bt build --target Release

# Upload to jump station
bt build --upload

# Verbose output
bt build -v
```

**Options:**
- `--target <target>`: Specify build target
- `--upload`: Upload to jump station after build
- `-v, --verbose`: Increase verbosity

## Worktree Commands

### worktrees
List all Git worktrees.

```bash
bt worktrees
```

### create
Create a new Git worktree.

```bash
bt create <branch-name> [path]
```

**Arguments:**
- `branch-name`: Name of the branch
- `path`: Optional path for worktree (defaults to ../branch-name)

### select
Switch to a different worktree.

```bash
bt select <path>
```

### attach
Attach current directory to a Git repository.

```bash
bt attach <repo-path>
```

### detach
Detach current directory from Git repository.

```bash
bt detach
```

### remove
Remove a Git worktree.

```bash
bt remove <path>
```

## Version Control Commands

### fetch
Fetch updates from remote repository.

```bash
bt fetch
```

### merge
Merge changes from another branch.

```bash
bt merge <branch>
```

### push
Push commits to remote repository.

```bash
bt push
```

## Jump Station Commands

### jump
Execute commands on jump station.

```bash
bt jump <command>
```

## Utility Commands

### cleanup
Clean build artifacts.

```bash
bt cleanup
```

### top
Show top-level repository directory.

```bash
bt top
```

### use
Set active configuration or environment.

```bash
bt use <name>
```

## Command Options

Most commands support these global options:

- `-h, --help`: Show help for command
- `-v, --verbose`: Increase verbosity
- `-q, --quiet`: Decrease verbosity

## Getting Help

For detailed help on any command:

```bash
bt <command> --help
```
