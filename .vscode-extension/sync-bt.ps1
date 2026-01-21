# Auto-sync BT tool changes to bundled version
# This script watches the parent directory for changes and re-bundles automatically

param(
    [string]$SourcePath = ".."
)

Write-Host "Starting BT Tool Auto-Sync..." -ForegroundColor Cyan
Write-Host "Watching: $SourcePath" -ForegroundColor DarkGray
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

# Initial bundle
& "$PSScriptRoot\bundle-bt.ps1" -SourcePath $SourcePath

# Create file system watcher
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = (Resolve-Path $SourcePath).Path
$watcher.IncludeSubdirectories = $true
$watcher.NotifyFilter = [System.IO.NotifyFilters]::LastWrite -bor [System.IO.NotifyFilters]::FileName -bor [System.IO.NotifyFilters]::DirectoryName
$watcher.Filter = "*.py"

# Track last bundle time to debounce rapid changes
$script:lastBundleTime = Get-Date

$action = {
    $name = $Event.SourceEventArgs.Name
    $changeType = $Event.SourceEventArgs.ChangeType
    $timeStamp = $Event.TimeGenerated
    
    # Debounce: only rebundle if 2 seconds have passed
    $timeSinceLastBundle = (Get-Date) - $script:lastBundleTime
    if ($timeSinceLastBundle.TotalSeconds -lt 2) {
        return
    }
    
    Write-Host ""
    Write-Host "[$timeStamp] BT file $changeType: $name" -ForegroundColor Yellow
    Write-Host "Re-bundling..." -ForegroundColor Cyan
    
    try {
        & "$PSScriptRoot\bundle-bt.ps1" -SourcePath $using:SourcePath
        $script:lastBundleTime = Get-Date
        Write-Host "Sync complete!" -ForegroundColor Green
    } catch {
        Write-Host "Sync failed: $_" -ForegroundColor Red
    }
}

# Register event handlers
$handlers = @(
    (Register-ObjectEvent $watcher 'Changed' -Action $action),
    (Register-ObjectEvent $watcher 'Created' -Action $action),
    (Register-ObjectEvent $watcher 'Deleted' -Action $action),
    (Register-ObjectEvent $watcher 'Renamed' -Action $action)
)

# Enable the watcher
$watcher.EnableRaisingEvents = $true

Write-Host "Auto-sync is active. Monitoring for changes..." -ForegroundColor Green

try {
    # Keep script running
    while ($true) {
        Wait-Event -Timeout 1
        Get-Event | Remove-Event
    }
} finally {
    # Cleanup
    Write-Host "Stopping auto-sync..." -ForegroundColor Yellow
    $watcher.EnableRaisingEvents = $false
    $handlers | ForEach-Object { Unregister-Event -SourceIdentifier $_.Name }
    $watcher.Dispose()
    Write-Host "Auto-sync stopped." -ForegroundColor Cyan
}
