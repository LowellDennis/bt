#!/usr/bin/env python

# Standard python modules
import os
import sys

# Local modules
import data
from cmdline  import ParseCommandLine
from error    import ErrorMessage
from postbios import PostCMD, PostBIOS
from run      import DoCommand
from vcs      import GetVCSInfo

INPUT = raw_input if sys.version_info.major == 2 else input

# Destroy command handler
# returns 0 on success, DOES NOT RETURN otherwise
def destroy():
  # Get command line information
  prms, opts = ParseCommandLine({'keep': False}, 1)
  # Does not return if invalid options or parameters are found

  # Get path of worktree to be destroyed
  cwd  = os.getcwd()
  path = prms[0] if prms else cwd
  
  # Find worktree from full or partial path
  info     = GetVCSInfo(data.gbl.worktrees, path, 'worktree', True)
  worktree = info.VCS().Base()
  repo     = info.Repo()
  branch   = data.lcl.GetItem('branch')

  # Get confirmation from user remove it
  print('About to remove worktree {0}!\nThis will delete {0} from your system!'.format(worktree))
  while True:
    response = INPUT('Proceed [n]/y ? ')
    if not response: response = 'n'
    choice = response[0].lower()
    if choice in 'ny': break
    print('Invalid response: {0}'.format(response))

  # If user agreed ... get rid of worktree
  if choice == 'y':
  
    # Move away from directoy being removed (if needed)
    cmds = []
    if cwd.lower() == worktree:
      cmds += [repo[0:2], 'cd {0}'.format(repo)]

    # Add command for removing a worktree
    cmd  = 'git worktree remove --force {0}'.format(worktree)
    cmds += PostCMD(cmd, 'Removing worktree', 'Destroy Worktree')

    # Handle removal of associate branch (unless instructed to leave it)
    if not opts['keep'] and branch:
      # Check if branch is used by other worktrees before deleting
      cmd = 'git worktree list | findstr /I "{0}" >nul || git branch -D {0}'.format(branch)
      cmds += PostCMD(cmd, 'Removing branch (if not in use)', 'Destroy Branch')

    PostBIOS(cmds)

  return 0
