# Git Hooks for BT

This directory contains Git hooks to maintain code quality and consistency.

## Available Hooks

### pre-commit
Runs before each commit:
- Version consistency check
- Quick test run (fast feedback)
- Critical syntax error check

### pre-push
Runs before pushing to remote:
- Version consistency check
- Full test suite

## Installation

### Linux/macOS
```bash
./.githooks/install-hooks.sh
```

### Windows
```powershell
.\.githooks\install-hooks.ps1
```

## Bypassing Hooks

If you need to bypass hooks temporarily:

```bash
# Skip pre-commit hook
git commit --no-verify

# Skip pre-push hook
git push --no-verify
```

⚠️ **Warning:** Only bypass hooks when absolutely necessary!

## Customizing Hooks

Edit the hook scripts in this directory and reinstall:

1. Modify `.githooks/pre-commit` or `.githooks/pre-push`
2. Run installation script again

## Automatic Installation

Add to CONTRIBUTING.md or development setup to remind developers to install hooks.

## Why Git Hooks?

- **Catch issues early**: Before they reach CI/CD
- **Faster feedback**: Local checks are faster than remote CI
- **Maintain quality**: Prevent broken commits from being pushed
- **Version consistency**: Ensure version is always in sync
