#!/usr/bin/env python

# Standard python modules
import os
import sys

# Local modules
import data
from cmdline  import ParseCommandLine
from error    import ErrorMessage
from run      import DoCommand
from vcs      import GetVCSInfo

# Init command handler
# returns 0 on success, DOES NOT RETURN otherwise
def pull():
  # Get command line information
  prms, opts = ParseCommandLine({'merge': True}, 1)
  # DOES NOT RETURN if invalid options or parameters are found

  # Get partial name of target repositoy or worktree to be pulled
  tgt = prms[0] if prms else os.getcwd()

  # Determine full path of repository or worktree to be pulled
  info = GetVCSInfo(data.gbl.repos + data.gbl.worktrees, tgt.lower(), 'either', True)

  # Make sure repository or worktree was found
  if not info:
    ErrorMessage('Could not find {0} in list of repositories and worktrees'.format(tgt))
    # DOES NOT RETURN

  # Handle merge case
  if opts['merge']:
    # Make sure target is a worktree
    if info.IsRepo():
      ErrorMessage('Merge operation requires a worktree')
      # DOES NOT RETURN

    # Perform merge operation
    cmd = 'git merge {0}'.format(opts['merge'])
    rc = DoCommand('Merging changes from parent repository', 'Merge Operation', cmd, info.Repo())

  else:
    # Perform pull operation
    cmd = 'git pull --rebase' if info.VCS()._VCS__name == 'git' else 'svn update'
    rc = DoCommand('Syncing with upstream repository', 'Pull Operation', cmd, info.Repo())

  return rc
