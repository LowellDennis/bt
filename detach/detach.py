#!/usr/bin/env python

# Standard python modules
import os
import sys

# Local modules
import data
from cmdline  import ParseCommandLine
from vcs      import AutoSelectRepo, GetVCSInfo, UpdateRepos

# Detach command handler
# returns 0 on success, DOES NOT RETURN otherwise
def detach():
  # Get command line information
  prms, opts = ParseCommandLine(None, 1)
  # Does not return if invalid options or parameters are found

  # Get detach target
  tgt = os.getcwd() if len(prms) < 1 else prms[0]

  # Get repo from full or partial path
  info = GetVCSInfo(data.gbl.repos, tgt.lower(), 'repository', True)

  # Remove it!
  repo = info.VCS().Base()
  print('Detaching: {0}'.format(repo))
  data.gbl.repos.remove(repo)
  UpdateRepos()

  # Handle case where removed repo was the currently selected repo
  if repo == data.gbl.repo:
    print('Currently selected repository just removed')
    AutoSelectRepo(True)
