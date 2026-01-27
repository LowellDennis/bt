# Script to bundle BT tool with the VS Code extension
param(
    [string]$SourcePath = "..",
    [string]$TargetPath = "bt-tool"
)

# Resolve source path to absolute
$SourcePath = (Resolve-Path $SourcePath).Path

Write-Host "Bundling BT tool with VS Code extension..." -ForegroundColor Cyan
Write-Host "Source: $SourcePath" -ForegroundColor DarkGray

if (Test-Path $TargetPath) {
    Write-Host "Removing existing bt-tool directory..." -ForegroundColor Yellow
    Remove-Item -Path $TargetPath -Recurse -Force
}

New-Item -ItemType Directory -Path $TargetPath -Force | Out-Null

$coreFiles = @(
    "bt.py", "bt.ps1", "bt.cmd", "bt.sh", "abbrev.py", "announce.py", "cmdline.py",
    "command.py", "data.py", "error.py", "evaluate.py", "logger.py",
    "misc.py", "postbios.py", "run.py", "vcs.py", "global.txt", "local.txt"
)

$commandDirs = @(
    "attach", "build", "cleanup", "config", "create", "remove", "detach",
    "fetch", "init", "jump", "merge", "move", "push", "select", "status", "use", "top", "worktrees"
)

Write-Host "Copying core files..." -ForegroundColor Green
foreach ($file in $coreFiles) {
    $sourceFile = "$SourcePath\$file"
    if (Test-Path $sourceFile) {
        Copy-Item -Path $sourceFile -Destination $TargetPath -Force
        Write-Host "  OK $file" -ForegroundColor DarkGray
    } else {
        Write-Host "  MISSING $file (looked in $sourceFile)" -ForegroundColor Red
    }
}

Write-Host "Copying command modules..." -ForegroundColor Green
foreach ($dir in $commandDirs) {
    $sourceDir = "$SourcePath\$dir"
    if (Test-Path $sourceDir) {
        $targetDir = "$TargetPath\$dir"
        Copy-Item -Path $sourceDir -Destination $targetDir -Recurse -Force
        Get-ChildItem -Path $targetDir -Filter "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
        Write-Host "  OK $dir/" -ForegroundColor DarkGray
    } else {
        Write-Host "  MISSING $dir/ (looked in $sourceDir)" -ForegroundColor Red
    }
}

$readmeText = "BIOS Tool (Bundled)`r`n`r`nBundled copy of HPE Server BIOS Tool."
Set-Content -Path (Join-Path $TargetPath "README.txt") -Value $readmeText

Write-Host ""
Write-Host "BT tool bundled successfully!" -ForegroundColor Green
Write-Host "Location: $TargetPath" -ForegroundColor Cyan

$fileCount = (Get-ChildItem -Path $TargetPath -Recurse -File | Measure-Object).Count
Write-Host "Total files: $fileCount" -ForegroundColor DarkGray
