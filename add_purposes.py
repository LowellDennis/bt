#!/usr/bin/env python3
"""
Quick script to add purposes to existing worktrees.
This is throw-away code to help populate the purpose field.
"""

import os
import sys
import subprocess

# Import the BT modules
import data
import vcs

def get_worktree_purpose(worktree_path):
    """Get the current purpose if it exists."""
    purpose_file = os.path.join(worktree_path, '.bt', 'purpose')
    if os.path.exists(purpose_file):
        with open(purpose_file, 'r') as f:
            return f.read().strip()
    return None

def set_worktree_purpose(worktree_path, purpose):
    """Set the purpose for a worktree."""
    bt_dir = os.path.join(worktree_path, '.bt')
    if not os.path.exists(bt_dir):
        os.makedirs(bt_dir)
    
    purpose_file = os.path.join(bt_dir, 'purpose')
    with open(purpose_file, 'w') as f:
        f.write(purpose)
    print(f"  ✓ Saved purpose")

def show_git_status(worktree_path):
    """Show git status for the worktree."""
    try:
        result = subprocess.run(
            ['git', 'status', '--short'],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            print("\n  Git Status:")
            for line in result.stdout.strip().split('\n'):
                print(f"    {line}")
        elif result.returncode == 0:
            print("\n  Git Status: Clean (no changes)")
    except Exception as e:
        print(f"  (Could not get git status: {e})")

def show_recent_commits(worktree_path, count=5):
    """Show recent commits for the worktree."""
    try:
        result = subprocess.run(
            ['git', 'log', f'-{count}', '--oneline', '--decorate'],
            cwd=worktree_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            print(f"\n  Recent Commits (last {count}):")
            for line in result.stdout.strip().split('\n'):
                print(f"    {line}")
    except Exception as e:
        print(f"  (Could not get commit history: {e})")

def main():
    # Initialize the data module
    data.InitializeSettings()
    
    # Check if we have any worktrees
    if not data.gbl.worktrees:
        print("No worktrees found.")
        return
    
    print(f"Found {len(data.gbl.worktrees)} worktree(s)\n")
    
    # Get cached worktree info
    worktree_cache = getattr(data.gbl, 'worktree_cache', {})
    
    for worktree_path in data.gbl.worktrees:
        info = worktree_cache.get(worktree_path, {})
        repo = info.get('repo', 'unknown')
        branch = info.get('branch', vcs.GetBranchFromWorktree(worktree_path))
        
        print(f"\n{'='*60}")
        print(f"Worktree: {worktree_path}")
        print(f"Repository: {repo}")
        print(f"Branch: {branch}")
        print('='*60)
        
        current_purpose = get_worktree_purpose(worktree_path)
        if current_purpose:
            print(f"Current Purpose: {current_purpose}")
        else:
            print("Current Purpose: (none)")
        
        # Show git status and recent commits to help remember what this worktree is for
        show_git_status(worktree_path)
        show_recent_commits(worktree_path)
        
        # Prompt for purpose
        purpose = input("\nEnter purpose (or press Enter to skip/keep current): ").strip()
        
        if purpose:
            set_worktree_purpose(worktree_path, purpose)
        else:
            if current_purpose:
                print("  ℹ Keeping existing purpose")
            else:
                print("  ℹ Skipped")
    
    print(f"\n{'='*60}")
    print("Done! Run 'bt worktrees' to see all purposes.")
    print('='*60)

if __name__ == '__main__':
    main()
