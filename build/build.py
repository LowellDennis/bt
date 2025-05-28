#!/usr/bin/env python

# Standard python modules
import os
import re
import sys

# Local modules
import data
from announce import Announce
from cmdline  import ParseCommandLine
from error    import ErrorMessage
from logger   import Logger
from misc     import GetBuildType, GetWarnings, GetBmcInfo, GetAlert
from postbios import PostBIOS
from run      import FilterCommand

bld    = None

# Logger for the build command
class BuildLogger(Logger):

  # Constructor
  # dir:    Directory for log file
  # warn:   True if warnings are to be logged, False otherwise
  # returns nothing
  def __init__(self, dir, warn = False):
    self.passed = False
    self.warn   = warn
    self.count  = 0
    self.Load()
    Logger.__init__(self, 'Build.log', 'Building', warn)

  # Prints output
  # prefix: Prefix to include in optput
  # line:   Line of output
  # result: Variable in which to return information (if needed)
  # returns nothing
  def Print(self, prefix, line):
    Logger.Print(self, '{0:>6}'.format(self.count), line)

  # Indicates if a line is a real error or warning
  # which:  'error' for error, 'warn' otherwise
  # line :  Line to check
  # result: Variable in which to return information (if needed)
  # returns True if real error or warning, False otherwise
  def IsReal(self, which, line, result):
    # Eliminate false positives
    for regex in self.regex:
      if regex.search(line): return False
    return True

  # Loads the regular expressions
  # returns nothing
  def Load(self):
    self.regex = []
    filter = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'filter.txt')
    if os.path.isfile(filter):
      with open(filter, 'r') as txt:
        patterns = txt.readlines()
        for pattern in patterns:
          self.regex.append(re.compile(pattern.rstrip(), re.IGNORECASE))

  # Processes a line of output
  # line:   Line of output
  # returns nothing
  def Process(self, line):
    self.count += 1
    if (line.startswith(b'-- Build Ok --')): self.passed = True
    Logger.Process(self, line)

# Build command hanlder
# returns 0 on success, DOES NOT RETURN otherwise
def build():
  # Get command line information
  prms, opts = ParseCommandLine({'debug': False, 'release': False, 'warnings': False, 'upload': False}, 0)
  # DOES NOT RETURN if invalid options or parameters are found

  # Validate options
  if opts['debug'] and opts['release']:
    ErrorMessage('/debug and /release options are mutually axclusive')

  # Get platform name
  name     = data.GetSetting(data.lcl, 'name', '{0} init')
  # DOES NOT RETURN if name is not set

  # Get build type
  btype    = GetBuildType()
  if opts['debug']:   btype = 'DEBUG'
  if opts['release']: btype = 'RELEASE'

  # Get warnings setting
  warning  = GetWarnings()
  if opts['warnings']: warning = True

  # Setup for filtering build command
  directory = os.path.dirname(data.lcl.base)
  bld       = BuildLogger(directory, warning)

  # Execute build command
  cmd       = 'hpbuild.bat -b {0} -P {1} --UDRIVE'.format(btype, name)
  if opts['upload']:
    bmc = GetBmcInfo()
    if not bmc:
      ErrorMessage('Unable to upload because local bmc setting is not set')
      # DOES NOT RETURN

    # Handle iLO
    if bmc['bmc'] == 'iLO':
      cmd = cmd + ' -I {0}'.format(bmc['ip'])
    # Handle OpenBMC
    else:
      ErrorMessage('OpenBMC upload support TBD')
      # DOES NOT RETURN

  print('Executing: {0}'.format(cmd))
  try:
    rc      = FilterCommand(cmd, bld.Process, directory)

    # Send email alert (if enabled)
    if GetAlert():

      # Local alert is enabled
      email = data.gbl.GetItem('email')  # Email does not have to be set
      if (email):

        # Global email is set
        script = '{0}\\send.ps1'.format(os.path.dirname(os.path.abspath(__file__)))
        command = 'powershell.exe -File {0} {1} "{2}<eom>" ""'.format(script, email, 'successful!' if rc == 0 else 'FAILED!')
        PostBIOS([command])

  except KeyboardInterrupt:
    pass

  # Return results
  return bld.passed
