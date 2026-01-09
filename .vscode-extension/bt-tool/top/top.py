#!/usr/bin/env python 

# Standard python modules
# None

# Local modules
import data
from cmdline  import ParseCommandLine
from postbios import PostBIOS

# Top command handler
# returns 0 on success, DOES NOT RETURN otherwise
def top():
  # Get command line information
  prms, opts = ParseCommandLine(None, 0)
  # DOES NOT RETURN if invalid options or parameters are found
  PostBIOS([ 'cd {0}'.format(data.gbl.worktree)])
  return 0
