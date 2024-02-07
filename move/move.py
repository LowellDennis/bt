#!/usr/bin/env python

# Standard python modules
import os
import sys

# Local modules
import data
from error    import ErrorMessage, UsageError
from cmdline  import ParseCommandLine
from postbios import PostBIOS
from vcs      import GetRepoFromWorktree, GetWorktree

# Global variables
Prms     = None
Worktree = None

# Determines if an item is in the path
# returns True if item is in path, False otherwise
def IsInList(items, path):
  found = None
  for item in items:
    low = item.lower()
    common = os.path.commonprefix([item, path])
    if common == item:
       found = item
       break
  return found

# Determine if src is a valid source path
# src:    Path to be checked for validity
# returns Repositoru of source path on sucess, DOES NOT RETURN otherwise
def CheckSourcePath(src):
  global Prms, Worktree
  
  # Get information on source directory
  Worktree, Info  = GetWorktree(Prms, idx = 1)
  # DOES NOT RETURN on error

  # Determine repo from which the worktree came
  repo = GetRepoFromWorktree(Worktree)
  # DOES NOT RETURN on error

  # Return path to repo
  print(' Parent repository: {0}'.format(repo.replace('/', '\\')))
  return repo

# Determine if src is a valid source path
# src:    Path to be checked for validity
# returns 0 on success, DOES NOT RETURN otherwise
def CheckDestinationPath(src, dst):
  # Make sure dst directory exists
  path = os.path.abspath(dst);
  if os.path.isdir(path):
    UsageError('Destination path already exists: {0}'.format(os.path.dirname(path)))
    # DOES NOT RETURN

  # See if dst itself is a directory
  if os.path.isdir(path):
    # dst retains name from src
    path = os.path.join(path, os.path.basename(src))

  else:
    # dst contains mame as well.
    # Make sure it does not exist
    if os.path.exists(path):
      UsageError('Cannot overwrite exisiting path: {0}, exists'.format(dst))
      # DOES NOT RETURN

  # Return fully quailified destination path
  print('  Target directory: {0}'.format(path))
  return path

# Generates commands to rename a worktree
# src:    Path to existing worktree (old path)
# dst:    Path to which to move     (new path)
# returns 0 on success, DOES NOT RETURN otherwise
# NOTE:   If dst is an existing directory, move src but keep name
#         If dst does not exist but its dirname does, move src and rename
def MoveWorktree(src, dst):
  # Makesure source path is good
  repo = CheckSourcePath(src)
  # DOES NOT RETURN on error

  # Make sure destination is valid
  path = CheckDestinationPath(src, dst)
  # DOES NOT RETURN on error

  # Assume cwd is not affected by the move
  cwd      = os.path.abspath(os.getcwd()).lower()
  endDir   = cwd

  # See if current directory will be affected by the move
  worktree = data.gbl.worktree
  common = os.path.commonprefix([worktree, cwd])
  if  common == worktree:
    subDir = cwd[len(worktree)+1:]
    endDir = os.path.join(path, subDir)
  else:
    endDir = path
  
  # Generate commands that will rename the worktree
  cmds = ['echo Moving worktree from {0} to {1}'.format(worktree, path),
          'cd {0}'.format(repo.replace('/', '\\')),
          'git worktree move {0} {1}'.format(worktree, path),
          'cd {0}'.format(endDir),
         ]
  return PostBIOS(cmds)

# Output worktree
# returns nothing
def List():
  print('  Available worktrees')
  print('  worktree, repository')
  print('  -----------------------------------------------')
  for item in data.gbl.worktrees:
    repo = GetRepoFromWorktree(item)
    print('  {0}, {1}'.format(item, repo))

# Moves a worktree
# returns nothing
def Move():
  global Prms
  MoveWorktree(Prms[1], Prms[0])

# Move corrent direcotry
# returns nothing
def MoveCurrent():
  MoveWorktree(os.getcwd(), Prms[0])

# Command handler based on number of arguments
# Note: argument counts of 0 and 1 are impossible here.
#       arg 0 is the program name
#       arg 1 is the command
#       could not be here i those two were not present
#
#        args, handler
Actions = { 0: List,
            1: MoveCurrent,
            2: Move
          }

# Move command handler
# returns 0 on success, DOES NOT RETURN otherwise
def move():
  global Actions, Prms

  # Get command line information
  Prms, Opts = ParseCommandLine(None, 2)
  # DOES NOT RETURN if invalid options or parameters are found

  # Dispatch action to perform
  action = Actions[len(Prms)]
  return action()
