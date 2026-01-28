# Build BT GUI standalone executable for Windows

Write-Host "Building BT GUI standalone executable for Windows..." -ForegroundColor Cyan

# Check PyInstaller
if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Host "PyInstaller not found. Installing..." -ForegroundColor Yellow
    pip install pyinstaller
}

# Clean previous builds
if (Test-Path "build") {
    Remove-Item -Recurse -Force build
}
if (Test-Path "dist") {
    Remove-Item -Recurse -Force dist
}

# Build with PyInstaller
Write-Host "Running PyInstaller..." -ForegroundColor Cyan
pyinstaller btgui.spec --clean

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Build successful!" -ForegroundColor Green
    Write-Host "Executable: $PWD\dist\BTGui.exe" -ForegroundColor Green
    
    # Show file size
    $exe = Get-Item "dist\BTGui.exe"
    $sizeMB = [math]::Round($exe.Length / 1MB, 2)
    Write-Host "Size: $sizeMB MB" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}
