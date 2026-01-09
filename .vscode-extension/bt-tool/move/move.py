#!/usr/bin/env python

# Standard python modules
import os
import sys

# Local modules
import data
from error    import ErrorMessage, UsageError
from cmdline  import ParseCommandLine
from misc     import FixPath
from postbios import PostBIOS
from vcs      import GetVCSInfo

# Global constants
DIRECTORY_MARKER = '\\' if data.gbl.platform == 'Windows' else '/'

# Global variables
Cwd  = None     # Current working directory
Dest = None     # Destination directory
Opts = None     # Command line options
Prms = None     # Command line parameters
Repo = None     # Repository for worktree
Work = None     # Worktree to move

# Get and validate the destination parameter
def GetAndValidateDestination():
  global Dest
  dst  = Prms[0]
  Dest = os.path.abspath(dst)
  # Add ending directory marker if needed
  if not Dest[-1] == DIRECTORY_MARKER:
    Dest += DIRECTORY_MARKER
  # Make sure destination directory does not exist
  if os.path.exists(Dest):
    ErrorMessage('Directory already exists: {0}'.format(dst))
    # DOES NOT RETURN

# Get and validate the worktree parameter (or default)
def GetAndValidateWorktree():
  global Cwd, Repo, Work
  Cwd  = os.getcwd()
  wrk  = Prms[1] if len(Prms) > 1 else Cwd
  Work = os.path.abspath(wrk)
  # Add ending directory marker if needed
  if not Work[-1] == DIRECTORY_MARKER:
    Work += DIRECTORY_MARKER
  # Get worktree information
  info = GetVCSInfo(data.gbl.worktrees, Work, 'worktree', True)
  if not info:
    ErrorMessage('Not a worktree: {0}'.format(wrk))
    # DOES NOT RETURN
  Repo = FixPath(info.Repo())

# Move command handler
# returns 0 on success, DOES NOT RETURN otherwise
def move():
  global Cwd, Dest, Opts, Prms, Repo, Work

  # Get command line information
  Prms, Opts = ParseCommandLine(None, 2)
  # DOES NOT RETURN if invalid options or parameters are found

  # Get move source and destination
  GetAndValidateDestination()
  GetAndValidateWorktree()

  # See if directory needs to change
  needsCd = Cwd.lower().startswith(Work.lower())
  
  # Handle CD before worktree move (if needed)
  cmds = []
  if needsCd:
    cmds += [ Repo[0:2], 'cd {0}'.format(Repo) ]

  # Generate commands that will move the worktree
  cmds += ['echo Moving worktree from {0} to {1}'.format(Work, Dest),
           'git worktree move {0} {1}'.format(Work, Dest)]

  # Handle CD after worktree move (if needed)
  if needsCd:
    path = os.path.join(Dest, Cwd[len(Work):])
    cmds += [ path[0:2], 'cd {0}'.format(path) ]

  return PostBIOS(cmds)
