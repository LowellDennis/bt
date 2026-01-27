# PowerShell script to set up BT Jump Station (Mapped Drive + RDP Workflow)
# Copy and paste this entire script into PowerShell (Run as Administrator) on the jump station

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "  BT Jump Station Setup for Windows Server" -ForegroundColor Cyan
Write-Host "  (Mapped Drive + RDP Workflow - No SSH Required)" -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

Write-Host "Step 1: Installing 7-Zip (for fast file extraction)..." -ForegroundColor Green
try {
    # Check if 7-Zip is already installed
    $7zipPath = "C:\Program Files\7-Zip\7z.exe"
    if (Test-Path $7zipPath) {
        Write-Host "  - 7-Zip already installed" -ForegroundColor Gray
    } else {
        # Check if winget is available (Windows Server 2022+)
        $winget = Get-Command winget -ErrorAction SilentlyContinue
        if ($winget) {
            Write-Host "  - Installing 7-Zip via winget..." -ForegroundColor Yellow
            winget install --id 7zip.7zip --silent --accept-source-agreements --accept-package-agreements
            Write-Host "  - 7-Zip installed" -ForegroundColor Gray
        } else {
            # Download and install 7-Zip directly
            Write-Host "  - Downloading 7-Zip installer..." -ForegroundColor Yellow
            $installerUrl = "https://www.7-zip.org/a/7z2408-x64.exe"
            $installerPath = "$env:TEMP\7zip-installer.exe"
            
            try {
                Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath -UseBasicParsing
                Write-Host "  - Installing 7-Zip..." -ForegroundColor Yellow
                Start-Process -FilePath $installerPath -ArgumentList "/S" -Wait -NoNewWindow
                Remove-Item $installerPath -Force
                
                if (Test-Path $7zipPath) {
                    Write-Host "  - 7-Zip installed successfully" -ForegroundColor Gray
                } else {
                    Write-Host "  - 7-Zip installation completed but path not found" -ForegroundColor Yellow
                    Write-Host "  - PowerShell's Expand-Archive will be used instead" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "  - Could not download/install 7-Zip: $_" -ForegroundColor Yellow
                Write-Host "  - PowerShell's built-in Expand-Archive (slower but works)" -ForegroundColor Yellow
            }
        }
    }
} catch {
    Write-Host "  - Could not install 7-Zip: $_" -ForegroundColor Yellow
    Write-Host "  - PowerShell's built-in Expand-Archive will be used instead" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Step 2: Verifying Git Installation..." -ForegroundColor Green
try {
    $git = Get-Command git -ErrorAction SilentlyContinue
    if ($git) {
        $gitVersion = git --version
        Write-Host "  - Git is installed: $gitVersion" -ForegroundColor Gray
    } else {
        Write-Host "  - WARNING: Git not found" -ForegroundColor Yellow
        Write-Host "  - Install Git from: https://git-scm.com/download/win" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  - WARNING: Could not verify Git installation" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "How the BT Jump Station workflow works:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. On your dev machine, map this jump station's drive" -ForegroundColor White
Write-Host "     (e.g., map \\jumpstation\C$ to drive D:)" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Create/navigate to your BIOS repository on this jump station" -ForegroundColor White
Write-Host "     Example: C:\Users\Administrator\Desktop\GNext" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. From your dev machine, configure BT with the destination path:" -ForegroundColor White
Write-Host "     bt config jumpstation `"C:\Users\Administrator\Desktop\GNext`"" -ForegroundColor Cyan
Write-Host ""
Write-Host "  4. Generate sync files on your dev machine:" -ForegroundColor White
Write-Host "     bt jump" -ForegroundColor Cyan
Write-Host "     This creates jump_sync.ps1 and jump_sync.zip in the repo root" -ForegroundColor Gray
Write-Host ""
Write-Host "  5. Connect to this jump station via RDP" -ForegroundColor White
Write-Host "     (e.g., using Remote Desktop or RDCMan)" -ForegroundColor Gray
Write-Host ""
Write-Host "  6. On this jump station, run the sync script:" -ForegroundColor White
Write-Host "     D:\HPE\Dev\ROMS\G12\jump_sync.ps1" -ForegroundColor Cyan
Write-Host "     (Replace D: with your mapped drive letter and path)" -ForegroundColor Gray
Write-Host ""
Write-Host "The script will:" -ForegroundColor Yellow
Write-Host "  - Check git status and sync commits if needed" -ForegroundColor White
Write-Host "  - Copy the zip file from your mapped drive" -ForegroundColor White
Write-Host "  - Extract all files with progress display" -ForegroundColor White
Write-Host "  - Clean up temporary files" -ForegroundColor White
Write-Host ""
Write-Host "Benefits of this workflow:" -ForegroundColor Green
Write-Host "  ✓ No SSH configuration needed" -ForegroundColor White
Write-Host "  ✓ Uses your existing RDP connection" -ForegroundColor White
Write-Host "  ✓ Leverages mapped network drives" -ForegroundColor White
Write-Host "  ✓ Full visibility into sync progress" -ForegroundColor White
Write-Host "  ✓ Manual control - you decide when to sync" -ForegroundColor White
Write-Host ""
