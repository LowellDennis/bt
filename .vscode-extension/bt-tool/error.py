#!/usr/bin/env python

# Standard python modules
import os
import sys

# Local modules
import data

# Not a worktree exception: For when a worktree is required but not found!
class NotAWorktree(Exception):

  def __init__(self, directory):
     self.directory = directory

  def __str__(self):
    dirName = os.getcwd() if not self.directory else self.directory
    return ('Directory is not part of a HPE Server BIOS git worktree: {0}'.format(dirName))

# Ambiguous partial worktree exception: For a partial worktree matches more that one worktree path!
class AmbiguousPartialWorktree(Exception):

  def __init__(self, directory):
     self.directory = directory

  def __str__(self):
    return ('Partial directory given matches more than one HPE Server BIOS git worktree: {0}'.format(self.directory))

# Write a message to stderr and exit with given error code
# message: Message to display
# returns  nothing
def WarningMessage(message):
  sys.stderr.write('*** WARNING *** {0}\n'.format(message))
  sys.stderr.flush()

# Write a message to stderr and exit with given error code
# message:   Message to display
# errorcode: Error code to use on exit
# DOES NOT RETURN
def ErrorMessage(message, errorcode = 1):
  sys.stderr.write('*** ERROR *** {0}\n'.format(message))
  sys.stderr.flush()
  sys.exit(errorcode)
  # DOES NOT RETURN

#################################################################
## The following are defined to allow error message consitency ##
## among the various places where similar errors might occur.  ##
#################################################################

# Outputs and error messge attaching instructions to get help on a command
# message: Message to be displayed
# DOE NOT RETURN
def UsageError(message):
  cmd = str.lower(sys.argv[1])
  ErrorMessage('{0} (use "{1} help {2}" for more information)'.format(message, data.gbl.program, cmd))
  # DOES NOT RETURN

# Handles condition where a BIOS tree is needed but not found
# path: path that is not a BIOS tree
#       if not given, defaults to current working directory
# DOES NOT RETURN
def NotABiosTree(path = None):
  dirName = os.getcwd() if not path else path
  ErrorMessage('Directory is not part of a HPE Server BIOS tree: {0}'.format(dirName))
  # DOES NOT RETURN

# Handles uninitialized platform error messaging
# DOES NOT RETURN
def UninitializedPlatform():
  ErrorMessage('Platform not configured (use "{0} init [target]" to configure)'.format(data.gbl.program))
  # DOES NOT RETURN

# Handles unrecognized command messaging
# command: command that is not recognized
# DOES NOT RETURN
def UnrecognizedCommand(command):
  ErrorMessage('Unrecognized command: {0} (use "{1} help" for more information)'.format(command, data.gbl.program))
  # DOES NOT RETURN

# Handles invalid option error messaging
# option:  Invalid option string
# command: Command for which option does not apply
# DOES NOT RETURN
def InvalidOption(option):
  UsageError('Invalid option: {0}'.format(option))
  # DOES NOT RETURN

# Handles too many parameters error messaging
# parameter: Parameter that caused this function to be invoked
# command:   Command for which parameter was intended
# DOES NOT RETURN
def ToManyParamters(parameter):
  UsageError('Too many parameters: {0}'.format(parameter))
  # DOES NOT RETURN

# Handles too many parameters error messaging
# item:    Argument or option that is not supported
# command: Command for which option does not apply
# DOES NOT RETURN
def NotEnoughParameters(parameter):
  UsageError('Parameters not given: {0}'.format(parametere))
  # DOES NOT RETURN
