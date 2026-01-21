# Extension Testing Checklist

## Pre-Testing Setup
- [ ] Extension compiled successfully (`npm run compile`)
- [ ] BT tool bundled (`npm run bundle-bt`)
- [ ] Have a UEFI workspace available for testing

## Launch Testing
1. [ ] Press F5 to launch Extension Development Host
2. [ ] Open a UEFI workspace (with `hpbuild.bat` or `hpbuild.sh`)
3. [ ] Extension activates (check Output > Extension Host for logs)
4. [ ] "BIOS Tool" icon appears in Activity Bar

## UI Components
### Tree View
- [ ] Click BIOS Tool icon in Activity Bar
- [ ] Platforms are discovered and displayed
- [ ] Current platform is marked with ★
- [ ] Refresh button (↻) works
- [ ] Build button (⚙) appears next to platforms

### Status Bar
- [ ] Current platform shown in status bar (bottom)
- [ ] Click status bar item opens platform picker
- [ ] Can switch platforms from status bar

## Commands Testing
### Platform Management
- [ ] **BT: Init** (`Ctrl+Shift+P` > "BT: Init")
  - Shows platform picker
  - Initializes selected platform
  - Updates current platform indicator

- [ ] **BT: Select Platform** 
  - Right-click platform in tree view
  - Platform switches correctly

### Build Commands
- [ ] **BT: Build** 
  - Opens terminal
  - Runs build command
  - Shows progress (if available)
  - Errors appear in Problems panel

- [ ] **BT: Clean**
  - Cleans build artifacts
  - Terminal output visible

### VCS Commands
- [ ] **BT: Status**
  - Shows file changes
  - Displays in terminal

- [ ] **BT: Switch**
  - Lists repositories and worktrees
  - Current workspace marked with ★
  - Can switch to different workspace
  - "Open in new/current window" prompt works

- [ ] **BT: Pull**
  - Pulls changes from remote

- [ ] **BT: Push**
  - Pushes changes to remote

- [ ] **BT: Merge**
  - Merges changes

### Worktree Management
- [ ] **BT: Create**
  - Prompts for branch name
  - Prompts for worktree path
  - Prompts for commit-ish (optional)
  - Creates worktree
  - Opens in new window

- [ ] **BT: Destroy**
  - Lists existing worktrees
  - Destroys selected worktree

- [ ] **BT: Move**
  - Prompts for new path
  - Moves worktree

### Repository Management
- [ ] **BT: Attach**
  - Opens folder picker
  - Validates git/svn repository
  - Adds to repositories list
  - Updates tree view

- [ ] **BT: Detach**
  - Lists attached repositories
  - Removes selected repository
  - Updates tree view

### Navigation
- [ ] **BT: Top**
  - Navigates to top of repository

- [ ] **BT: Config**
  - Opens config interface

## Output & Diagnostics
- [ ] Output channel "BIOS Tool" exists
- [ ] Command output appears in output channel
- [ ] Build errors populate Problems panel
- [ ] File paths in errors are clickable

## Terminal Integration
- [ ] "BIOS Tool" terminal is created/reused
- [ ] Commands execute in correct directory
- [ ] Terminal output is readable
- [ ] Progress bars display correctly (if supported)

## Edge Cases
- [ ] Open workspace without `hpbuild.bat`/`hpbuild.sh` - extension should not activate
- [ ] No platforms found - shows appropriate message
- [ ] Cancel command prompts - handles gracefully
- [ ] BT command fails - shows error message
- [ ] Switch to non-existent path - handles gracefully

## Performance
- [ ] Extension activates quickly
- [ ] Platform discovery is fast
- [ ] Tree view updates responsively
- [ ] No memory leaks during repeated commands

## Cross-Platform (if applicable)
- [ ] Works on Windows
- [ ] Works on Linux (if UEFI dev supported)
- [ ] Works on macOS (if UEFI dev supported)

## Notes
- Extension logs: View > Output > Extension Host
- Extension Development Host Console: Help > Toggle Developer Tools
- BT command output: View > Output > BIOS Tool

## Found Issues
<!-- Document any issues found during testing below -->

---

**Testing Date:** _________  
**Tester:** _________  
**VS Code Version:** _________  
**Extension Version:** 0.7.0
