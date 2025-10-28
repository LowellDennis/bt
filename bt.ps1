# Delete post executable command file (if it exists)
$postBtFile = "$env:TEMP\postbt.cmd"
if (Test-Path $postBtFile) {
    Remove-Item $postBtFile -Force | Out-Null
}

# Execute the BIOS tool
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptName = [System.IO.Path]::GetFileNameWithoutExtension($MyInvocation.MyCommand.Name)
$pythonScript = Join-Path $scriptDir "$scriptName.py"

& py.exe $pythonScript @args

# See if there is a post executable command file
if (Test-Path $postBtFile) {
    # Execute post command file
    & $postBtFile
}
