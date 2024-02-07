#!/usr/bin/env python

# Standard python modules
import os
import sys

# Local modules
import data
from announce import Announce
from cmdline  import ParseCommandLine
from error    import WarningMessage
from postbios import PostCMD, PostBIOS
from misc     import GetCurrentBranch
from vcs      import GetVCSInfo

INPUT = raw_input if sys.version_info.major == 2 else input

# Destroy command handler
# returns 0 on success, DOES NOT RETURN otherwise
def destroy():
  # Get command line information
  prms, opts = ParseCommandLine({'branch': False}, 1)
  # Does not return if invalid options or parameters are found

  # Get path of worktree to be destroyed
  cwd  = os.getcwd()
  path = prms[0] if prms else cwd
  
  # Find worktree from full or partial path
  info     = GetVCSInfo(data.gbl.worktrees, path, 'worktree', True)
  worktree = info.VCS().Base()
  repo     = info.Repo()
  branch   = GetCurrentBranch(worktree)

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

    # Create post execution script to perform destroy operation
    cmd =   'git worktree remove --force {0}'.format(worktree)
    cmds =  [ 'cd {0}'.format(repo) ]
    cmds += PostCMD(cmd, 'Removing worktree', 'Destroy Worktree')
    if opts['branch']:
      if branch == None:
        WarningMessage('Not on a branch ... therefore branch cannot be deleted')
      else:
        cmds.append('git branch -d {0}'.format(branch))
    if path != cwd: cmds.append('cd {0}'.format(os.path.abspath(cwd)))
    PostBIOS(cmds)

  return 0
