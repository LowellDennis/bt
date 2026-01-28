#!/usr/bin/env python

# Standard python modules
import os
import subprocess
import zipfile
import json
import hashlib

# Local modules
import data
from cmdline  import ParseCommandLine
from error    import ErrorMessage
from misc     import GetJumpStationInfo

# Calculate SHA256 hash of a file
def calculate_file_hash(file_path):
  sha256_hash = hashlib.sha256()
  with open(file_path, 'rb') as f:
    # Read in chunks to handle large files efficiently
    for byte_block in iter(lambda: f.read(4096), b""):
      sha256_hash.update(byte_block)
  return sha256_hash.hexdigest()

# Clean jump station cache - removes hash cache and sync timestamp
# returns 0 on success
def clean_jump_cache():
  bt_dir = os.path.join(data.gbl.worktree, '.bt')
  hash_file = os.path.join(bt_dir, 'jump_hashes.json')
  sync_file = os.path.join(bt_dir, 'jump_last_sync')
  
  removed = []
  if os.path.exists(hash_file):
    os.remove(hash_file)
    removed.append('jump_hashes.json')
  
  if os.path.exists(sync_file):
    os.remove(sync_file)
    removed.append('jump_last_sync')
  
  if removed:
    print('')
    print('Jump Station Cache Cleared')
    print('=' * 60)
    print(f'Removed: {", ".join(removed)}')
    print('')
    print('Next "bt jump" will perform a full sync (not incremental)')
    print('')
  else:
    print('')
    print('No jump station cache found (already clean)')
    print('')
  
  return 0

# Jump command handler - syncs source and build artifacts to Jump Station using mapped drive + RDP
# returns 0 on success, DOES NOT RETURN otherwise
def jump():
  # Get command line information
  prms, opts = ParseCommandLine({'source-only': False, 'clean': False}, 1)
  # DOES NOT RETURN if invalid options or parameters are found
  
  # Handle /clean option
  if opts['clean']:
    return clean_jump_cache()

  # Get jump station configuration
  jump_info = GetJumpStationInfo()
  if not jump_info:
    ErrorMessage('Jump station not configured.\n' +
                 'Set using: bt config jump <destination-path>')
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
  
  # Hash cache in .bt directory
  bt_dir = os.path.join(source_dir, '.bt')
  hash_cache_file = os.path.join(bt_dir, 'jump_hashes.json')
  sync_timestamp_file = os.path.join(bt_dir, 'jump_last_sync')
  
  # Load previous hashes if last sync was successful
  previous_hashes = {}
  cache_valid = False
  if os.path.exists(sync_timestamp_file) and os.path.exists(hash_cache_file):
    try:
      with open(sync_timestamp_file, 'r') as f:
        last_sync_time = f.read().strip()
      with open(hash_cache_file, 'r') as f:
        previous_hashes = json.load(f)
      cache_valid = True
      print(f'Previous sync: {last_sync_time} ({len(previous_hashes)} files cached)')
    except Exception as e:
      print(f'Warning: Could not load hash cache: {e}')
      print('Performing full sync...')
  else:
    print('No previous sync found - performing full sync')
  
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
  current_hashes = {}  # Track hashes for all files being synced
  
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
              # Calculate hash and check if changed
              file_hash = calculate_file_hash(full_path)
              current_hashes[file_path] = file_hash
              
              # Add if new or hash changed
              if not cache_valid or file_path not in previous_hashes or previous_hashes[file_path] != file_hash:
                changed_files.append(file_path)
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
  
  # Step 5: Add Intel ITP debug files (.map, .cod, .efi, .pdb, etc.) from Build directory
  # Use hash-based incremental sync
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
          rel_path = os.path.relpath(full_path, source_dir)
          
          # Calculate hash
          file_hash = calculate_file_hash(full_path)
          current_hashes[rel_path] = file_hash
          
          # Incremental: skip if hash unchanged
          if cache_valid and rel_path in previous_hashes and previous_hashes[rel_path] == file_hash:
            skipped_count += 1
            continue
          
          # Add to zip
          itp_files.append(rel_path)
          zipf.write(full_path, rel_path)
    
    if cache_valid:
      print(f'  Found {len(itp_files)} modified ITP file(s) (skipped {skipped_count} unchanged)')
    else:
      print(f'  Found {len(itp_files)} ITP debug file(s)')
    print('')
  
  # Close the zip file
  zipf.close()
  
  # Save updated hash cache to .bt directory
  try:
    os.makedirs(bt_dir, exist_ok=True)
    with open(hash_cache_file, 'w') as f:
      json.dump(current_hashes, f, indent=2)
  except Exception as e:
    print(f'Warning: Could not save hash cache: {e}')
  
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
      f.write('Remove-Item -Path jump_sync.zip -Force\n\n')
      
      # Write sync timestamp back to local machine via mapped drive
      f.write('# Write sync timestamp back to local machine (validates hash cache)\n')
      sync_timestamp_path = sync_timestamp_file.replace('\\', '\\\\')
      f.write(f'$timestamp = (Get-Date).ToString("o")\n')
      f.write(f'$timestamp | Out-File -FilePath "{sync_timestamp_path}" -Encoding UTF8 -Force\n\n')
      
      f.write('Remove-Item -Path jump_sync.ps1 -Force\n\n')
      
      f.write('Write-Host ""\n')
      f.write('Write-Host "Sync completed successfully!" -ForegroundColor Green\n')
  
  # Display completion message with instructions
  print('')
  print('=' * 60)
  print('*** Sync package created successfully!')
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
