#!/usr/bin/env python

# Standard python modules
import os
import sys

# Local modules
import data
from   error      import ErrorMessage
from   run        import FilterCommand
from   misc       import FixPath, FixStr
from   vcs        import AutoSelectRepo, SetWorktree, FindWorkTreeFromPartialPath

# Global variables
gbl    = None       # For holding BIOS tool global settings
lcl    = None       # For holding BIOS tool local  settings
info   = None       # For holding VCS  information
Output = []         # For holding command output

# Add line to output
# line:   Line of text to be added
# retruns nothing
def KeepLines(line):
  global Output
  Output.append(line)

# A class for holding and modifying BIOS tool settings
class BIOSSettings:

  # Constructor
  # base:     directory containing current settings
  # possible: possible settings
  # returns   nothing
  def __init__(self, base, possible):
    assert base     and type(base)     is str
    assert possible and type(possible) is str
    # Save givens
    self.base     = base
    self.possible = os.path.join(os.path.dirname(os.path.abspath(__file__)), possible)
    # Handle case where setting file does not exist
    if not os.path.isfile(self.possible): return
    # Load current settings
    self.items    = []
    self.readonly = []
    self.prompt   = {}
    with open(self.possible) as possible:   # Get possible settings from file
      for line in possible.readlines():     # Loop through each setting
        item = line.strip()
        if item[0] == '*':                  # Readonly?
          items = item[1:].split(',')
          item  = items[0].strip()
          self.readonly.append(item)        # Add to readonly setting
          self.prompt[item] = '' if len(items) == 1 else items[1].strip()
        else:                             # Handle read/write settings
          self.items.append(item)
        self.GetItem(item)                # Get setting value

  # Get a configuration setting item
  # item:   Item to get
  # returns Value of item (if set) or '' if unset  
  def GetItem(self, item):
    assert item and ((item in self.items) or (item in self.readonly))
    # Assume unset
    value = ''
    # Already loaded?
    if hasattr(self, item):
      # Get loaded value
      value = getattr(self, item)
    else:
      # Setting file exist?
      name = os.path.join(self.base, item)
      if (os.path.isfile(name)):
        # Get value from file
        with open(name, 'r') as file:
          value = file.read()
    setattr(self, item, value)
    return value

  # Set a configuration setting item
  # item:   Item to set
  # returns nothing
  # Note: The readonly notion is not enforced here but in the config command
  def SetItem(self, item, value = ''):
    assert item and ((item in self.items) or (item in self.readonly))
    # Set attribute value of item
    setattr(self, item, value)
    # Save value to file
    if not os.path.isdir(self.base):
      # Make directory
      os.mkdir(self.base)
    name = os.path.join(self.base, item)
    with open(name, 'w') as file:
      file.write(value)

# Gets the indicated setting
# obj:    Object from which to get the setting
# name:   Name of the setting to get
# msg:    Command(s) for configuring setting (in case setting is not yet configured)
#         (place {0} in msg string where program name is to be inserted)
# returns Value of setting
def GetSetting(obj, name, msg):
  assert isinstance(obj, BIOSSettings)
  # Get indicated setting
  setting = obj.GetItem(name)
  # Make sure setting has been given
  if (not setting):
    ErrorMessage('Item "{0}" not configured (use "{1}" to set)'.format(name, msg.format(gbl.program)))
    # DOES NOT RETURN
  return setting
    
# Get settings
# returns Nothing
def InitializeSettings():
  global Output

  # Determine execution environment
  supported ={
    'linux':  'Linux',
    'linux2': 'Linux',
    'darmin': 'OS X',
    'win32':  'Windows',
  }
  platform = sys.platform
  if platform not in supported:
    ErrorMessage(f'Unsuppored plattfom: {platform}')
  platform = supported[platform]

  # Detect if running WSL
  if platform == 'Linux':
    platform = 'Linux' if os.system('uname -a | grep "WSL"') else 'WSL' 

  # Get user's home directory
  env  = 'USERPROFILE' if platform == 'Windows' else 'HOME'
  home = os.getenv(env)
  if home == None:
    ErrorMessage(f'Environment Variable not set: {env}')
    # DOES NOT RETURN

  # Load global settings
  data.gbl          = data.BIOSSettings(os.path.join(home, '.bt'), 'global.txt')
  data.gbl.cmdDir   = os.path.dirname(os.path.abspath(__file__))
  data.gbl.program  = os.path.splitext(os.path.basename(sys.argv[0]))[0].lower()
  data.gbl.platform = platform

  # Start with no repos and no worktrees
  data.gbl.repos     = []
  data.gbl.worktrees = []

  # Get repositories
  selected           = False  # Assume selected repo is not found in available repos
  if hasattr(data.gbl, 'repositories'):
    # Split into individual repos
    repos = data.gbl.repositories.split(';')
    # Loop through repos
    for repo in repos:
      # Make sure directory exists and has a VCS repository
      repo = repo.lower()
      if os.path.isdir(repo):
        # Handle svn repo
        if os.path.isdir(os.path.join(repo, '.svn')):
          data.gbl.repos.append(repo)                         # Add repository to list
        # Handle git repo
        elif os.path.isdir(os.path.join(repo, '.git')):
          data.gbl.repos.append(repo)                         # Add repository to list
          # Get worktrees within repo
          Output = []                                         # Start with no output
          FilterCommand('git worktree list', KeepLines, repo) # Get list of worktrees
          if Output:                                          # Make sure worktree(s) were found
            for line in Output[1:]:                           # Don't include repo in worktree list
              parts = line.split()                            # Split worktree info
              name = FixStr(parts[0].lower())                 # Get worktree name
              name = FixPath(name)
              data.gbl.worktrees.append(name)                 # Add worktree to list
        # Handle mistaken repo
        else:
          continue
        # Update selected (if found)
        if data.gbl.repo != None:
          if repo == data.gbl.repo:
            selected = True                                   # Match for selected repo found

  # Handle case where selected repo not found
  if not selected:
    Show = False
    if data.gbl.repo:
      print('Selected repository is not present: {0}'.format(data.gbl.repo))
      Show = True
    # Pick the best repo
    AutoSelectRepo(Show)

  # Get current worktree (if any)
  data.gbl.worktree = None              # Assume None
  current = os.getcwd().lower()         # Get current directory
  worktree = FindWorkTreeFromPartialPath(current)
  if worktree:
    SetWorktree(worktree)

# Keeps track of the last worktree used
# returns nothing
def SetLast():
  last = os.path.join(data.gbl.base,'last')
  if data.gbl.worktree:
    with open(last, 'w') as file:
      file.write('{0}, {1}'.format(os.path.dirname(data.gbl.worktree), os.path.basename(data.gbl.worktree)))
  else:
    if os.path.isfile(last):
      os.remove(last)
