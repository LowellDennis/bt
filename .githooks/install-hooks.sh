#!/bin/bash
# Install Git hooks from .githooks directory

echo "Installing Git hooks..."

# Get the git directory
GIT_DIR=$(git rev-parse --git-dir)

if [ ! -d "$GIT_DIR" ]; then
    echo "Error: Not in a Git repository"
    exit 1
fi

# Copy hooks
cp .githooks/pre-commit "$GIT_DIR/hooks/pre-commit"
cp .githooks/pre-push "$GIT_DIR/hooks/pre-push"

# Make executable
chmod +x "$GIT_DIR/hooks/pre-commit"
chmod +x "$GIT_DIR/hooks/pre-push"

echo "✓ Git hooks installed successfully!"
echo ""
echo "Installed hooks:"
echo "  - pre-commit: Version check, quick tests"
echo "  - pre-push: Version check, full test suite"
echo ""
echo "To bypass hooks use: git commit --no-verify"
