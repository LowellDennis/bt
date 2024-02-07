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
from vcs      import GetVCSInfo, UndefinedRepo

# Global variables
Prms = None
Opts = None
Repo = None
Work = None

# Create a git worktree command
# returns git worktree command string
def WorktreeCommand():
  global Opts, Prms, Repo, Work
  # Generate command line, format = git worktree add [-b Branch] [<path>\]Name [<Commmit>]
  command = 'git worktree add '
  if Opts['branch']: command += '-b {0} '.format(Opts['branch'])
  Work    = os.path.join(os.path.dirname(Repo), Prms[0])
  command += '{0} '.format(Work)
  command += Opts['commit'] if Opts['commit'] else 'HEAD'
  return command

# Clean command handler
# returns 0 on success, DOES NOT RETURN otherwise
def create():
  global Opts, Prms, Repo, Work

  # Get command line information
  Prms, Opts = ParseCommandLine({'repo': True, 'commit': True, 'branch': True}, 4)
  # DOES NOT RETURN if invalid options or parameters are found

  # Make sure the worktree (name or path) is given
  argc = len(Prms)
  if argc < 1:
    UsageError('worktree path not given')
    # DOES NOT RETURN

  # Make sure repository exits
  Repo = data.gbl.repo
  if Opts['repo']: Repo = Opts['repo']
  if not Repo:
    UsageError('Unable to determine repo to use')
    # DOES NOT RETURN

  # Get repo information
  info = GetVCSInfo(data.gbl.repos, Repo, 'repository', False)
  if info:

    # Make sure repo is a git repo
    if info._VCSInfo__vcs._VCS__name != 'git':
      ErrorMessage('Worktrees are only supported by git')
      # DOES NOT RETURN

    # Make sure worktree does not already exist
    if (GetVCSInfo(data.gbl.worktrees, Prms[0], 'worktree', False)):
      ErrorMessage('Worktree already exists: {0}'.format(Prms[0]))
      # DOES NOT RETURN

    # Get command for creating worktree
    cmd = WorktreeCommand()
    # Perform create operation
    rc = DoCommand('Creating worktree', 'Create Worktree', cmd, info.VCS().Base())
    if rc:
      ErrorMessage('Unable to create worktree')
      # DOES NOT RETURN

    # Switch to newly created worktree
    PostBIOS(['cd {0}'.format(Work)])
  else:
    ErrorMessage('Unable to get repo information')
    # DOES NOT RETURN

  # Return results
  return rc
