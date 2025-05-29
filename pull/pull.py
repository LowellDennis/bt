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
  prms, opts = ParseCommandLine(None, 1)
  # DOES NOT RETURN if invalid options or parameters are found

  # Get partial name of target repositoy or worktree to be pulled
  tgt = prms[0] if prms else os.getcwd()

  # Determine full path of repository or worktree to be pulled
  info = GetVCSInfo(data.gbl.repos + data.gbl.worktrees, tgt.lower(), 'either', True)

  # Make sure repository or worktree was found
  if not info:
    ErrorMessage('Could not find {0} in list of repositories and worktrees'.format(tgt))
    # DOES NOT RETURN

  # Pull operation is not available with SVN
  if info._VCSInfo__vcs._VCS__name == "svn":
    ErrorMessage('Pull operation cannot be performed on an SVN repository (use "bt upodate")')
    # DOES NOT RETURN
    
  # Perform pull operation
  cmd = 'git pull --rebase'
  rc = DoCommand('Syncing with upstream repository', 'Pull Operation', cmd, info.Repo())

  return rc
