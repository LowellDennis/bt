#!/usr/bin/env python

# Standard python modules
import os
import sys
import subprocess
import socket
import tempfile
import zipfile
import shutil
import json
import time

# Local modules
import data
from cmdline  import ParseCommandLine
from error    import ErrorMessage
from misc     import GetJumpStationInfo

# Jump command handler - syncs source and build artifacts to Jump Station using mapped drive + RDP
# returns 0 on success, DOES NOT RETURN otherwise
def jump():
  # Get command line information
  prms, opts = ParseCommandLine({'source-only': False}, 1)
  # DOES NOT RETURN if invalid options or parameters are found

  # Get jumpstation configuration
  jump_info = GetJumpStationInfo()
  if not jump_info:
    ErrorMessage('Jump station not configured.\n' +
                 'Set using: bt config jumpstation <destination-path>')
    # DOES NOT RETURN

  # Remote path on the jump station
  remote_path = jump_info['dest']
  
  # Verify we have a worktree
  if not data.gbl.worktree:
    ErrorMessage('Not in a worktree. Use "bt create" to create one.')
    # DOES NOT RETURN

  # Get platform for build artifacts
  platform = data.lcl.GetItem('platform')
  if not platform:
    print('  Warning: Platform not set (.bt/platform), will sync source only')
    print('  Set platform with: bt config platform <platform-name>')
    print('')

  # Source directory
  source_dir = data.gbl.worktree
  
  # Build directory (if platform is set)
  build_dir = None
  if platform and not opts['source-only']:
    # Platform format: HpeProductLine\Volume\HpPlatforms\U68Pkg
    # Build directory uses only the package name (last component)
    pkg_name = platform.replace('/', '\\').split('\\')[-1]
    build_dir = os.path.join(source_dir, 'Build', pkg_name)
    if not os.path.exists(build_dir):
      print(f'  Warning: Build directory not found: {build_dir}')
      print(f'  Will sync source only. Build the project first with: bt build')
      print('')
      build_dir = None
  elif opts['source-only']:
    print('  /source-only: Skipping build artifacts (ITP debug files)')
    print('')

  # Display sync information
  print('')
  print('Jump Station Sync (Mapped Drive + RDP)')
  print('=' * 60)
  print(f'Source:      {source_dir}')
  if build_dir:
    print(f'Build:       {build_dir}')
  print(f'Destination: {remote_path}')
  print('')

  # Create sync files in repository root (allows multiple repos with different jump stations)
  temp_command_file = os.path.join(source_dir, 'jump_sync.ps1')
  temp_zip_file = os.path.join(source_dir, 'jump_sync.zip')
  completion_marker = os.path.join(source_dir, '.bt_jump_completed.json')
  
  # Check for previous successful sync
  last_sync_commit = None
  last_sync_time = 0
  if os.path.exists(completion_marker):
    try:
      with open(completion_marker, 'r') as f:
        completion_data = json.load(f)
        last_sync_commit = completion_data.get('commit')
        timestamp_str = completion_data.get('timestamp')
        if timestamp_str:
          # Parse ISO format timestamp
          from datetime import datetime
          last_sync_dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
          last_sync_time = last_sync_dt.timestamp()
        print(f'Previous sync: {completion_data.get("timestamp", "unknown")} ({completion_data.get("files_synced", 0)} files)')
    except Exception as e:
      print(f'Warning: Could not read previous sync data: {e}')
  
  # Initialize PowerShell script for execution on jump station
  with open(temp_command_file, 'w', newline='\n') as f:
    f.write('# PowerShell script for BT Jump Station sync\n')
    f.write('# Execute this script ON THE JUMP STATION via RDP\n')
    f.write('$ErrorActionPreference = "Stop"\n\n')
    f.write(f'# Navigate to destination directory\n')
    f.write(f'Set-Location "{remote_path}"\n\n')
    f.write('# Cleanup any leftover files from previous sync\n')
    f.write('if (Test-Path jump_sync.zip) { Remove-Item jump_sync.zip -Force }\n\n')
  
  # Initialize zip file
  # Use ZIP_STORED (no compression) for much faster zip creation
  # Files transfer only slightly slower but zip creation is 10x+ faster
  zipf = zipfile.ZipFile(temp_zip_file, 'w', zipfile.ZIP_STORED)
  
  # Step 1: Get local git commit-id
  print('Getting local git commit...')
  local_commit = None
  try:
    result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                          cwd=source_dir, capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
      local_commit = result.stdout.strip()
      print(f'  Local commit: {local_commit[:12]}')
      
      # Add git commands to script (will execute on jump station)
      with open(temp_command_file, 'a', newline='\n') as f:
        f.write('# Sync git commit with local repository\n')
        f.write('if (Test-Path .git) {\n')
        f.write('  $remoteCommit = git rev-parse HEAD 2>$null\n')
        f.write(f'  if ($remoteCommit -ne "{local_commit}") {{\n')
        f.write(f'    Write-Host "Syncing git to commit {local_commit[:12]}..."\n')
        f.write('    \n')
        f.write('    # Fetch latest commits\n')
        f.write('    Write-Host "  Fetching latest commits..."\n')
        f.write('    git fetch --all 2>&1 | Out-Null\n')
        f.write('    \n')
        f.write('    # Check for uncommitted changes\n')
        f.write('    $status = git status --porcelain\n')
        f.write('    if ($status) {\n')
        f.write('      Write-Host "  Stashing uncommitted changes..."\n')
        f.write('      git stash\n')
        f.write('    }\n')
        f.write('    \n')
        f.write(f'    Write-Host "  Resetting to {local_commit[:12]}..."\n')
        f.write(f'    git reset --hard {local_commit}\n')
        f.write('  } else {\n')
        f.write(f'    Write-Host "Git commit already at {local_commit[:12]}"\n')
        f.write('  }\n')
        f.write('} else {\n')
        f.write('  Write-Host "No git repository found - skipping git sync"\n')
        f.write('}\n\n')
    else:
      print('  Warning: Could not get local git commit')
  except Exception as e:
    print(f'  Warning: Git check failed: {str(e)}')
  print('')
  
  # Step 4: Check local git status and add modified/uncommitted changes to zip
  print('Checking for modified/uncommitted files...')
  changed_files = []
  try:
    result = subprocess.run(['git', 'status', '--porcelain'],
                          cwd=source_dir, capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
      status_lines = [line for line in result.stdout.strip().split('\n') if line]
      if status_lines:
        for line in status_lines:
          # Format: "XY filename" where X and Y are status codes (2 chars), then space(s), then filename
          # Split to get just the filename part (everything after the status codes)
          if len(line) > 3:
            # The first 2 characters are status codes, skip them and any following whitespace
            file_path = line[2:].lstrip()
            full_path = os.path.join(source_dir, file_path)
              
            # Only add existing files (skip deleted files)
            if os.path.exists(full_path) and os.path.isfile(full_path):
              changed_files.append(file_path)
              # Add to zip with proper path structure
              zipf.write(full_path, file_path)
        
        if changed_files:
          print(f'  Found {len(changed_files)} modified/new source file(s)')
        else:
          print('  No local changes detected')
      else:
        print('  No local changes detected')
    else:
      print('  Warning: Could not check git status')
  except Exception as e:
    print(f'  Warning: Git status failed: {str(e)}')
  print('')
  
  # Step 5: Recurse through Build directory and add Intel ITP files
  # Step 5: Add Intel ITP debug files (.map, .cod, .efi, .pdb, etc.) from Build directory
  # Use last successful sync time for incremental updates
  itp_files = []
  if build_dir:
    print('Adding Intel ITP debug files from Build directory...')
    
    # File extensions needed by Intel ITP
    itp_extensions = {'.map', '.cod', '.efi', '.pdb', '.debug', '.sym'}
    
    skipped_count = 0
    for root, dirs, files in os.walk(build_dir):
      for file in files:
        _, ext = os.path.splitext(file)
        if ext.lower() in itp_extensions:
          full_path = os.path.join(root, file)
          
          # Incremental: skip if file not modified since last successful sync
          if last_sync_time > 0:
            file_mtime = os.path.getmtime(full_path)
            if file_mtime <= last_sync_time:
              skipped_count += 1
              continue
          
          # Get relative path from source_dir
          rel_path = os.path.relpath(full_path, source_dir)
          itp_files.append(rel_path)
          zipf.write(full_path, rel_path)
    
    if last_sync_time > 0:
      print(f'  Found {len(itp_files)} modified ITP file(s) (skipped {skipped_count} unchanged)')
    else:
      print(f'  Found {len(itp_files)} ITP debug file(s)')
    print('')
  
  # Close the zip file
  zipf.close()
  
  # Step 6: Add copy and unzip commands to script
  if changed_files or itp_files:
    with open(temp_command_file, 'a', newline='\n') as f:
      f.write('# Copy zip file from mapped drive to destination\n')
      f.write(f'$zipSource = "{temp_zip_file.replace(chr(92), chr(92)+chr(92))}"\n')
      f.write('Write-Host "Copying zip file from mapped drive..."\n')
      f.write('Copy-Item -Path $zipSource -Destination jump_sync.zip -Force\n\n')
      
      f.write('# Extract synced files\n')
      f.write('Write-Host "Extracting files..."\n')
      f.write(f'if (Test-Path "C:\\Program Files\\7-Zip\\7z.exe") {{\n')
      f.write(f'  & "C:\\Program Files\\7-Zip\\7z.exe" x -y -bsp1 jump_sync.zip\n')
      f.write(f'}} else {{\n')
      f.write(f'  Expand-Archive -Path jump_sync.zip -DestinationPath "{remote_path}" -Force -Verbose\n')
      f.write(f'}}\n\n')
      
      f.write('# Cleanup\n')
      f.write('Remove-Item -Path jump_sync.zip -Force\n')
      
      # Write completion marker back to local machine via mapped drive
      f.write('# Write completion marker back to local machine\n')
      completion_path = completion_marker.replace('\\', '\\\\')
      f.write(f'$completionData = @{{\n')
      f.write(f'  timestamp = (Get-Date).ToString("o")\n')
      f.write(f'  commit = "{local_commit if local_commit else "unknown"}"\n')
      f.write(f'  files_synced = {len(changed_files) + len(itp_files)}\n')
      f.write(f'}} | ConvertTo-Json\n')
      f.write(f'$completionData | Out-File -FilePath "{completion_path}" -Encoding UTF8 -Force\n\n')
      
      f.write('Remove-Item -Path jump_sync.ps1 -Force\n\n')
      
      f.write('Write-Host ""\n')
      f.write('Write-Host "Sync completed successfully!" -ForegroundColor Green\n')
  
  # Display completion message with instructions
  print('')
  print('=' * 60)
  print('✓ Sync package created successfully!')
  print('=' * 60)
  print('')
  print('Files created in repository root:')
  print(f'  Script: {os.path.basename(temp_command_file)}')
  print(f'  Zip:    {os.path.basename(temp_zip_file)}')
  if changed_files or itp_files:
    print(f'  Count:  {len(changed_files) + len(itp_files)} file(s)')
  print('')
  print('To complete the sync:')
  print('  1. Connect to jump station via RDP')
  print(f'  2. Execute the script from your mapped drive:')
  print(f'     Example: D:\\HPE\\Dev\\ROMS\\G12\\jump_sync.ps1')
  print(f'     (Replace with your mapped drive letter and repo path)')
  print('')
  print('The script will:')
  print('  - Fetch latest commits and sync to local commit')
  print('  - Copy zip file from mapped drive')
  print('  - Extract all files to destination')
  print('  - Clean up temporary files')
  print('')
  
  return 0


  
  return 0
