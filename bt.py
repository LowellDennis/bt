#!/usr/bin/env python

# Standard python modules
import os
import sys

# Local modules
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from command  import LoadCommands, DispatchCommand
from data     import InitializeSettings
from error    import NotAWorktree

# If running this file
if __name__ == '__main__':
  try:
    print('BIOS Tool V0.4')
    InitializeSettings()
    LoadCommands()
    DispatchCommand()
  except NotAWorktree as e:
    print(str(e))
  except KeyboardInterrupt:
    pass
