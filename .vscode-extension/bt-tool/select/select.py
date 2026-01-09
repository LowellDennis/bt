#!/usr/bin/env python

# Standard python modules
import os
import sys

# Local modules
import data
from cmdline  import ParseCommandLine
from vcs      import GetVCSInfo

# Init command handler
# returns 0 on success, DOES NOT RETURN otherwise
def select():
  # Get command line information
  prms, opts = ParseCommandLine(None, 1)
  # DOES NOT RETURN if invalid options or parameters are found

  # Setting or listing?
  if len(prms) == 0:

    # List repositories
    repo  = data.gbl.GetItem('repo')     # Get currently selected repository 
    print('  Available repositories (currently selected repository has *)')
    print('    vcs repository')
    print('  - --- ------------------------------------------------------')
    for item in data.gbl.repos:
      asterisk = '*' if (repo == item) else ' '
      path     = os.path.join(item, '.git')
      vcs      = 'git' if os.path.exists(path) else 'svn'
      print('  {0} {1} {2}'.format(asterisk, vcs, item))
  else:
  
    # Select repo from full or partial path
    info = GetVCSInfo(data.gbl.repos, sys.argv[2], 'repository', True)
    # Does not return on error
    
    repo = info.VCS().Base()
    data.gbl.SetItem('repo', repo)
    print('Selected repository = {0}'.format(repo))
