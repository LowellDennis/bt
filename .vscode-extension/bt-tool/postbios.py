#!/usr/bin/env python 

# Standard python modules
import os

# Local modules
# None

POSTCMD = 'postbt.cmd'
Counter = 1

# Genrates script for performing a command
# cmd: Command to be performed
# msg: What command actually does
# op:  Operation carried out by command
# returns nothing
def PostCMD(cmd, msg, op):
  global Counter
  assert type(cmd) is str
  assert type(msg) is str
  assert type(op)  is str
  equalLine  = '=' * (58 + len(msg))
  starLine   = '*' * (16 + len(op))
  exclamLine = '!' * (16 + len(op))
  # Generate script with given information
  cmds = [ 'echo {0}'.format(equalLine),
           'echo === {0} ... Please be patient this could take a while ... ==='.format(msg),
           'echo {0}'.format(equalLine),
           'echo Command: {0}'.format(cmd),
           '{0}'.format(cmd),
           'echo. ',
           'if %ERRORLEVEL% neq 0 goto :ERROR{0}'.format(Counter),
           'echo {0}'.format(starLine),
           'echo *** {0} Passed! ***'.format(op),
           'echo {0}'.format(starLine),
           'goto :Done{0}'.format(Counter),
           ':ERROR{0}'.format(Counter),
           'echo {0}'.format(exclamLine),
           'echo *** {0} FAILED! ***'.format(op),
           'echo {0}'.format(exclamLine),
           ':Done{0}'.format(Counter)
         ]
  Counter += 1
  # Return script 
  return cmds

# Genrates post execution script
# commands: List of commands to be performed
# returns nothing
def PostBIOS(commands):
  assert type(commands) is list
  # Get TEMP environment variable
  temp = os.getenv('TEMP', '.')
  # Open POSTBIOS.CMD
  with open(os.path.join(temp, POSTCMD), 'w') as f:
    # Turn off echo in CMD file
    f.write('@echo off\n')
    # Write commands to CMD file
    for command in commands:
      f.write(command + '\n')
