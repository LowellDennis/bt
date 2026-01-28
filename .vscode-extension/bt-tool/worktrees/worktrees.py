#!/usr/bin/env python

# Standard python modules
import os
import sys
import textwrap

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
    print('')
    print('  Available worktrees (currently selected worktree has *)')
    print('')
    
    # Use cached worktree info from initialization (fast!)
    worktree_info = getattr(data.gbl, 'worktree_cache', None)
    
    # Collect all data first to calculate column widths
    rows = []
    if worktree_info:
      for item in worktrees_list:
        purpose = GetWorktreePurpose(item)
        star = '*' if item == data.gbl.worktree else ' '
        rows.append((star, item, purpose if purpose else '(no purpose set)'))
    else:
      # Fallback
      worktree_info = GetAllWorktreeInfo(worktrees_list)
      for item in worktrees_list:
        purpose = GetWorktreePurpose(item)
        star = '*' if item == data.gbl.worktree else ' '
        rows.append((star, item, purpose if purpose else '(no purpose set)'))
    
    # Calculate maximum worktree path width
    max_worktree_len = max(len(row[1]) for row in rows) if rows else 0
    # Ensure minimum width for header
    max_worktree_len = max(max_worktree_len, len('Worktree'))
    
    # Print header
    print(f'  {"Worktree":<{max_worktree_len}}  Purpose')
    print(f'  {"-" * max_worktree_len}  -------')
    
    # Print table with aligned columns and wrapped purpose text
    # Calculate indent for wrapped lines: '* ' (2 chars) + worktree width + '  ' (2 chars)
    indent = ' ' * (2 + max_worktree_len + 2)
    
    for star, worktree, purpose in rows:
      # First line with worktree and start of purpose
      first_line_width = 100 - (2 + max_worktree_len + 2)  # Total 100 chars, minus prefix
      
      if len(purpose) <= first_line_width:
        # Purpose fits on one line
        print(f'{star} {worktree:<{max_worktree_len}}  {purpose}')
      else:
        # Need to wrap - use textwrap
        wrapped_lines = textwrap.wrap(purpose, width=first_line_width)
        # Print first line with worktree
        print(f'{star} {worktree:<{max_worktree_len}}  {wrapped_lines[0]}')
        # Print continuation lines with indent
        for line in wrapped_lines[1:]:
          print(f'{indent}{line}')
    
    print('')
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
