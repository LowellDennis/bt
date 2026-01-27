#!/usr/bin/env python

# Standard python modules
import os
import sys
import subprocess

# Local modules
import data
from cmdline  import ParseCommandLine
from error    import ErrorMessage
from misc     import GetJumpStationInfo

# Jump command handler - syncs source and build artifacts to Jump Station
# returns 0 on success, DOES NOT RETURN otherwise
def jump():
  # Get command line information
  prms, opts = ParseCommandLine(None, 2)
  # DOES NOT RETURN if invalid options or parameters are found

  # Determine destination
  destination = None
  save_destination = False
  
  if len(prms) > 0:
    # Destination provided on command line
    destination = prms[0]
    save_destination = True
  else:
    # Try to get from jumpstation setting
    jump_info = GetJumpStationInfo()
    if jump_info:
      destination = jump_info['dest']
    else:
      ErrorMessage('No destination specified and jumpstation setting not configured.\n' +
                   'Usage: bt jump <destination-path>\n' +
                   'Or set: bt config jumpstation <host>;<user>;<password>;<destination>')
      # DOES NOT RETURN

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
  if platform:
    build_dir = os.path.join(source_dir, 'Build', platform)
    if not os.path.exists(build_dir):
      print(f'  Warning: Build directory not found: {build_dir}')
      print(f'  Will sync source only. Build the project first with: bt build')
      print('')
      build_dir = None

  # Confirm sync
  print('')
  print('Jump Station Sync')
  print('=================')
  print(f'Source:      {source_dir}')
  if build_dir:
    print(f'Build:       {build_dir}')
  print(f'Destination: {destination}')
  print('')

  # Ask to save if this is a new destination
  if save_destination:
    response = input('Save this destination in .bt/jumpstation setting? (y/n): ').strip().lower()
    if response == 'y' or response == 'yes':
      # Get additional info for full jumpstation setting
      print('')
      print('Enter Jump Station connection details:')
      host = input('  Hostname or IP: ').strip()
      user = input('  Username: ').strip()
      pswd = input('  Password: ').strip()
      
      # Save the setting
      jumpstation_value = f'{host};{user};{pswd};{destination}'
      data.lcl.SetItem('jumpstation', jumpstation_value)
      print('  Saved jumpstation setting')
      print('')

  # Robocopy exclude patterns
  exclude_dirs = [
    '.git',
    '__pycache__',
    '.vscode',
    '.history',
    'node_modules',
    '.venv'
  ]
  
  exclude_files = [
    '*.pyc',
    '*.pyo',
    '*.pyd',
    '.gitignore',
    '.gitattributes'
  ]

  # Sync source files
  print('Syncing source files...')
  print('')
  
  # Build robocopy command for source
  robocopy_cmd = ['robocopy', source_dir, destination, '/E', '/MT:8', '/R:2', '/W:5']
  
  # Add exclude directories
  for exc_dir in exclude_dirs:
    robocopy_cmd.extend(['/XD', exc_dir])
  
  # Add exclude files
  for exc_file in exclude_files:
    robocopy_cmd.extend(['/XF', exc_file])
  
  # Add progress indicators
  robocopy_cmd.extend(['/NP', '/NDL', '/NFL'])
  
  # Run robocopy for source
  try:
    result = subprocess.run(robocopy_cmd, capture_output=False, text=True)
    
    # Robocopy return codes:
    # 0 = No files copied, no failures, no mismatches
    # 1 = Files copied successfully
    # 2 = Extra files or directories detected
    # 3 = Files copied and extra files detected
    # 4+ = Errors occurred
    if result.returncode >= 8:
      ErrorMessage(f'Source sync failed with robocopy error code {result.returncode}')
      # DOES NOT RETURN
    
    print('')
    print('  Source sync complete')
    print('')
    
  except Exception as e:
    ErrorMessage(f'Failed to run robocopy: {str(e)}')
    # DOES NOT RETURN

  # Sync build artifacts if available
  if build_dir:
    print('Syncing build artifacts...')
    print('')
    
    build_dest = os.path.join(destination, 'Build', platform)
    
    # Build robocopy command for build artifacts
    # Include specific file types for debugging
    build_cmd = [
      'robocopy', build_dir, build_dest,
      '/E', '/MT:8', '/R:2', '/W:5',
      '/NP', '/NDL', '/NFL'
    ]
    
    try:
      result = subprocess.run(build_cmd, capture_output=False, text=True)
      
      if result.returncode >= 8:
        ErrorMessage(f'Build artifacts sync failed with robocopy error code {result.returncode}')
        # DOES NOT RETURN
      
      print('')
      print('  Build artifacts sync complete')
      print('')
      
    except Exception as e:
      ErrorMessage(f'Failed to sync build artifacts: {str(e)}')
      # DOES NOT RETURN

  print('=' * 60)
  print('Jump Station sync completed successfully!')
  print('=' * 60)
  print('')

  return 0
