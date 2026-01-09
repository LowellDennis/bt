#!/usr/bin/env python

# Standard python modules
import os
import sys

# Local modules
import data
from cmdline  import ParseCommandLine
from error    import UsageError

# Init command handler
# returns 0 on success, DOES NOT RETURN otherwise
def status():
  # Get command line information
  prms, opts = ParseCommandLine(None, 1)
  # DOES NOT RETURN if invalid options or parameters are found

  # See if all is indicated
  all = False   # Assume not incluing all
  if prms:
    if prms[0].lower in ('a', 'al', 'all'):
      all = True
    else:
      UsageError('Unrecognized parameter: {0}'.format(prms[0]))
      # DOES NOT RETURN

  # Display status
  return data.gbl.vcs.Status(all)
