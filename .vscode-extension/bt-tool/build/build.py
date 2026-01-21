#!/usr/bin/env python

# Standard python modules
import glob
import os
import re
import sys

# Local modules
import data
from announce import Announce
from cmdline  import ParseCommandLine
from error    import ErrorMessage
from logger   import Logger
from misc     import GetBuildType, GetWarnings, GetBmcInfo, GetAlert, GetITP
from postbios import PostBIOS
from run      import FilterCommand, DoCommand

# Import progress tracker from same directory
import_dir = os.path.dirname(os.path.abspath(__file__))
if import_dir not in sys.path:
    sys.path.insert(0, import_dir)
from progress_tracker import ProgressTracker

# Logger for the build command
class BuildLogger(Logger):

  # Constructor
  # dir:    Directory for log file
  # warn:   True if warnings are to be logged, False otherwise
  # name:   Platform name
  # btype:  Build type (DEBUG or RELEASE)
  # returns nothing
  def __init__(self, dir, warn = False, name = None, btype = None):
    self.passed = False
    self.warn   = warn
    self.count  = 0
    self.progress = ProgressTracker(dir, name, btype, width=40)
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
  # line:   Line of output (or None for timeout update)
  # returns nothing
  def Process(self, line):
    # Handle timeout updates (when line is None)
    if line is None:
      # Check if we should force an update based on elapsed time
      if self.progress.ShouldForceUpdate():
        self.UpdateStatusLine()
      return
    
    self.count += 1
    
    # Check if we're processing a module (INF file)
    # EDK2 build output format: "  Building ... <path>.inf [<arch>]"
    if b'Building ... ' in line and b'.inf [' in line:
      self.progress.IncrementModule()
    
    if line.startswith(b'- Done -') or line.startswith(b'-- Build Ok --'):
      self.passed = True
    
    # Handle line counting and error/warning detection from parent class
    self.lines += 1
    self.progress.linesProcessed = self.lines
    
    # Update progress based on line count
    if self.progress.linesProcessed > self.progress.totalLines:
      self.progress.totalLines = self.progress.linesProcessed + int(self.progress.linesProcessed * 0.1)
    self.progress.UpdateProgress()
    
    decoded_line = line.decode('utf-8')
    if self.log: self.log.write(decoded_line.rstrip() + '\n')
    
    # Check for errors and warnings using parent's regex patterns
    quick = self.reQuick.search(decoded_line)
    if quick:
      error = self.reError.search(decoded_line)
      if error and self.IsReal('error', decoded_line, error):
        self.errors += 1
        self.Print('***  ERROR  ***', decoded_line)
      elif self.warn:
        warn = self.reWarn.search(decoded_line)
        if warn and self.IsReal('warn', decoded_line, warn):
          self.warnings += 1
          self.Print('*** WARNING ***', decoded_line)
    
    # Always update the status line
    self.UpdateStatusLine()
  
  # Save progress data to cache (only called on successful builds)
  # returns nothing
  def SaveProgress(self):
    if self.lines > 0:
      # Force progress to 100% now that build is complete
      self.progress.totalLines = self.progress.linesProcessed
      self.progress.UpdateProgress()
      self.UpdateStatusLine()
      print()  # Final newline after progress bar
      # Save the actual line count for next build
      self.progress.SaveLineCount(os.path.dirname(data.lcl.base), self.progress.name, self.lines)
  
  # Update the status line with progress information
  # returns nothing
  def UpdateStatusLine(self):
    # Update status line with progress bar included
    # Format: mm:ss, ####:#####/##### bar##%, Error #
    progress_str = self.progress.GetProgressString()
    elapsed_str = self.progress.GetElapsedTime()
    
    # Extract bar and percentage from progress string (no brackets now)
    if '%' in progress_str:
      pct_match = progress_str.split(']')
      if len(pct_match) > 1:
        # Old format still has brackets, extract them
        bar_part = pct_match[0].replace('[', '')  # ████░░░░
        pct_part = pct_match[1]                    # ##%
      else:
        bar_part = progress_str.replace('%', '')
        pct_part = '%'
    else:
      bar_part = progress_str
      pct_part = ''
    
    # Default to empty progress bar if none set yet
    if not bar_part or '[' in bar_part:
      bar_part = '░' * 40
      pct_part = '0%'
    
    msg = '\r{0}, {1}:{2}/{3} {4}{5}, Error {6}{7}'.format(
      elapsed_str,
      self.progress.modulesBuilt,
      self.lines,
      self.progress.totalLines,
      bar_part,
      pct_part,
      self.errors,
      ', Warnings {0}'.format(self.warnings) if self.warn else ''
    )
    self.length = len(msg)
    print(msg, end='', flush=True)


# Get all the burn.bin files for platform build
# base:  Base of the BIOS tree to be purged
# plat:  Platform to purge
# btype: build type to purge
# returns nothing
def GetBurnBins(base, plat, btype):
  spec = "Build\\Images\\" + plat + "\\" + btype + "\\" + plat + "*burn.bin"
  return glob.glob(os.path.join(base, spec))

# Build command hanlder
# returns 0 on success, DOES NOT RETURN otherwise
def build():
  # Get command line information
  prms, opts = ParseCommandLine({'debug': False, 'release': False, 'warnings': False, 'upload': False, 'itp': False}, 0)
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

  # Get ITP setting
  itp = GetITP()
  if opts['itp']: itp = True

  # Setup for filtering build command
  directory = os.path.dirname(data.lcl.base)
  bld       = BuildLogger(directory, warning, name, btype)

  # Execute build command
  cmd       = 'hpbuild.bat -b {0} -P {1} --UDRIVE'.format(btype, name)
  if itp:
    cmd = cmd + ' -D TXT_ACM_PRODUCTION=FALSE'
  upload    = False
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
      # Remove any burn.bin files that may confuse things
      for filePath in GetBurnBins(directory, name, btype):
        os.remove(filePath)
      upload = True

  print('Executing: {0}'.format(cmd))
  try:
    rc = FilterCommand(cmd, bld.Process, directory)
    
    # Save progress if build was successful
    if rc == 0 and bld.passed:
      bld.SaveProgress()

    if not rc and upload:
      print('')
      burnBins = GetBurnBins(directory, name, btype)
      script = '{0}\\upload.ps1'.format(os.path.dirname(os.path.abspath(__file__)))
      command = 'powershell.exe -File {0} "{1}" {2} {3} {4}'.format(script, burnBins[0], bmc['ip'], bmc['user'], bmc['password'])
      rc2 = DoCommand('Uploading BIOS Image', 'Upload', command, directory)

    # Send email alert (if enabled)
    if GetAlert():

      # Local alert is enabled
      email = data.gbl.GetItem('email')  # Email does not have to be set
      if (email):

        commands = []

        # Global email is set
        script = '{0}\\send.ps1'.format(os.path.dirname(os.path.abspath(__file__)))
        command = 'powershell.exe -File {0} {1} "{2}<eom>" ""'.format(script, email, 'Build successful!' if rc == 0 else 'Build FAILED!')
        commands.append(command)

        if not rc and upload:
          command = 'powershell.exe -File {0} {1} "{2}<eom>" ""'.format(script, email, 'Upload successful!' if rc2 == 0 else 'Upload FAILED!')
          commands.append(command)
        
        PostBIOS(commands)

  except KeyboardInterrupt:
    pass

  # Return results
  return bld.passed
