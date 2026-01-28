# Install Git hooks from .githooks directory

Write-Host "Installing Git hooks..." -ForegroundColor Cyan

# Get the git directory
$gitDir = git rev-parse --git-dir 2>$null

if (-not $gitDir) {
    Write-Host "Error: Not in a Git repository" -ForegroundColor Red
    exit 1
}

# Copy hooks
Copy-Item ".githooks\pre-commit" "$gitDir\hooks\pre-commit" -Force
Copy-Item ".githooks\pre-push" "$gitDir\hooks\pre-push" -Force

Write-Host "✓ Git hooks installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Installed hooks:"
Write-Host "  - pre-commit: Version check, quick tests"
Write-Host "  - pre-push: Version check, full test suite"
Write-Host ""
Write-Host "To bypass hooks use: git commit --no-verify"
