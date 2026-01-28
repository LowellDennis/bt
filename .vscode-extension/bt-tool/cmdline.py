#!/usr/bin/env python 

# Standard python modules
import os
import sys

# Local modules
import data
from abbrev   import UniqueAbbreviation
from error    import UsageError

# Checks options and parameters on the command line
# options: option information dictionary (tuples containing (name, arg))
#          name  Option name string
#          arg   True if option takes an argument, False otherwise
# max:     maximum number of parameters
#          (-1 indicates unknown number of parameters)
# returns  tuple with parameter array (sys.argv with options removed)
#                and  option    dictionary (True if simple option found
#                                           Value if option take as argument)
def ParseCommandLine(options = None, max = 0):
  # Start with no parameters and no options
  cnt   = 0
  prms  = []
  opts  = {}

  # Initialize options
  # (Set all to false since not encountered yet)
  if options:
    for opt in options:
      opts[opt] = False

  # Create abbreviaiton dictionary for the options
  unique = UniqueAbbreviation(options)

  # Loop through remaining command line
  idx  = 3
  argc = len(sys.argv)
  while idx <= argc:

    # Check for option
    arg = sys.argv[idx-1]
    if arg[0] in ('/', '-'):
      if arg[1:] in unique:

        # Get option information
        opt = unique[arg[1:]]
        flg = options[opt]

        # See if option has a argument
        if flg:

          # Make sure there are enough arguments for option
          idx += 1
          if idx > argc:
            UsageError('Missing argument for {0} option'.format(arg))
            # DOES NOT RETURN

          # Save option argument
          opts[opt] = sys.argv[idx-1]

        # Option does not have an argument
        # Mark it True for found on command line
        else:
          opts[opt] = True

      # Option not found in unique array
      else:
        UsageError('Invalid option: {0}'.format(arg))
        # DOES NOT RETURN

    # It must be a parameter
    else:
      # Make sure the maximum number of parameters has not been exceeded
      if max != -1 and len(prms) >= max:
        UsageError('Too many paramters: {0}'.format(arg))
        # DOES NOT RETURN

      # Save parameter
      prms.append(arg)

    # Next argument
    idx += 1

  # Return tuple with both arrays
  return (prms, opts)
