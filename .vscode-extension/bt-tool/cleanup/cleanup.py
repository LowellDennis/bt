#!/usr/bin/env python

# Standard python modules
import os
import re

# Local modules
import data
from announce import Announce
from cmdline  import ParseCommandLine
from run      import FilterCommand

# Cleans build artefacts
# target: Target directory to be cleaned
#         (either BUILD or BUILDR)
# returns 0 on success, DOES NOT RETURN otherwise
def PerformClean(target):
  rc = 0
  try:
    # Do not need to clean if indicated path does not exist
    path = os.path.join(data.gbl.worktree, target)
    if os.path.isdir(path):
      cmd = 'cmd.exe /C rmdir /S /Q {0}'.format(path)
      print('Executing: {0}'.format(cmd))
      rc = FilterCommand(cmd, directory = data.gbl.worktree)
    else:
      print('No need to clean {0}'.format(target))
  except KeyboardInterrupt:
    rc = 1
  return rc

# Cleanup command handler
# returns 0 on success, DOES NOT RETURN otherwise
def cleanup():
  global cln

  # Get command line information
  prms, opts = ParseCommandLine(None, 0)
  # DOES NOT RETURN if invalid options or parameters are found

  # Get platform name
  # (makes sure this is a repository or worktree that has been initialized)
  name     = data.GetSetting(data.lcl, 'name', '{0} init')
  # DOES NOT RETURN if name is not set

  # Clean normal build files
  rc = PerformClean('BUILD')

  # Show results
  print('')
  result = 'Successful' if rc == 0 else 'FAILED'
  char   = '*'          if rc == 0 else '!'
  Announce('Cleanup {0}'.format(result), char)
  return rc
