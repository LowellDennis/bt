# Build HPE Server BIOS Tool Installer for Windows
# Requires Inno Setup 6.0 or later

param(
    [string]$Configuration = "Release",
    [switch]$SkipVSCodeExtension = $false
)

$ErrorActionPreference = "Stop"

Write-Host "Building BIOSTool Windows Installer..." -ForegroundColor Cyan

# Check for Inno Setup
$InnoSetupPaths = @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles}\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 5\ISCC.exe"
)

$ISCC = $null
foreach ($path in $InnoSetupPaths) {
    if (Test-Path $path) {
        $ISCC = $path
        break
    }
}

if (-not $ISCC) {
    Write-Error "Inno Setup not found. Please install from https://jrsoftware.org/isinfo.php"
    exit 1
}

Write-Host "Found Inno Setup: $ISCC" -ForegroundColor Green

# Build VS Code extension if not skipping
if (-not $SkipVSCodeExtension) {
    Write-Host "Building VS Code extension..." -ForegroundColor Cyan
    
    $ExtensionDir = Join-Path $PSScriptRoot "..\..\vscode-extension"
    if (Test-Path $ExtensionDir) {
        Push-Location $ExtensionDir
        try {
            # Install dependencies and build
            if (Test-Path "package.json") {
                Write-Host "Installing npm dependencies..." -ForegroundColor Yellow
                npm install
                
                Write-Host "Building extension..." -ForegroundColor Yellow
                npm run compile
                
                Write-Host "Packaging extension..." -ForegroundColor Yellow
                npx @vscode/vsce package --out .
            }
        }
        finally {
            Pop-Location
        }
    } else {
        Write-Warning "VS Code extension directory not found at: $ExtensionDir"
    }
}

# Create output directory
$OutputDir = Join-Path $PSScriptRoot "output"
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

# Build installer
Write-Host "Building installer with Inno Setup..." -ForegroundColor Cyan
$ISSFile = Join-Path $PSScriptRoot "biostool.iss"

& $ISCC $ISSFile

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nInstaller built successfully!" -ForegroundColor Green
    Write-Host "Output: $OutputDir" -ForegroundColor Green
    
    # List output files
    Get-ChildItem $OutputDir -Filter "*.exe" | ForEach-Object {
        Write-Host "  - $($_.Name) ($([math]::Round($_.Length / 1MB, 2)) MB)" -ForegroundColor Cyan
    }
} else {
    Write-Error "Installer build failed with exit code: $LASTEXITCODE"
    exit $LASTEXITCODE
}
