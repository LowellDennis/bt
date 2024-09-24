#!/usr/bin/env python

# Standard python modules
import os
import sys

# Local modules
import data
from announce import Announce
from error    import ErrorMessage, UsageError
from cmdline  import ParseCommandLine
from postbios import PostBIOS
from run      import DoCommand
from vcs      import GetVCSInfo, DoesBranchExist

# Global variables
Prms      = None
Opts      = None
Repo      = None
Branch    = None
Worktree  = None
Abstree   = None
Commitish = 'HEAD'

# Clean command handler
# returns 0 on success, DOES NOT RETURN otherwise
def create():
  global Opts, Prms, Repo, Branch, Worktree, Abstree, Commitish

  # Get command line information
  Prms, Opts = ParseCommandLine({'repo': True}, 3)
  # DOES NOT RETURN if invalid options or parameters are found

  # Make sure required parameters are given
  argc = len(Prms)
  if argc < 2:
    UsageError('worktree directory not given')
    # DOES NOT RETURN
  elif argc < 1:
    UsageError('worktree branch not given')
    # DOES NOT RETURN

  # Get parameters (with defaults)
  Branch    = Prms[0].replace("\\", "/") # Enforce that branches have slashes not backslashes
  #Branch    = Prms[0]
  Worktree  = Prms[1]
  Abstree   = os.path.abspath(Worktree)
  Commitish = "HEAD" if len(Prms) < 3 else Prms[2]

  # Make sure target directory does not exist
  if os.path.exists(Abstree):
    ErrorMessage('Directory already exists: {0}'.format(Worktree))
    # DOES NOT RETURN

  # Make sure repository exits
  Repo = data.gbl.repo
  if Opts['repo']: Repo = Opts['repo']
  if not Repo:
    UsageError('Unable to determine repo to use')
    # DOES NOT RETURN

  # Get repo information
  info = GetVCSInfo(data.gbl.repos, Repo, 'repository', False)
  if not info:
    ErrorMessage('Not a repository: {0}'.format(Repo))
    # DOES NOT RETURN

  # Make sure repo is a git repo
  if info.VCS().Name() != 'git':
    ErrorMessage('Not a git repository: {0}'.format(Repo))
    # DOES NOT RETURN

  # Make sure branch does not already exist
  if DoesBranchExist(Repo, Branch):
    ErrorMessage('Branch already exists: {0}'.format(Branch))
    # DOES NOT RETURN

  # Make sure worktree does not already exist
  if (GetVCSInfo(data.gbl.worktrees, Abstree, 'worktree', False)):
    ErrorMessage('Worktree already exists: {0}'.format(Worktree))
    # DOES NOT RETURN

  # Get command for creating worktree
  cmd  = 'git worktree add -b {0} {1} {2}'.format(Branch, Abstree, Commitish)
  # Perform create operation
  rc = DoCommand('Creating worktree', 'Create Worktree', cmd, Repo)
  if rc:
    ErrorMessage('Unable to create worktree')
    # DOES NOT RETURN

  # Save resulting branch for destroy
  name = os.path.join(Abstree, data.SETTINGS_DIRECTORY)
  os.mkdir(name)
  name = os.path.join(name, 'branch')
  with open(name, 'w') as file:
    file.write(Branch)

  # Switch to newly created worktree
  PostBIOS([Abstree[0:2], 'cd {0}'.format(Abstree)])

  # Return results
  return rc
