# Generate unique session ID based on timestamp and random number
$btid = "{0:HHmmssff}{1}" -f (Get-Date), (Get-Random -Minimum 1000 -Maximum 9999)
$postBtFile = "$env:TEMP\postbt_$btid.cmd"

# Delete post executable command file (if it exists)
if (Test-Path $postBtFile) {
    Remove-Item $postBtFile -Force | Out-Null
}

# Execute the BIOS tool with session ID
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$scriptName = [System.IO.Path]::GetFileNameWithoutExtension($MyInvocation.MyCommand.Name)
$pythonScript = Join-Path $scriptDir "$scriptName.py"

& py.exe $pythonScript --btid=$btid @args

# See if there is a post executable command file
if (Test-Path $postBtFile) {
    # Execute post command file
    & cmd.exe /c $postBtFile
    # Clean up post command file
    Remove-Item $postBtFile -Force -ErrorAction SilentlyContinue | Out-Null
}
