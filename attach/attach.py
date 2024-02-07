#!/usr/bin/env python

# Standard python modules
import os
import sys

# Local modules
import data
from error    import ErrorMessage
from cmdline  import ParseCommandLine
from vcs      import GetVCSInfo, UpdateRepos, AutoSelectRepo

# Attach command hanlder
# returns 0 on success, DOES NOT RETURN otherwise
def attach():
  # Get command line information
  prms, opts = ParseCommandLine(None, 1)
  # DOES NOT RETURN if invalid options or parameters are found

  # Get target repo to be attached
  tgt = prms[0] if len(prms) > 0 else os.getcwd()

  # Get repo from full or partial path
  info = GetVCSInfo(data.gbl.repos, tgt.lower(), 'repository', False)

  # Do not add it if is not a repository
  if not info:
    # Already there
    ErrorMessage('Not a repository: {0}'.format(tgt))
    # DOES NOT RETURN

  # Do not add it if it is already there
  if info.IsListed():
    # Already there
    ErrorMessage('Repository already attached: {0}'.format(tgt))
    # DOES NOT RETURN

  # Add it!
  repo = info.VCS().Base()
  print('Attaching {0}'.format(repo))
  data.gbl.repos.append(repo.lower())
  UpdateRepos()
  if data.gbl.repo == None:
    AutoSelectRepo
  return 0
