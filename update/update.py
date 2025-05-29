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
def update():
  # Get command line information
  prms, opts = ParseCommandLine(None, 1)
  # DOES NOT RETURN if invalid options or parameters are found

  # Get partial name of target repositoy to be updates
  tgt = prms[0] if prms else os.getcwd()

  # Determine full path of repository to e updated
  info = GetVCSInfo(data.gbl.repos + data.gbl.worktrees, tgt.lower(), 'either', True)

  # Make sure repository was found
  if not info:
    ErrorMessage('Could not find {0} in list of repositories'.format(tgt))
    # DOES NOT RETURN

  # Update operation is not available with git
  if info._VCSInfo__vcs._VCS__name == "git":
    ErrorMessage('Update operation cannot be performed on an git repository or worktree (use "bt pull")')
    # DOES NOT RETURN
    
  # Perform pull operation
  cmd = 'svn update'
  rc = DoCommand('Syncing with upstream repository', 'Update Operation', cmd, info.Repo())

  return rc
