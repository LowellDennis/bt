#!/usr/bin/env python

# Standard python modules
import os
import sys
import subprocess
import socket

# Local modules
import data
from cmdline  import ParseCommandLine
from error    import ErrorMessage
from misc     import GetJumpStationInfo

# Jump command handler - syncs source and build artifacts to Jump Station
# returns 0 on success, DOES NOT RETURN otherwise
def jump():
  # Get command line information
  prms, opts = ParseCommandLine({'check': False}, 1)
  # DOES NOT RETURN if invalid options or parameters are found

  # Get jumpstation configuration
  jump_info = GetJumpStationInfo()
  if not jump_info:
    ErrorMessage('Jump station not configured.\n' +
                 'Set using: bt config jumpstation <host>;<user>;<password>;<destination>')
    # DOES NOT RETURN

  # Convert local path on remote system to UNC path
  # E.g., "C:\Users\Admin\Desktop\GNext" -> "\\10.14.38.211\C$\Users\Admin\Desktop\GNext"
  remote_path = jump_info['dest']
  host = jump_info['host']
  
  # Check if it's already a UNC path
  if remote_path.startswith('\\\\'):
    destination = remote_path
  else:
    # Convert local path to UNC path (e.g., C:\path -> \\host\C$\path)
    if len(remote_path) >= 2 and remote_path[1] == ':':
      drive = remote_path[0]
      path_without_drive = remote_path[2:].lstrip('\\')
      destination = f'\\\\{host}\\{drive}$\\{path_without_drive}'
    else:
      ErrorMessage(f'Invalid remote path format: {remote_path}\n' +
                   'Expected: C:\\path\\to\\folder or \\\\host\\share\\path')
      # DOES NOT RETURN
  
  # If /check option, verify configuration and connectivity
  if opts['check']:
    return check_jumpstation(jump_info, destination)
  
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
    # Platform format: HpeProductLine\Volume\HpPlatforms\U68Pkg
    build_dir = os.path.join(source_dir, 'Build', platform.replace('/', os.sep))
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
  
  # Authenticate with the network share
  # Extract the share path (e.g., \\host\C$ from \\host\C$\path\to\folder)
  parts = destination.lstrip('\\').split('\\')
  if len(parts) >= 2:
    share_path = f'\\\\{parts[0]}\\{parts[1]}'
    
    print(f'Authenticating to {share_path}...')
    
    # Get credentials
    user = jump_info['user']
    pswd = jump_info['pswd']
    host_from_dest = parts[0]
    
    # Use net use to authenticate
    net_use_cmd = ['net', 'use', share_path, f'/user:{user}', pswd]
    
    try:
      result = subprocess.run(net_use_cmd, capture_output=True, text=True, timeout=10)
      if result.returncode == 0 or 'already in use' in result.stderr.lower() or 'multiple connections' in result.stderr.lower():
        print(f'  Network share authenticated')
        print('')
      else:
        ErrorMessage(f'Authentication failed: {result.stderr.strip()}')
        # DOES NOT RETURN
    except Exception as e:
      ErrorMessage(f'Authentication error: {str(e)}')
      # DOES NOT RETURN

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

  # Check if remote has git repository
  remote_git = os.path.join(destination, '.git')
  use_git_sync = False
  local_commit = None
  
  if os.path.exists(remote_git):
    # Get local commit
    try:
      result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                            cwd=source_dir, capture_output=True, text=True, timeout=5)
      if result.returncode == 0:
        local_commit = result.stdout.strip()
        use_git_sync = True
        print('Remote has git repository - will use git to sync')
        print(f'  Target commit: {local_commit[:12]}')
        print('')
      else:
        print('Warning: Could not get local git commit, falling back to robocopy')
        print('')
    except Exception as e:
      print(f'Warning: Git check failed: {str(e)}, falling back to robocopy')
      print('')
  else:
    print('Remote has no git repository - will use robocopy for initial sync')
    print('')

  # Sync source files
  if use_git_sync:
    # Use git to sync - much faster than robocopy
    print('Syncing source files using git...')
    print('')
    
    try:
      # Git doesn't work well with UNC paths, use pushd to map temporarily
      # Run git commands via cmd.exe with pushd/popd
      
      # Check for uncommitted changes on remote
      print('  Checking remote repository status...')
      print(f'  Command: pushd "{destination}" && git status --porcelain && popd')
      git_status_cmd = f'pushd "{destination}" && git status --porcelain && popd'
      result = subprocess.run(['cmd', '/c', git_status_cmd],
                            capture_output=True, text=True, timeout=30)
      
      if result.returncode != 0:
        print(f'  Warning: Could not check remote git status')
        if result.stderr.strip():
          print(f'  {result.stderr.strip()}')
        print('  Falling back to robocopy...')
        print('')
        use_git_sync = False
      elif result.stdout.strip():
        # Remote has uncommitted changes - stash them
        print('  Remote has uncommitted changes - stashing...')
        print(f'  Command: pushd "{destination}" && git stash && popd')
        git_stash_cmd = f'pushd "{destination}" && git stash && popd'
        result = subprocess.run(['cmd', '/c', git_stash_cmd],
                              capture_output=False, text=True, timeout=30)
        if result.returncode != 0:
          print(f'  Warning: Could not stash changes')
          print('  Falling back to robocopy...')
          print('')
          use_git_sync = False
        else:
          print('  ✓ Changes stashed')
      else:
        print('  ✓ Working tree clean')
      
      if use_git_sync:
        # Checkout the target commit
        print('')
        print(f'  Switching remote to commit {local_commit[:12]}...')
        print(f'  Command: pushd "{destination}" && git checkout {local_commit} && popd')
        print('')
        print('  --- Git Output (from remote) ---')
        git_checkout_cmd = f'pushd "{destination}" && git checkout {local_commit} && popd'
        result = subprocess.run(['cmd', '/c', git_checkout_cmd],
                              capture_output=False, text=True, timeout=300)
        print('  --- End Git Output ---')
        
        if result.returncode == 0:
          print('')
          print('  ✓ Source sync complete (git checkout)')
          print('')
        else:
          print('')
          print(f'  Warning: Git checkout failed (exit code {result.returncode})')
          print('  Falling back to robocopy...')
          print('')
          use_git_sync = False
    
    except Exception as e:
      print(f'  Warning: Git sync failed: {str(e)}')
      print('  Falling back to robocopy...')
      print('')
      use_git_sync = False
  
  if not use_git_sync:
    # Fallback to robocopy
    print('Syncing source files using robocopy...')
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
  
  if not use_git_sync:
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

# Check Jump Station connectivity and configuration
# jump_info: Dictionary with jump station configuration
# destination: The converted UNC destination path
# returns 0 on success, DOES NOT RETURN otherwise
def check_jumpstation(jump_info, destination):
  host = jump_info['host']
  user = jump_info['user']
  remote_path = jump_info['dest']
  
  print('')
  print('Jump Station Configuration Check')
  print('=' * 60)
  print(f'Host:        {host}')
  print(f'Username:    {user}')
  print(f'Remote Path: {remote_path}')
  print(f'UNC Path:    {destination}')
  print('')
  
  # Check 1: Verify IP/hostname is reachable
  print('Checking network connectivity...')
  try:
    # Try to resolve hostname
    ip_address = socket.gethostbyname(host)
    print(f'  ✓ Resolved {host} to {ip_address}')
    
    # Try to ping (optional, may fail due to firewall)
    result = subprocess.run(['ping', '-n', '1', '-w', '1000', host], 
                          capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
      print(f'  ✓ Host is reachable (ping successful)')
    else:
      print(f'  ⚠ Ping failed (may be blocked by firewall, but host resolved)')
  except socket.gaierror:
    print(f'  ✗ Failed to resolve hostname: {host}')
    print('')
    return 1
  except Exception as e:
    print(f'  ⚠ Network check warning: {str(e)}')
  
  print('')
  
  # Check 2: Verify destination path is accessible
  print('Checking destination path accessibility...')
  
  # First, try to authenticate with the network share
  # Extract the share path (e.g., \\host\C$ from \\host\C$\path\to\folder)
  parts = destination.lstrip('\\').split('\\')
  if len(parts) >= 2:
    share_path = f'\\\\{parts[0]}\\{parts[1]}'
    
    print(f'  Authenticating to {share_path}...')
    
    # Use net use to authenticate
    pswd = jump_info['pswd']
    net_use_cmd = ['net', 'use', share_path, f'/user:{user}', pswd]
    
    try:
      result = subprocess.run(net_use_cmd, capture_output=True, text=True, timeout=10)
      if result.returncode == 0 or 'already in use' in result.stderr.lower() or 'multiple connections' in result.stderr.lower():
        print(f'  ✓ Network share authenticated')
      else:
        print(f'  ✗ Authentication failed: {result.stderr.strip()}')
        print('')
        return 1
    except Exception as e:
      print(f'  ✗ Authentication error: {str(e)}')
      print('')
      return 1
  
  if not os.path.exists(destination):
    print(f'  ✗ Destination path not accessible: {destination}')
    print(f'  Possible issues:')
    print(f'    - Network path not mounted')
    print(f'    - Incorrect credentials')
    print(f'    - Path does not exist on remote system')
    print('')
    return 1
  else:
    print(f'  ✓ Destination path is accessible')
    
    # Try to write a test file to verify write permissions
    test_file = os.path.join(destination, '.bt_jump_test')
    try:
      with open(test_file, 'w') as f:
        f.write('test')
      os.remove(test_file)
      print(f'  ✓ Write permissions verified')
    except Exception as e:
      print(f'  ✗ Cannot write to destination: {str(e)}')
      print('')
      return 1
  
  print('')
  
  # Check 3: Verify we're in a worktree
  if not data.gbl.worktree:
    print('Not in a worktree - cannot check file counts or git status')
    print('Navigate to a worktree to perform full check')
    print('')
    return 0
  
  source_dir = data.gbl.worktree
  platform = data.lcl.GetItem('platform')
  
  # Check 4: Use git to efficiently determine what needs syncing
  print('Checking git commit status...')
  
  local_commit = None
  remote_commit = None
  commits_match = False
  
  # Get local commit
  try:
    result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                          cwd=source_dir, capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
      local_commit = result.stdout.strip()
      print(f'  Local commit:  {local_commit[:12]}')
      
      # Check if remote has .git directory
      remote_git = os.path.join(destination, '.git')
      if os.path.exists(remote_git):
        # Try to read remote commit - git often fails with UNC paths
        # Use git --git-dir to specify the .git location directly
        result = subprocess.run(['git', '--git-dir', remote_git, '--work-tree', destination, 'rev-parse', 'HEAD'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
          remote_commit = result.stdout.strip()
          print(f'  Remote commit: {remote_commit[:12]}')
          
          if local_commit == remote_commit:
            print(f'  ✓ Local and remote are at the same commit')
            commits_match = True
          else:
            print(f'  ⚠ Local and remote commits differ')
            print(f'      Will use git to switch remote to local commit')
        else:
          # Git failed - likely due to UNC path issues
          print(f'  ⚠ Could not read remote git commit')
          print(f'      Will use robocopy for sync')
          print(f'      (Git may not work with UNC paths: {destination})')
      else:
        print(f'  ⚠ Remote has no git repository')
        print(f'      Will use robocopy for initial sync')
        print(f'      (This is normal for first sync)')
    else:
      print(f'  ⚠ Could not read local git commit')
  except Exception as e:
    print(f'  ⚠ Git check failed: {str(e)}')
  
  print('')
  
  # Check 5: Analyze files to sync using git
  print('Analyzing files to sync...')
  
  if commits_match:
    # Commits match - only check for local modifications
    try:
      # Check for modified, added, or untracked files
      result = subprocess.run(['git', 'status', '--porcelain'], 
                            cwd=source_dir, capture_output=True, text=True, timeout=10)
      if result.returncode == 0:
        status_lines = [line for line in result.stdout.strip().split('\n') if line]
        
        if status_lines:
          # Count different types of changes
          modified = [l for l in status_lines if l.startswith(' M') or l.startswith('M')]
          added = [l for l in status_lines if l.startswith('A') or l.startswith('??')]
          
          total_changes = len(status_lines)
          print(f'  Source changes: {total_changes} modified/new files')
          print(f'    - Modified: {len(modified)}')
          print(f'    - New/Untracked: {len(added)}')
        else:
          print(f'  ✓ No source file changes (commits match, working tree clean)')
      else:
        print(f'  ⚠ Could not check git status')
    except Exception as e:
      print(f'  ⚠ Git status check failed: {str(e)}')
  else:
    # Commits differ - will use git checkout
    print(f'  Commits differ - will use git checkout on remote')
    print(f'  Remote will be switched to commit {local_commit[:12]}')
  
  # Check build artifacts
  if platform:
    # Platform format: HpeProductLine\Volume\HpPlatforms\U68Pkg
    # Build directory: Build\HpeProductLine\Volume\HpPlatforms\U68Pkg
    build_dir = os.path.join(source_dir, 'Build', platform.replace('/', os.sep))
    if os.path.exists(build_dir):
      print(f'  Build artifacts: Will sync from {platform}')
    else:
      print(f'  ⚠ Build directory not found: {build_dir}')
  else:
    print(f'  Platform not set - build artifacts will not be synced')
  
  print('')
  print('=' * 60)
  print('Configuration check complete!')
  print('')
  print('Run "bt jump" to perform the sync.')
  print('=' * 60)
  print('')
  
  return 0
