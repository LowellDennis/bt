#!/usr/bin/env python

# Standard python modules
import os
import sys

# Local modules
import data
from cmdline  import ParseCommandLine
from error    import ErrorMessage, UsageError
from run      import DoCommand
from vcs      import GetVCSInfo

# Init command handler
# returns 0 on success, DOES NOT RETURN otherwise
def merge():
  # Get command line information
  prms, opts = ParseCommandLine({'target': True}, 1)
  # DOES NOT RETURN if invalid options or parameters are found

  # Make sure commit-ish is given
  if len(prms) != 1:
    UsageError('commit-ish not given')
    # DOES NOT RETURN

  # Get partial name of target repositoy or worktree
  tgt = opts['target'] if opts['target'] else os.getcwd()

  # Determine full path of repository or worktree
  info = GetVCSInfo(data.gbl.repos + data.gbl.worktrees, tgt.lower(), 'either', True)

  # Make sure repository or worktree was found
  if not info:
    ErrorMessage('Could not find {0} in list of repositories and worktrees'.format(tgt))
    # DOES NOT RETURN

  # Make sure there are no uncommited changes
  if info._VCSInfo__vcs.HasUncommitedChanges():
    ErrorMessage('Unable to merge because there are uncommited changes')
    # DOES NOT RETURN

  # Perform merge operation
  cmd = '{0} merge {1}'.format(info._VCSInfo__vcs._VCS__name, prms[0])
  rc = DoCommand('Merging changes into local repository', 'Update Operation', cmd, info.Repo())

  return rc
