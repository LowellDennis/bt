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
def push():
  # Get command line information
  prms, opts = ParseCommandLine(None, 1)
  # DOES NOT RETURN if invalid options or parameters are found

  # Get partial name of target repositoy or worktree to be pushed
  tgt = prms[0] if prms else os.getcwd()

  # Determine full path of repository or worktree to be pushed
  info = GetVCSInfo(data.gbl.repos + data.gbl.worktrees, tgt.lower(), 'either', True)

  # Make sure repository or worktree was found
  if not info:
    ErrorMessage('Could not find {0} in list of repositories and worktrees'.format(tgt))
    # DOES NOT RETURN
  
  # Push is only available for to GIT
  if info.VCS()._VCS__name == 'svn':
    ErrorMessage('Push operation cannot be performed on an SVN repository (use "svn commit")')
    # DOES NOT RETURN

  # Perform push operation
  cmd = 'git push'
  rc = DoCommand('Pushing local update to upstream repository', 'Push Operation', cmd, info.Repo())
  return rc
