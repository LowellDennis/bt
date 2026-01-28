#!/usr/bin/env python

# Standard python modules
import os
import sys

# Local modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from command  import LoadCommands, DispatchCommand
from data     import InitializeSettings
from error    import NotAWorktree
from postbios import SetSessionId

# Extract and set session ID from command line (if provided)
# This is passed by bt.cmd/bt.ps1 for unique post-command files
def InitSessionId():
  for i, arg in enumerate(sys.argv[1:], 1):
    if arg.startswith('--btid='):
      session_id = arg.split('=', 1)[1]
      SetSessionId(session_id)
      # Remove this argument so it doesn't interfere with command parsing
      sys.argv.pop(i)
      return
  # If no btid provided, postbios will use PID as default

# If running this file
if __name__ == '__main__':
  try:
    print('BIOS Tool V1.0')
    InitSessionId()
    InitializeSettings()
    LoadCommands()
    DispatchCommand()
  except NotAWorktree as e:
    print(str(e))
  except KeyboardInterrupt:
    pass
