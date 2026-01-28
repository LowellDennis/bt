#!/usr/bin/env python

# Standard python modules
import os
import sys

# Local modules
import data
from cmdline  import ParseCommandLine
from error    import ErrorMessage
from postbios import PostBIOS
from vcs      import GetVCSInfo, GetRepoFromWorktree, GetBranchFromWorktree, GetAllWorktreeInfo

# Global variables
Prms = None

# Use command handler
# returns 0 on success, DOES NOT RETURN otherwise
def use():
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
      print('')
      
      # Use cached worktree info from initialization (fast!)
      worktree_info = getattr(data.gbl, 'worktree_cache', None)
      
      # Collect all data first to calculate column widths
      rows = []
      if worktree_info:
        # Use cached data - no git commands needed!
        for item in data.gbl.worktrees:
          info = worktree_info.get(item, {})
          repo = info.get('repo', '')
          branch = info.get('branch', '')
          star = '*' if item == data.gbl.worktree else ' '
          rows.append((star, vcs, item, repo, branch))
      else:
        # Fallback: get info in single git command
        worktree_info = GetAllWorktreeInfo(data.gbl.worktrees)
        if worktree_info:
          for item in data.gbl.worktrees:
            info = worktree_info.get(item, {})
            repo = info.get('repo', GetRepoFromWorktree(item))
            branch = info.get('branch', GetBranchFromWorktree(item))
            star = '*' if item == data.gbl.worktree else ' '
            rows.append((star, vcs, item, repo, branch))
        else:
          # Final fallback to original method
          for item in data.gbl.worktrees:
            repo = GetRepoFromWorktree(item)
            branch = GetBranchFromWorktree(item)
            star = '*' if item == data.gbl.worktree else ' '
            rows.append((star, vcs, item, repo, branch))
      
      # Calculate maximum widths for alignment
      if rows:
        max_worktree_len = max(len(row[2]) for row in rows)
        max_repo_len = max(len(row[3]) for row in rows)
        
        # Ensure minimum width for headers
        max_worktree_len = max(max_worktree_len, len('Worktree'))
        max_repo_len = max(max_repo_len, len('Repository'))
        
        # Print header
        print(f'  VCS {"Worktree":<{max_worktree_len}}  {"Repository":<{max_repo_len}}  Branch')
        print(f'  --- {"-" * max_worktree_len}  {"-" * max_repo_len}  ------')
        
        # Print table with aligned columns
        for star, vcs, worktree, repo, branch in rows:
          print(f'{star} {vcs} {worktree:<{max_worktree_len}}  {repo:<{max_repo_len}}  {branch}')
      
      print('')
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
