#!/usr/bin/env python

# Standard python modules
import os
import sys

# Local modules
import data
from   abbrev     import UniqueAbbreviation
from   error      import NotABiosTree, UnrecognizedCommand

# Constants
NEEDS_VCS     = 'needs.vcs'
TERSE_HELP    = 'terse.txt'
DETAILS_HELP  = 'details.txt'
USAGE_HELP    = 'usage.txt'
COMMAND_FILES = {'terse':   TERSE_HELP,
                 'details': DETAILS_HELP,
                 'code':    '' }

# Global data
Abbreviate    = { }
Commands      = { }

# BIOS utility command class
class Command:

  # Constructor
  # dir:    Path to command directory
  # returns nothing
  def __init__(self, dir):
    assert dir and dir != ''
    # Import command
    base = os.path.basename(dir)    # Get name of command
    sys.path.insert(0,dir)          # Add its directory to the python path
    exec('import {0}'.format(base)) # Import it!
    # Load help text from files
    for key in ('terse', 'details'):
      with open(os.path.join(dir, COMMAND_FILES[key])) as txt:
        setattr(self, key, txt.read().strip())
    # Indicate need for presence in VCS tree
    setattr(self, "needsVcs", os.path.isfile(os.path.join(dir, NEEDS_VCS)))
    # Set up execution
    cmd = 'self.code = {0}.{0}'.format(base)
    exec(cmd)

  # Processing command specific help
  # level:  Level of help needed (terse or details)
  # returns help text
  def Help(self, level):
    return getattr(self, level)

  # Indicates command need for VCS
  # returns True if command needs VCS, False otherwise
  def NeedsVCS(self):
    return self.needsVcs
  
  # Runs the command
  # returns nothing
  def Run(self):
    self.code()

# Gets command information
# cmd: Command to be loaded
# returns command
def GetCommand(cmd):
  # Only interested in directories
  dir = os.path.join(data.gbl.cmdDir, cmd)
  if (not os.path.isdir(dir)): return None
  # Must have help files and code
  COMMAND_FILES['code'] = cmd + '.py'
  for key in COMMAND_FILES:
    if (not os.path.isfile(os.path.join(dir, COMMAND_FILES[key]))): return None
  return Command(dir)

# Gets command name from possilbe abbreviation
# command: Potentailly abbreviated command
# returns  Unabreviated command or None if not found or ambiguous
def IsCommand(command):
  global Abbreviate
  cmd = command.lower()
  if (cmd in Abbreviate): return Abbreviate[cmd]
  return None

# Show terse help for each command
# returns nothing
def ShowTerseHelp():
  # Display program help
  print('usage: {0} <command> [param1 [param2 [...]]]'.format(data.gbl.program))
  print('  where command is one of:')
  # Include terse help for each command
  for cmd in sorted(Commands):
    print('    {0:>8} - {1}'.format(cmd, Commands[cmd].Help('terse')))
  print('\nNOTE: command can be abbreviated as afar as it does not conflict with\n      another command abbreviation')
  print('\nFor detailed help on a particular command use "{0} help <command>"'.format(data.gbl.program))

# Show detailed help for a command
# returns nothing
def ShowDetailedHelp():
  # Determine command for which detailed help is needed
  command = sys.argv[2]
  # Make sure it exists
  cmd     = IsCommand(command)
  if (cmd):
    print('\nSummary\n-------')
    print(Commands[cmd].Help('terse'))
    print('')
    print(Commands[cmd].Help('details'))
  else:
    UnrecognizedCommand(command)
    # DOES NOT RETURN

# Load commands supported by this utility
# returns Nothing
def LoadCommands():
  global Abbreviate, Command
  # Get contents of command directory
  lst = os.listdir(data.gbl.cmdDir)
  # Loop through list of potential commands
  for cmd in lst:
    # Add valid command to the command table
    command = GetCommand(cmd)
    if (command): Commands[cmd] = command        
  # Create unique command abbreviation table
  Abbreviate = UniqueAbbreviation(Commands)

# Dipatch the appropriate command
# returns nothing
def DispatchCommand():
  global Commands

  # Handle basic help
  argc = len(sys.argv)
  if (argc < 2): ShowTerseHelp()
  else:
    # Get command
    command = sys.argv[1]
    # Handle help
    if (command.lower() == 'help'):
      # Differentiate between basic and detailed help
      ShowTerseHelp() if (argc == 2) else ShowDetailedHelp()
    else:
      # Make sure command exists
      cmd = IsCommand(command)
      # Handle command
      if (cmd):
        # Make sure command can be executed
        if (data.gbl.worktree == None) and (Commands[cmd].NeedsVCS()):
          NotABiosTree()
          # DOES NOT RETURN
        # Run the command
        data.SetLast()             # Indicate last worktree accessed
        Commands[cmd].Run()
      else:
        # Command not found
        UnrecognizedCommand(command)
        # DOES NOT RETURN
