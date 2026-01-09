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

  # Make sure there are no uncommited changes
  if info._VCSInfo__vcs.HasUncommitedChanges():
    ErrorMessage('Unable to pull because there are uncommited changes')
    # DOES NOT RETURN

  # Pull operation for SVN is an update
  if info._VCSInfo__vcs._VCS__name == "svn":
    cmd = 'svn update'

  # Pull operation for git
  else:
    cmd = 'git pull --rebase'

  rc = DoCommand('Syncing with upstream repository', 'Pull Operation', cmd, info.Repo())

  return rc
