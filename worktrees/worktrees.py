#!/usr/bin/env python

# Standard python modules
import os
import sys

# Local modules
import data
from cmdline  import ParseCommandLine
from error    import ErrorMessage
from vcs      import GetVCSInfo, GetRepoFromWorktree, GetBranchFromWorktree, GetAllWorktreeInfo

# Get the purpose for a worktree
# worktree: Full path to the worktree
# returns: Purpose string or empty string if not set
def GetWorktreePurpose(worktree):
  purpose_file = os.path.join(worktree, data.SETTINGS_DIRECTORY, 'purpose')
  if os.path.isfile(purpose_file):
    try:
      with open(purpose_file, 'r') as f:
        return f.read().strip()
    except:
      return ''
  return ''

# Worktrees command handler
# returns 0 on success, DOES NOT RETURN otherwise
def worktrees():
  # Get command line information
  prms, opts = ParseCommandLine(None, 1)
  # DOES NOT RETURN if invalid options or parameters are found

  # Check if we have any worktrees
  worktrees_list = data.gbl.worktrees
  if not worktrees_list:
    print('  No worktrees (use "bt create" to create one).')
    return 0

  # Are we showing all worktrees or just one?
  if len(prms) == 0:
    # Show all worktrees
    vcs = 'git'
    print('')
    print('  Available worktrees (currently selected worktree has *)')
    print('  vcs worktree, repository, branch, purpose')
    print('  --- -----------------------------------------------')
    
    # Use cached worktree info from initialization (fast!)
    worktree_info = getattr(data.gbl, 'worktree_cache', None)
    
    if worktree_info:
      # Use cached data - no git commands needed!
      for item in worktrees_list:
        info = worktree_info.get(item, {})
        repo = info.get('repo', '')
        branch = info.get('branch', '')
        purpose = GetWorktreePurpose(item)
        star = '*' if item == data.gbl.worktree else ' '
        print('{0} {1} {2}, {3}, {4}, {5}'.format(star, vcs, item, repo, branch, purpose))
    else:
      # Fallback: get info in single git command
      worktree_info = GetAllWorktreeInfo(worktrees_list)
      if worktree_info:
        for item in worktrees_list:
          info = worktree_info.get(item, {})
          repo = info.get('repo', GetRepoFromWorktree(item))
          branch = info.get('branch', GetBranchFromWorktree(item))
          purpose = GetWorktreePurpose(item)
          star = '*' if item == data.gbl.worktree else ' '
          print('{0} {1} {2}, {3}, {4}, {5}'.format(star, vcs, item, repo, branch, purpose))
      else:
        # Final fallback to original method
        for item in worktrees_list:
          repo = GetRepoFromWorktree(item)
          branch = GetBranchFromWorktree(item)
          purpose = GetWorktreePurpose(item)
          star = '*' if item == data.gbl.worktree else ' '
          print('{0} {1} {2}, {3}, {4}, {5}'.format(star, vcs, item, repo, branch, purpose))
  else:
    # Show detailed info for a specific worktree
    given = prms[0]
    info = GetVCSInfo(worktrees_list, given, 'worktree', True)
    if not info:
      ErrorMessage('Unable to find matching worktree: {0}'.format(given))
      # DOES NOT RETURN
    
    worktree = info.VCS().Base()
    repo = info.Repo()
    branch = GetBranchFromWorktree(worktree)
    purpose = GetWorktreePurpose(worktree)
    
    print('')
    print('Worktree Information')
    print('====================')
    print('Path:       {0}'.format(worktree))
    print('Repository: {0}'.format(repo))
    print('Branch:     {0}'.format(branch))
    print('Purpose:    {0}'.format(purpose if purpose else '(not set)'))
    print('')

  return 0
