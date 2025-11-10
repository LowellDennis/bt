#!/usr/bin/env python

# Standard python modules
import os
import sys

# Local modules
import data
from cmdline  import ParseCommandLine
from error    import ErrorMessage
from postbios import PostBIOS
from vcs      import GetVCSInfo, GetRepoFromWorktree, GetBranchFromWorktree

# Global variables
Prms = None

# Init command handler
# returns 0 on success, DOES NOT RETURN otherwise
def switch():
  # Get command line information
  prms, opts = ParseCommandLine({'platform': False}, 1)
  # DOES NOT RETURN if invalid options or parameters are found

  # Setting or listing?
  if len(prms) == 0:

    # List avaialble repos
    repositories = data.gbl.repositories
    if repositories:
      print('  Available repositories (currently selected repository has *)')
      print('  vcs repository')
      print('  --- -----------------------------------------------')
      for item in repositories.split(';'):
        path = os.path.join(item, '.git')
        vcs  = 'git' if os.path.exists(path) else 'svn'
        star = '*' if item.lower() == data.gbl.repo else ' '
        print('{0} {1} {2}'.format(star, vcs, item))
    else:
      print('  No repositories (use "bt attach" to add one).')

    # List avaialble worktrees
    worktrees = data.gbl.worktrees
    if worktrees:
      vcs = 'git'
      print('')
      print('  Available worktrees (currently selected worktree has *)')
      print('  vcs worktree, repository, branch')
      print('  --- -----------------------------------------------')
      for item in data.gbl.worktrees:
        repo = GetRepoFromWorktree(item)
        branch = GetBranchFromWorktree(item)
        star = '*' if item == data.gbl.worktree else ' '
        print('{0} {1} {2}, {3}, {4}'.format(star, vcs, item, repo, branch))
    else:
      print('  No worktrees    (use "bt create" to create one).')
  else:

    # First look for worktree from full or partial path
    given = prms[0]
    which = 'worktree'
    info = GetVCSInfo(data.gbl.worktrees, given, 'worktree', True)
    if (info == None):
      # Next look for repository from full or partial path
      which = 'repository'
      info = GetVCSInfo(data.gbl.repositories.split(';'), given, 'repository', True)
      if (info == None):
        # Not found
        ErrorMessage('Unable to find matching worktree or repository: {0}'.format(given))
        # DOES NOT RETURN
    # Switch to indicated BIOS worktree or repository on exit
    item = info.VCS().Base()
    print('Selected {0} = {1}'.format(which, item))
    cmds = []
    cmds.append(item[0:2])
    cmds.append('cd {0}'.format(item))
    PostBIOS(cmds)
  return 0
