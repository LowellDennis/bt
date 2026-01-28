#!/usr/bin/env python
"""
BIOS Tool GUI - Graphical interface for bt build system
Provides workspace discovery, build management, and progress tracking
"""

import sys
import os
import subprocess
import glob
import re
from datetime import datetime

try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                 QHBoxLayout, QPushButton, QTextEdit, QLabel,
                                 QGroupBox, QStatusBar, QTabWidget, QMessageBox, 
                                 QInputDialog, QFileDialog, QProgressBar, QMenu, QToolButton)
    from PyQt6.QtCore import Qt, QTimer, QProcess
    from PyQt6.QtGui import QFont, QTextCursor, QKeyEvent, QTextCharFormat, QColor
except ImportError as e:
    # PyQt6 not installed - install it automatically
    import ctypes
    import subprocess
    
    # Run pip install with visible console
    process = subprocess.Popen(
        [sys.executable, '-m', 'pip', 'install', 'PyQt6'],
        creationflags=subprocess.CREATE_NEW_CONSOLE
    )
    process.wait()
    
    if process.returncode == 0:
        ctypes.windll.user32.MessageBoxW(0, 
            "PyQt6 installed successfully!\n\nPlease restart the BIOS Tool GUI.", 
            "Installation Complete", 
            0x40)  # MB_ICONINFORMATION
    else:
        ctypes.windll.user32.MessageBoxW(0, 
            f"Failed to install PyQt6.\n\nTry running manually:\n{sys.executable} -m pip install PyQt6", 
            "Installation Failed", 
            0x10)  # MB_ICONERROR
    sys.exit(1)

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class InteractiveConsole(QTextEdit):
    """Interactive console widget with command input and persistent shell session"""
    
    def __init__(self, working_directory=None, parent=None):
        super().__init__(parent)
        self.setFont(QFont('Consolas', 9))
        
        self.working_directory = working_directory or os.getcwd()
        self.command_history = []
        self.history_index = -1
        self.current_command = ""
        self.awaiting_output = False
        self.pending_prompt = ""
        
        # Tab completion state
        self.last_completion_matches = []
        self.completion_index = 0
        self.last_completion_prefix = ""
        
        # Input control
        self.input_enabled = True
        
        # Create persistent shell process
        self.shell_process = QProcess(self)
        self.shell_process.setWorkingDirectory(self.working_directory)
        self.shell_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        
        # Set environment to force Python unbuffered output
        env = QProcess.systemEnvironment()
        from PyQt6.QtCore import QProcessEnvironment
        proc_env = QProcessEnvironment()
        for item in env:
            if '=' in item:
                key, value = item.split('=', 1)
                proc_env.insert(key, value)
        proc_env.insert('PYTHONUNBUFFERED', '1')
        self.shell_process.setProcessEnvironment(proc_env)
        
        # Only connect stdout since we use MergedChannels (stderr goes to stdout)
        self.shell_process.readyReadStandardOutput.connect(self._handle_shell_output)
        self.shell_process.finished.connect(self._handle_command_finished)
        
        # Start shell and inherit environment PROMPT
        if sys.platform == 'win32':
            self.shell_process.start('cmd.exe', ['/Q'])  # /Q turns off command echo
        else:
            self.shell_process.start('bash', ['-i'])
        
        self.shell_process.waitForStarted(1000)
        
        # Wait for initial prompt to appear
        QTimer.singleShot(300, self._capture_initial_prompt)
        
        # Track where user can edit (after the prompt)
        self.prompt_position = 0
    
    def _capture_initial_prompt(self):
        """Capture the initial shell prompt"""
        output = self.shell_process.readAllStandardOutput().data().decode('utf-8', errors='replace')
        if output:
            # Display the shell's welcome and prompt
            self.insertPlainText(output)
        self.prompt_position = self.textCursor().position()
        self.ensureCursorVisible()
    
    def _handle_shell_output(self):
        """Handle output from the shell process"""
        # Note: MergedChannels mode combines stderr into stdout
        output = self.shell_process.readAllStandardOutput().data().decode('utf-8', errors='replace')
        if output:
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            cursor.insertText(output)
            self.setTextCursor(cursor)
            self.prompt_position = cursor.position()
            self.ensureCursorVisible()
    
    def _handle_command_finished(self):
        """Handle command completion"""
        # This won't be called for individual commands in an interactive shell
        pass
    
    def set_input_enabled(self, enabled):
        """Enable or disable user input"""
        self.input_enabled = enabled
        self.setReadOnly(not enabled)

    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle key presses for command input"""
        # Always allow copy (Ctrl+C) regardless of input state
        if event.key() == Qt.Key.Key_C and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.copy()
            return
        
        # Always allow select all (Ctrl+A)
        if event.key() == Qt.Key.Key_A and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.selectAll()
            return
        
        # Ignore all other input if disabled
        if not self.input_enabled:
            return
        
        # Allow paste (Ctrl+V) when input is enabled
        if event.key() == Qt.Key.Key_V and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            # Paste at end of document
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self.setTextCursor(cursor)
            self.paste()
            return
        
        cursor = self.textCursor()
        
        # Return key - execute command
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._execute_command()
            return
        
        # Tab key - command completion
        elif event.key() == Qt.Key.Key_Tab:
            self._handle_tab_completion()
            return
        
        # Up arrow - previous command in history
        elif event.key() == Qt.Key.Key_Up:
            if self.command_history:
                if self.history_index == -1:
                    self.current_command = self._get_current_command()
                    self.history_index = len(self.command_history) - 1
                elif self.history_index > 0:
                    self.history_index -= 1
                
                if self.history_index >= 0:
                    self._replace_current_command(self.command_history[self.history_index])
            return
        
        # Down arrow - next command in history
        elif event.key() == Qt.Key.Key_Down:
            if self.history_index >= 0:
                self.history_index += 1
                if self.history_index >= len(self.command_history):
                    self.history_index = -1
                    self._replace_current_command(self.current_command)
                else:
                    self._replace_current_command(self.command_history[self.history_index])
            return
        
        # Backspace - prevent deleting prompt
        elif event.key() == Qt.Key.Key_Backspace:
            if cursor.position() <= self.prompt_position:
                return
        
        # Left arrow - allow navigation but prevent editing
        elif event.key() == Qt.Key.Key_Left:
            super().keyPressEvent(event)
            return
        
        # Home - move to start of command (after prompt)
        elif event.key() == Qt.Key.Key_Home:
            cursor.setPosition(self.prompt_position)
            self.setTextCursor(cursor)
            return
        
        # For printable characters, enforce position at or after prompt
        if event.text() and cursor.position() < self.prompt_position:
            cursor.setPosition(self.prompt_position)
            self.setTextCursor(cursor)
        
        # Handle normal text input
        super().keyPressEvent(event)
    
    def _get_current_command(self):
        """Get the command currently being typed"""
        cursor = self.textCursor()
        cursor.setPosition(self.prompt_position)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        return cursor.selectedText()
    
    def _replace_current_command(self, command):
        """Replace the current command with a new one"""
        cursor = self.textCursor()
        cursor.setPosition(self.prompt_position)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        cursor.removeSelectedText()
        cursor.insertText(command)
        self.setTextCursor(cursor)
    
    def _execute_command(self):
        """Execute the current command"""
        command = self._get_current_command().strip()
        
        # Handle cls command locally to clear the screen
        if command.lower() == 'cls' or command.lower() == 'clear':
            self.clear()
            self.prompt_position = 0
            # Add to history
            if not self.command_history or self.command_history[-1] != command:
                self.command_history.append(command)
            self.history_index = -1
            # Send just newline to get a fresh prompt without echoing cls
            self.shell_process.write('\n'.encode('utf-8'))
            return
        
        # Add to history (only non-empty commands)
        if command and (not self.command_history or self.command_history[-1] != command):
            self.command_history.append(command)
        self.history_index = -1
        
        # Move cursor to end and add newline (keep the typed command visible since /Q disables echo)
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText('\n')
        self.setTextCursor(cursor)
        self.prompt_position = cursor.position()
        
        # Send command to shell (even if empty, to get a new prompt)
        self.awaiting_output = True
        self.shell_process.write((command + '\n').encode('utf-8'))
        
        # Track directory changes for tab completion
        if command and command.lower().startswith('cd '):
            self._update_working_dir_from_command(command)
        
        # Wait for output to complete
        QTimer.singleShot(500, self._finish_command)
    
    def _update_working_dir_from_command(self, command):
        """Update working directory tracking when user executes cd command"""
        # Extract the directory from cd command
        parts = command.split(maxsplit=1)
        if len(parts) > 1:
            target = parts[1].strip().strip('"')
            if target:
                import os
                if os.path.isabs(target):
                    self.working_directory = target
                else:
                    new_dir = os.path.join(self.working_directory, target)
                    self.working_directory = os.path.normpath(new_dir)
    
    def _finish_command(self):
        """Finish command execution"""
        self.awaiting_output = False
    
    def _handle_tab_completion(self):
        """Handle tab completion for files and directories with cycling"""
        partial_command = self._get_current_command()
        
        if not partial_command.strip():
            # If empty, just insert spaces
            cursor = self.textCursor()
            cursor.insertText('    ')  # 4 spaces for indent
            self.setTextCursor(cursor)
            # Reset completion state
            self.last_completion_matches = []
            return
        
        # Parse the command to get the last token (word being completed)
        tokens = partial_command.split()
        if not tokens:
            self.last_completion_matches = []
            return
        
        # Get the last token (the one being completed)
        last_token = tokens[-1] if partial_command and partial_command[-1] != ' ' else ''
        
        # Check if we're cycling through previous matches
        # We're cycling if we have matches and the current token matches one of them
        is_cycling = False
        if self.last_completion_matches and last_token:
            for match in self.last_completion_matches:
                match_basename = os.path.basename(match)
                if os.path.isdir(match):
                    match_basename += os.sep
                if last_token.endswith(match_basename) or match_basename.startswith(last_token):
                    is_cycling = True
                    break
        
        if is_cycling:
            # Cycle to next match
            self.completion_index = (self.completion_index + 1) % len(self.last_completion_matches)
            match = self.last_completion_matches[self.completion_index]
            
            # Get basename before adding trailing slash
            replacement = os.path.basename(match)
            if os.path.isdir(match):
                replacement += os.sep
            
            if tokens and partial_command[-1] != ' ':
                new_command = ' '.join(tokens[:-1] + [replacement]) if len(tokens) > 1 else replacement
            else:
                new_command = partial_command + replacement
            
            self._replace_current_command(new_command)
            return
        
        # New completion - search for matches
        self.completion_index = 0
        
        # Try to complete as a file/directory path
        try:
            # Handle relative and absolute paths
            if last_token and os.path.isabs(last_token):
                search_pattern = last_token + '*'
            elif last_token:
                search_pattern = os.path.join(self.working_directory, last_token + '*')
            else:
                search_pattern = os.path.join(self.working_directory, '*')
            
            matches = glob.glob(search_pattern)
            
            if not matches:
                self.last_completion_matches = []
                return
            
            # Store matches for cycling
            self.last_completion_matches = matches
            
            # Complete to first match
            match = matches[0]
            # Get basename before adding trailing slash
            replacement = os.path.basename(match)
            if os.path.isdir(match):
                replacement += os.sep
            
            if tokens and partial_command[-1] != ' ':
                new_command = ' '.join(tokens[:-1] + [replacement]) if len(tokens) > 1 else replacement
            else:
                new_command = partial_command + replacement
                
            self._replace_current_command(new_command)
                
        except Exception:
            # If completion fails, reset state
            self.last_completion_matches = []
    
    def _update_prompt_position(self):
        """Update the prompt position after output"""
        self.prompt_position = self.textCursor().position()
    
    def _process_tab_completion(self):
        """Process any tab completion output from shell"""
        # The shell output handler will automatically display any completions
        pass
    
    def write_output(self, text):
        """Write output to console (for compatibility with existing code)"""
        if text is None:
            return
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(text)
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
        # Update prompt position
        self.prompt_position = self.textCursor().position()
    
    def append(self, text):
        """Override append to update prompt position"""
        if text is None:
            return
        super().append(text)
        self.prompt_position = self.textCursor().position()
        self.ensureCursorVisible()
    
    def insertPlainText(self, text):
        """Override insertPlainText to update prompt position"""
        if text is None:
            return
        super().insertPlainText(text)
        self.prompt_position = self.textCursor().position()
        self.ensureCursorVisible()
    
    def set_working_directory(self, directory):
        """Change the working directory of the shell"""
        # Only change directory if it's different from current
        if directory == self.working_directory:
            return
        self.working_directory = directory
        if sys.platform == 'win32':
            self.shell_process.write(f'cd /d "{directory}"\n'.encode('utf-8'))
        else:
            self.shell_process.write(f'cd "{directory}"\n'.encode('utf-8'))
    
    def run_command(self, command):
        """Run a command programmatically (like typing it and pressing Enter)"""
        if not command:
            return
        
        # Display the command in the console with newline
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(command + '\n')
        self.setTextCursor(cursor)
        self.ensureCursorVisible()
        
        # Add to history
        if command and (not self.command_history or self.command_history[-1] != command):
            self.command_history.append(command)
        self.history_index = -1
        
        # Send command to shell
        self.shell_process.write((command + '\n').encode('utf-8'))


class WorkspaceDiscovery:
    """Discovers repositories, platforms, and build configurations"""
    
    def __init__(self, bt_path):
        self.bt_path = bt_path
        self.cache_dir = os.path.join(os.path.expanduser('~'), '.bt')
    
    def get_repositories(self):
        """Read repositories from .bt cache and discover worktrees"""
        main_repos = []
        all_worktrees = []
        repos_set = set()  # Use set to avoid duplicates (lowercase on Windows for case-insensitive comparison)
        
        print("\n=== Discovering repositories ===")
        print(f"Cache directory: {self.cache_dir}")
        
        # Check for 'repositories' file in cache (stores known repos)
        repo_file = os.path.join(self.cache_dir, 'repositories')
        if os.path.exists(repo_file):
            print(f"Reading {repo_file}...")
            try:
                with open(repo_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        # Split by newline or comma
                        for line in content.split('\n'):
                            for repo in line.split(','):
                                repo = repo.strip()
                                if repo:
                                    # Normalize path
                                    repo = os.path.normpath(os.path.abspath(repo))
                                    repo_key = repo.lower() if os.name == 'nt' else repo
                                    if os.path.isdir(repo) and repo_key not in repos_set:
                                        print(f"  Found repository: {repo}")
                                        repos_set.add(repo_key)
                                        main_repos.append(repo)
                                        # Discover git worktrees for this repo
                                        worktrees = self.get_worktrees(repo)
                                        for wt in worktrees:
                                            wt_key = wt.lower() if os.name == 'nt' else wt
                                            if wt_key not in repos_set:
                                                print(f"    Found worktree: {wt}")
                                                repos_set.add(wt_key)
                                                all_worktrees.append(wt)
                                    elif not os.path.isdir(repo):
                                        print(f"  Skipping (not found): {repo}")
            except Exception as e:
                print(f"Error reading repositories: {e}")
        
        # Also check 'repo' file (single repository)
        repo_file = os.path.join(self.cache_dir, 'repo')
        if os.path.exists(repo_file):
            print(f"Reading {repo_file}...")
            try:
                with open(repo_file, 'r') as f:
                    repo = f.read().strip()
                    if repo:
                        # Normalize path
                        repo = os.path.normpath(os.path.abspath(repo))
                        repo_key = repo.lower() if os.name == 'nt' else repo
                        if os.path.isdir(repo) and repo_key not in repos_set:
                            print(f"  Found repository: {repo}")
                            repos_set.add(repo_key)
                            main_repos.append(repo)
                            # Discover git worktrees for this repo
                            worktrees = self.get_worktrees(repo)
                            for wt in worktrees:
                                wt_key = wt.lower() if os.name == 'nt' else wt
                                if wt_key not in repos_set:
                                    print(f"    Found worktree: {wt}")
                                    repos_set.add(wt_key)
                                    all_worktrees.append(wt)
                        elif not os.path.isdir(repo):
                            print(f"  Skipping (not found): {repo}")
            except Exception as e:
                print(f"Error reading repo: {e}")
        
        # Return repos first, then worktrees
        repos = main_repos + all_worktrees
        print(f"\nTotal repositories found: {len(main_repos)}")
        print(f"Total worktrees found: {len(all_worktrees)}")
        print(f"Total workspaces: {len(repos)}")
        return repos
    
    def get_worktrees(self, repo_path):
        """Get all git worktrees for a repository (excluding the main repo)"""
        worktrees = []
        try:
            # Check if this is a git repository
            git_dir = os.path.join(repo_path, '.git')
            if not os.path.isdir(git_dir) and not os.path.isfile(git_dir):
                # Not a git repo (note: worktrees have .git as a file, not dir)
                return worktrees
            
            # Run git worktree list
            result = subprocess.run(
                ['git', 'worktree', 'list'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                # Normalize the main repo path for comparison (case-insensitive on Windows)
                main_repo_normalized = os.path.normpath(os.path.abspath(repo_path)).lower()
                
                for line in lines:
                    if line.strip():
                        # Format: <path> <commit> [<branch>]
                        parts = line.split()
                        if parts:
                            worktree_path = parts[0].strip()
                            # Normalize path for comparison (case-insensitive)
                            worktree_normalized = os.path.normpath(os.path.abspath(worktree_path)).lower()
                            
                            # Only add if it's not the main repo itself and directory exists
                            # Skip the first entry which is always the main worktree
                            if (worktree_normalized != main_repo_normalized and 
                                os.path.isdir(worktree_path)):
                                # Return the original path, not the normalized one
                                worktrees.append(os.path.normpath(os.path.abspath(worktree_path)))
        except Exception as e:
            print(f"Error getting worktrees for {repo_path}: {e}")
        
        return worktrees
    
    def discover_platforms(self, repo_path):
        """Discover all platforms in a repository"""
        platforms = []
        if not os.path.isdir(repo_path):
            print(f"  Path does not exist: {repo_path}")
            return platforms
        
        # Get current platform from local.txt
        current_platform = self.get_current_platform(repo_path)
        print(f"  Current active platform: {current_platform}")
        
        # Search for directories containing PlatformPkg.dsc
        # Limit search to reasonable depth to avoid scanning entire tree
        print(f"  Searching for PlatformPkg.dsc files...")
        for root, dirs, files in os.walk(repo_path):
            # Limit depth by removing deep directories from search
            depth = root[len(repo_path):].count(os.sep)
            if depth > 5:  # Don't go deeper than 5 levels
                dirs.clear()
                continue
            
            if 'PlatformPkg.dsc' in files:
                # Only include platforms from HPeProductLine directory (case-insensitive)
                if 'hpeproductline' not in root.lower():
                    print(f"    Skipping (not in HPeProductLine): {root}")
                    continue
                
                platform_name = os.path.basename(root)
                if platform_name.endswith('Pkg'):
                    platform_name = platform_name[:-3]  # Remove 'Pkg' suffix
                
                # Only include platforms matching pattern: Letter + 2 digits (e.g., U68, G11)
                import re
                if not re.match(r'^[A-Z]\d{2}$', platform_name):
                    print(f"    Skipping non-platform: {platform_name} at {root}")
                    continue
                
                print(f"    Found platform: {platform_name}")
                
                # Get cached build info
                cache_file = os.path.join(self.cache_dir, platform_name)
                cached_count = None
                last_build = None
                
                if os.path.exists(cache_file):
                    try:
                        with open(cache_file, 'r') as f:
                            cached_count = int(f.read().strip())
                        last_build = datetime.fromtimestamp(os.path.getmtime(cache_file))
                    except:
                        pass
                
                platforms.append({
                    'name': platform_name,
                    'path': root,
                    'dsc': os.path.join(root, 'PlatformPkg.dsc'),
                    'cached_count': cached_count,
                    'last_build': last_build,
                    'repo': repo_path,
                    'is_current': platform_name.lower() == current_platform.lower() if current_platform else False
                })
        
        return platforms
    
    def get_current_platform(self, repo_path):
        """Get the currently active platform from local.txt"""
        local_file = os.path.join(repo_path, 'local.txt')
        if os.path.exists(local_file):
            try:
                with open(local_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('platform'):
                            # Format: platform, <path>
                            parts = line.split(',')
                            if len(parts) > 1:
                                platform_path = parts[1].strip()
                                # Extract platform name from path
                                platform_name = os.path.basename(platform_path)
                                if platform_name.endswith('Pkg'):
                                    platform_name = platform_name[:-3]
                                return platform_name
            except Exception as e:
                print(f"Error reading local.txt: {e}")
        return None
    
    def get_local_settings(self, repo_path):
        """Get all local settings for a repository by reading .bt directory files"""
        settings = {
            'alert': None,
            'bmc': None,
            'branch': None,
            'cpu': None,
            'itp': None,
            'name': None,
            'platform': None,
            'release': None,
            'vendor': None,
            'warnings': None
        }
        
        print(f"\nReading bt settings from .bt directory: {repo_path}")
        
        # Read from .bt directory files
        bt_dir = os.path.join(repo_path, '.bt')
        if not os.path.isdir(bt_dir):
            print(f"  .bt directory does not exist")
            return settings
        
        # Read each setting file
        for setting_name in settings.keys():
            setting_file = os.path.join(bt_dir, setting_name)
            if os.path.exists(setting_file):
                try:
                    with open(setting_file, 'r') as f:
                        value = f.read().strip()
                        settings[setting_name] = value
                        print(f"  {setting_name} = {value}")
                except Exception as e:
                    print(f"  Error reading {setting_name}: {e}")
        
        return settings


class WorkspaceTab(QWidget):
    """Individual tab for a workspace/repository"""
    
    def __init__(self, workspace_path, discovery, parent=None):
        super().__init__(parent)
        self.workspace_path = workspace_path
        self.discovery = discovery
        self.build_process = None  # QProcess for build command (for stopping)
        self.local_settings = {}
        
        self.init_ui()
        self.load_local_settings()
    
    def closeEvent(self, event):
        """Clean up when tab is closed"""
        # Kill build process if running
        if self.build_process:
            try:
                self.build_process.kill()
            except:
                pass
        # Kill shell process in console
        if hasattr(self, 'cmd_output') and hasattr(self.cmd_output, 'shell_process'):
            try:
                self.cmd_output.shell_process.kill()
            except:
                pass
        event.accept()
    
    def init_ui(self):
        """Initialize tab UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 0)
        layout.setSpacing(3)
        
        # Progress bar for builds (hidden by default)
        self.progress_container = QWidget()
        progress_layout = QHBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(8)
        
        # Elapsed time label
        self.elapsed_label = QLabel('Time:00:00')
        self.elapsed_label.setStyleSheet('QLabel { font-family: Consolas; color: #0078d4; }')
        progress_layout.addWidget(self.elapsed_label)
        
        # INF files label
        self.inf_label = QLabel('INFs:0')
        self.inf_label.setStyleSheet('QLabel { color: #666666; }')
        self.inf_label.setMinimumWidth(70)
        progress_layout.addWidget(self.inf_label)
        
        # Error count label
        self.error_label = QLabel('Errors:0')
        self.error_label.setStyleSheet('QLabel { color: #666666; }')
        self.error_label.setMinimumWidth(70)
        progress_layout.addWidget(self.error_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat('%v/%m (%p%)')
        self.progress_bar.setStyleSheet('''
            QProgressBar {
                border: 1px solid #999999;
                border-radius: 3px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 2px;
            }
        ''')
        progress_layout.addWidget(self.progress_bar, stretch=1)
        
        self.progress_container.setVisible(False)
        layout.addWidget(self.progress_container)
        
        # Command/Output area - Terminal
        output_group = QGroupBox('Command & Output')
        output_group.setStyleSheet('QGroupBox { font-weight: bold; color: #000000; }')
        output_layout = QVBoxLayout()
        
        self.cmd_output = InteractiveConsole(working_directory=self.workspace_path)
        output_layout.addWidget(self.cmd_output)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group, stretch=1)
    
    def load_local_settings(self):
        """Load local settings for this workspace"""
        self.local_settings = self.discovery.get_local_settings(self.workspace_path)
    
    def edit_email(self):
        """Edit the email setting with validation"""
        current = self.local_settings.get('email', '')
        text, ok = QInputDialog.getText(self, 'Edit Email', 'Enter email address:', text=current)
        
        if ok:
            if text:
                # Validate email format
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if re.match(email_pattern, text):
                    self.save_setting('email', text)
                else:
                    QMessageBox.warning(
                        self,
                        'Invalid Email',
                        'Please enter a valid email address.'
                    )
            else:
                # Allow clearing the email
                self.save_setting('email', '')
    
    def edit_bmc(self):
        """Edit the bmc setting"""
        current = self.local_settings.get('bmc', '')
        text, ok = QInputDialog.getText(self, 'Edit BMC', 'Enter BMC setting:', text=current)
        if ok and text:
            self.save_setting('bmc', text)
    
    def edit_name(self):
        """Edit the name setting by selecting from available platforms"""
        # Discover available platforms in this workspace
        platforms = self.discovery.discover_platforms(self.workspace_path)
        
        if not platforms:
            # Fall back to text input if no platforms found
            current = self.local_settings.get('name', '')
            text, ok = QInputDialog.getText(self, 'Edit Name', 'Enter platform name:', text=current)
            if ok and text:
                self.save_setting('name', text)
            return
        
        # Get list of platform names
        platform_names = [p['name'] for p in platforms]
        
        # Get current selection
        current = self.local_settings.get('name', '')
        current_index = 0
        if current in platform_names:
            current_index = platform_names.index(current)
        
        # Show selection dialog
        item, ok = QInputDialog.getItem(
            self, 
            'Select Platform', 
            'Choose platform name:', 
            platform_names, 
            current_index, 
            False
        )
        
        if ok and item:
            # Run bt init with the selected platform name
            # cpu, name, platform, and vendor will be updated after successful init
            self.run_bt_init(item)
    
    def run_bt_init(self, platform_name):
        """Run bt init command to configure platform in the command output area"""
        # Run bt init via QProcess to display output in the command window
        process = QProcess(self)
        process.setWorkingDirectory(self.workspace_path)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        
        # Store context for handlers
        process.workspace_path = self.workspace_path
        process.platform_name = platform_name
        process.workspace_tab = self
        
        # Connect handlers
        process.readyReadStandardOutput.connect(lambda: self._handle_init_output(process))
        process.readyReadStandardError.connect(lambda: self._handle_init_output(process))
        process.finished.connect(lambda exit_code, exit_status: self._handle_init_finished(process, exit_code))
        process.errorOccurred.connect(lambda error: self._handle_init_error(process, error))
        
        # Use bt.cmd on Windows (via cmd.exe /c), bt.sh on Linux
        if sys.platform == 'win32':
            bt_executable = 'bt.cmd'
            bt_cmd = ['cmd.exe', '/c', bt_executable, 'init', platform_name]
        else:
            bt_executable = 'bt.sh'
            bt_cmd = [bt_executable, 'init', platform_name]
        
        # Show command in output window
        self.cmd_output.append(f"\n{'='*80}\n")
        self.cmd_output.append(f"Running: {bt_executable} init {platform_name}\n")
        self.cmd_output.append(f"Working directory: {self.workspace_path}\n")
        self.cmd_output.append(f"{'='*80}\n\n")
        self.cmd_output.ensureCursorVisible()
        
        # Start the process
        process.start(bt_cmd[0], bt_cmd[1:])
        
        if not process.waitForStarted(3000):
            self.cmd_output.append(f"ERROR: Failed to start {bt_executable}\n")
            self.cmd_output.append(f"Error: {process.errorString()}\n")
            return
    
    def _handle_init_output(self, process):
        """Handle output from bt init command"""
        if not hasattr(process, 'workspace_tab'):
            return
        
        # Read output
        output = process.readAllStandardOutput().data().decode('utf-8', errors='replace')
        
        if output:
            process.workspace_tab.cmd_output.insertPlainText(output)
            process.workspace_tab.cmd_output.ensureCursorVisible()
    
    def _handle_init_finished(self, process, exit_code):
        """Handle completion of bt init command"""
        if not hasattr(process, 'workspace_tab'):
            return
        
        if exit_code == 0:
            process.workspace_tab.cmd_output.append(f"\n{'='*80}\n")
            process.workspace_tab.cmd_output.append("bt init completed successfully!\n")
            process.workspace_tab.cmd_output.append(f"{'='*80}\n\n")
            process.workspace_tab.cmd_output.ensureCursorVisible()
            
            # Reload cpu, name, platform, and vendor settings after successful init
            process.workspace_tab.load_local_settings()
        else:
            process.workspace_tab.cmd_output.append(f"\n{'='*80}\n")
            process.workspace_tab.cmd_output.append(f"bt init failed! (exit code: {exit_code})\n")
            process.workspace_tab.cmd_output.append(f"{'='*80}\n\n")
            process.workspace_tab.cmd_output.ensureCursorVisible()
    
    def _handle_init_error(self, process, error):
        """Handle process errors during bt init"""
        if hasattr(process, 'workspace_tab'):
            error_msg = f"\nProcess error occurred: {process.errorString()}\n"
            process.workspace_tab.cmd_output.append(error_msg)
            process.workspace_tab.cmd_output.ensureCursorVisible()
    
    def toggle_setting(self, setting_name):
        """Toggle a boolean setting"""
        current = self.local_settings.get(setting_name, 'off')
        # Toggle between 'on' and 'off'
        new_value = 'off' if current == 'on' else 'on'
        self.save_setting(setting_name, new_value)
    
    def save_setting(self, setting_name, value):
        """Save a setting by writing to .bt directory file"""
        bt_dir = os.path.join(self.workspace_path, '.bt')
        
        # Create .bt directory if it doesn't exist
        if not os.path.exists(bt_dir):
            try:
                os.makedirs(bt_dir)
            except Exception as e:
                print(f"Error creating .bt directory: {e}")
                return
        
        # Write the setting to its file
        setting_file = os.path.join(bt_dir, setting_name)
        try:
            with open(setting_file, 'w') as f:
                f.write(value)
            self.local_settings[setting_name] = value
            print(f"Saved {setting_name} = {value}")
        except Exception as e:
            print(f"Error saving {setting_name}: {e}")
    
    def start_build(self, build_type='DEBUG'):
        """Start a build using QProcess for proper process management"""
        platform_name = self.local_settings.get('name', '')
        if not platform_name:
            self.cmd_output.append("\nError: No platform name set. Use 'name' button to set.\n")
            return False
        
        # Create QProcess for the build
        self.build_process = QProcess(self)
        self.build_process.setWorkingDirectory(self.workspace_path)
        self.build_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        
        # Set environment to use UTF-8 encoding to avoid Unicode errors
        env = self.build_process.processEnvironment()
        if env.isEmpty():
            env = QProcess.systemEnvironment()
            from PyQt6.QtCore import QProcessEnvironment
            proc_env = QProcessEnvironment()
            for item in env:
                if '=' in item:
                    key, value = item.split('=', 1)
                    proc_env.insert(key, value)
            env = proc_env
        env.insert('PYTHONIOENCODING', 'utf-8')
        self.build_process.setProcessEnvironment(env)
        
        # Connect signals
        self.build_process.readyReadStandardOutput.connect(self._handle_build_output)
        self.build_process.readyReadStandardError.connect(self._handle_build_output)
        self.build_process.finished.connect(self._handle_build_finished)
        self.build_process.errorOccurred.connect(self._handle_build_error)
        
        # Build command: bt.cmd build
        if sys.platform == 'win32':
            bt_executable = 'bt.cmd'
            bt_cmd = ['cmd.exe', '/c', bt_executable, 'build']
        else:
            bt_executable = 'bt.sh'
            bt_cmd = [bt_executable, 'build']
        
        # Show the command on the command line (like user typed it)
        self.cmd_output.insertPlainText(f"{bt_executable} build\n")
        self.cmd_output.ensureCursorVisible()
        
        # Show and reset progress bar
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setFormat('Starting...')
        self.elapsed_label.setText('Time:00:00')
        self.inf_label.setText('INFs:0')
        self.error_label.setText('Errors:0')
        self.error_label.setStyleSheet('QLabel { color: #666666; }')
        self.progress_container.setVisible(True)
        
        # Disable input while building
        self.cmd_output.set_input_enabled(False)
        
        # Start the process
        self.build_process.start(bt_cmd[0], bt_cmd[1:])
        
        if not self.build_process.waitForStarted(3000):
            self.cmd_output.append(f"ERROR: Failed to start build process\n")
            self.cmd_output.append(f"Error: {self.build_process.errorString()}\n")
            self.cmd_output.set_input_enabled(True)
            self.build_process = None
            return False
        
        return True
    
    def _handle_build_output(self):
        """Handle output from the build process"""
        if self.build_process:
            raw_output = self.build_process.readAllStandardOutput().data().decode('utf-8', errors='replace')
            if raw_output:
                # Strip ANSI escape codes first (colors, cursor movement, etc.)
                output = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', raw_output)
                output = re.sub(r'\x1b\][^\x07]*\x07', '', output)  # OSC sequences
                output = re.sub(r'\x1b[PX^_][^\x1b]*\x1b\\', '', output)  # DCS, SOS, PM, APC sequences
                output = re.sub(r'\x1b.', '', output)  # Any other escape sequences
                
                # Remove Unicode block elements (U+2580-U+259F) - they show as colored boxes
                output = re.sub(r'[\u2580-\u259F]+', '', output)
                
                # Check for progress line pattern: "00:04, 0:27/35000 0%, Error 0"
                # Format: elapsed_time, inf_count:lines_done/total_lines percent%, Error error_count
                # This pattern may appear in a line with progress bar characters (block elements already stripped)
                progress_line_match = re.search(r'(\d+:\d+),\s*(\d+):(\d+)/(\d+)\s+(\d+)%,?\s*Error\s+(\d+)', output, re.IGNORECASE)
                
                if progress_line_match:
                    elapsed_time = progress_line_match.group(1)  # e.g., "00:04"
                    inf_count = int(progress_line_match.group(2))  # e.g., 0
                    lines_done = int(progress_line_match.group(3))  # e.g., 27
                    total_lines = int(progress_line_match.group(4))  # e.g., 35000
                    percent = int(progress_line_match.group(5))  # e.g., 0
                    error_count = int(progress_line_match.group(6))  # e.g., 0
                    
                    # Update elapsed time label
                    self.elapsed_label.setText(f'Time:{elapsed_time}')
                    
                    # Update INF files label
                    self.inf_label.setText(f'INFs:{inf_count}')
                    
                    # Update error count label
                    self.error_label.setText(f'Errors:{error_count}')
                    if error_count > 0:
                        self.error_label.setStyleSheet('QLabel { color: #d32f2f; font-weight: bold; }')
                    else:
                        self.error_label.setStyleSheet('QLabel { color: #666666; }')
                    
                    # Update progress bar with lines progress
                    self.progress_bar.setMaximum(total_lines)
                    self.progress_bar.setValue(lines_done)
                    self.progress_bar.setFormat(f'Lines:{lines_done}/{total_lines} ({percent}%)')
                    
                    # Remove only the progress line from output (it's shown in progress bar)
                    # Match: timestamp, inf:lines/total percent%, Error count (and any trailing spaces)
                    output = re.sub(r'\r?\d+:\d+,\s*\d+:\d+/\d+\s+\d+%,?\s*Error\s+\d+\s*', '', output, flags=re.IGNORECASE)
                
                # Clean up empty lines from removed progress, but preserve lines with content
                output = re.sub(r'^\s*\n', '', output)  # Remove leading empty lines
                output = re.sub(r'\n\s*$', '\n', output)  # Clean trailing whitespace but keep newline
                
                # Handle carriage returns (\r) - used for progress updates on the same line
                # Split by \r and process each segment
                if '\r' in output:
                    segments = output.split('\r')
                    for i, segment in enumerate(segments):
                        if i > 0 and segment and not segment.startswith('\n'):
                            # This segment follows a \r, so clear from start of line
                            cursor = self.cmd_output.textCursor()
                            cursor.movePosition(QTextCursor.MoveOperation.End)
                            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.KeepAnchor)
                            cursor.removeSelectedText()
                            self.cmd_output.setTextCursor(cursor)
                        if segment:
                            self.cmd_output.insertPlainText(segment)
                elif output.strip():  # Only insert if there's non-whitespace content
                    self.cmd_output.insertPlainText(output)
                    
                if output.strip():
                    self.cmd_output.ensureCursorVisible()
    
    def _handle_build_finished(self, exit_code, exit_status):
        """Handle build process completion"""
        platform_name = self.local_settings.get('name', 'Unknown')
        success = exit_code == 0
        
        # Hide progress bar
        self.progress_container.setVisible(False)
        
        # Re-enable input
        self.cmd_output.set_input_enabled(True)
        
        # Clear the process reference
        self.build_process = None
        
        # Notify parent to update buttons and clear building_tab
        main_window = self.window()
        if isinstance(main_window, BTGui):
            main_window.building_tab = None
            main_window.update_button_states()
        
        # Show message box
        if success:
            QMessageBox.information(self, 'Build Complete', 
                                   f'{platform_name} built successfully!')
        else:
            QMessageBox.warning(self, 'Build Failed', 
                               f'{platform_name} build failed (exit code: {exit_code}).')
    
    def _handle_build_error(self, error):
        """Handle build process errors"""
        if self.build_process:
            self.cmd_output.append(f"\nProcess error: {self.build_process.errorString()}\n")
            self.cmd_output.ensureCursorVisible()
    
    def stop_build(self):
        """Stop the current build by killing the process"""
        if self.build_process and self.build_process.state() != QProcess.ProcessState.NotRunning:
            self.cmd_output.append("\n*** Stopping build... ***\n")
            self.cmd_output.ensureCursorVisible()
            
            # Kill the process (terminate may not work on Windows for cmd.exe subprocesses)
            self.build_process.kill()
            
            # Wait for it to finish
            if not self.build_process.waitForFinished(5000):
                self.cmd_output.append("*** Warning: Process did not terminate cleanly ***\n")
            
            self.cmd_output.append("*** Build stopped by user ***\n")
            self.cmd_output.ensureCursorVisible()
            
            # Hide progress bar
            self.progress_container.setVisible(False)
            
            # Re-enable input
            self.cmd_output.set_input_enabled(True)
            
            # Clear the process reference
            self.build_process = None
            
            # Trigger a new prompt
            self.cmd_output.shell_process.write(b'\n')
            
            # Notify parent to update buttons and clear building_tab
            main_window = self.window()
            if isinstance(main_window, BTGui):
                main_window.building_tab = None
                main_window.update_button_states()
    

    
    def has_platform_selected(self):
        """Check if a platform is selected"""
        return bool(self.local_settings.get('name', ''))
    
    def is_building(self):
        """Check if currently building"""
        return self.build_process is not None and self.build_process.state() != QProcess.ProcessState.NotRunning


class BTGui(QMainWindow):
    """Main GUI window for BIOS Tool"""
    
    def __init__(self):
        super().__init__()
        self.bt_path = os.path.dirname(os.path.abspath(__file__))
        self.discovery = WorkspaceDiscovery(self.bt_path)
        self.workspace_tabs = {}
        self.building_tab = None  # Track which tab has an active build (only one at a time due to U: drive mapping)
        
        self.init_ui()
        self.discover_workspaces()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle('BIOS Build Tool - GUI')
        
        # Set reasonable window size
        self.resize(1200, 800)
        
        # Central widget with main layout
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(5, 5, 5, 0)
        main_layout.setSpacing(5)
        
        # Top button bar
        button_bar = self.create_button_bar()
        main_layout.addLayout(button_bar)
        
        # Tab widget for workspaces
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(False)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Minimize tab size
        self.tab_widget.tabBar().setStyleSheet("""
            QTabBar::tab {
                padding: 4px 8px;
                min-width: 40px;
                max-width: 120px;
            }
        """)
        
        main_layout.addWidget(self.tab_widget, stretch=1)
        
        # Status bar with global email and local workspace settings (two-line: label above, value in badge)
        self.status_bar = QStatusBar()
        self.status_bar.setMinimumHeight(45)
        self.status_bar.setContentsMargins(0, 0, 0, 0)
        self.status_bar.setStyleSheet('QStatusBar { padding: 0px; } QStatusBar::item { border: none; }')
        self.setStatusBar(self.status_bar)
        
        # Helper to create a stacked widget with label above and value badge below
        def create_stacked_setting(label_text, is_button=False, checkable=False):
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(2, 2, 2, 2)
            layout.setSpacing(1)
            
            # Label on top (outside badge)
            label = QLabel(label_text)
            label.setStyleSheet('QLabel { color: #666666; font-size: 8px; font-weight: bold; background: transparent; border: none; }')
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label)
            
            # Value badge below
            if is_button:
                value_widget = QPushButton('-')
                if checkable:
                    value_widget.setCheckable(True)
                    value_widget.setStyleSheet('''
                        QPushButton { background-color: #555555; color: #ffffff; padding: 2px 6px; border-radius: 3px; font-size: 9px; }
                        QPushButton:checked { background-color: #00aa00; }
                    ''')
                else:
                    value_widget.setStyleSheet('''
                        QPushButton { background-color: #2d2d2d; color: #ffffff; padding: 2px 6px; border-radius: 3px; font-size: 9px; }
                        QPushButton:hover { background-color: #3d3d3d; }
                    ''')
            else:
                value_widget = QLabel('-')
                value_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
                value_widget.setStyleSheet('''
                    QLabel {
                        background-color: #e8e8e8;
                        color: #333333;
                        border: 1px solid #999999;
                        border-radius: 3px;
                        padding: 2px 6px;
                        font-size: 9px;
                    }
                ''')
            layout.addWidget(value_widget)
            return container, value_widget
        
        # Create a container widget for left-aligned items
        left_container = QWidget()
        left_layout = QHBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)
        
        # email setting (global, left-most)
        email_container, self.email_setting_btn = create_stacked_setting('email', is_button=True)
        self.email_setting_btn.clicked.connect(self.edit_email_setting)
        left_layout.addWidget(email_container)
        
        left_layout.addSpacing(6)
        
        # Toggle settings (local/per-workspace)
        alert_container, self.status_alert_btn = create_stacked_setting('alert', is_button=True, checkable=True)
        self.status_alert_btn.clicked.connect(lambda: self._toggle_local_setting('alert'))
        left_layout.addWidget(alert_container)
        
        itp_container, self.status_itp_btn = create_stacked_setting('itp', is_button=True, checkable=True)
        self.status_itp_btn.clicked.connect(lambda: self._toggle_local_setting('itp'))
        left_layout.addWidget(itp_container)
        
        release_container, self.status_release_btn = create_stacked_setting('release', is_button=True, checkable=True)
        self.status_release_btn.clicked.connect(lambda: self._toggle_local_setting('release'))
        left_layout.addWidget(release_container)
        
        warnings_container, self.status_warnings_btn = create_stacked_setting('warnings', is_button=True, checkable=True)
        self.status_warnings_btn.clicked.connect(lambda: self._toggle_local_setting('warnings'))
        left_layout.addWidget(warnings_container)
        
        left_layout.addSpacing(6)
        
        # Editable local settings
        bmc_container, self.status_bmc_btn = create_stacked_setting('bmc', is_button=True)
        self.status_bmc_btn.clicked.connect(lambda: self._edit_local_setting('bmc'))
        left_layout.addWidget(bmc_container)
        
        name_container, self.status_name_btn = create_stacked_setting('name', is_button=True)
        self.status_name_btn.clicked.connect(lambda: self._edit_local_setting('name'))
        left_layout.addWidget(name_container)
        
        self.status_bar.addWidget(left_container)
        
        # Read-only settings (pushed to the right edge)
        branch_container, self.status_branch_label = create_stacked_setting('branch', is_button=False)
        self.status_bar.addPermanentWidget(branch_container)
        
        cpu_container, self.status_cpu_label = create_stacked_setting('cpu', is_button=False)
        self.status_bar.addPermanentWidget(cpu_container)
        
        platform_container, self.status_platform_label = create_stacked_setting('platform', is_button=False)
        self.status_bar.addPermanentWidget(platform_container)
        
        vendor_container, self.status_vendor_label = create_stacked_setting('vendor', is_button=False)
        self.status_bar.addPermanentWidget(vendor_container)
        
        # Load and display current email
        self._load_email_setting()
        
        # Style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton, QToolButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover, QToolButton:hover {
                background-color: #106ebe;
            }
            QPushButton:disabled, QToolButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QToolButton::menu-button {
                border: none;
                border-left: 1px solid rgba(255, 255, 255, 0.3);
                width: 16px;
            }
            QTreeWidget {
                background-color: white;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Courier New', monospace;
                border: 1px solid #cccccc;
                border-radius: 4px;
            }
            QTabWidget::pane {
                border: 2px solid #cccccc;
                border-radius: 5px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #e0e0e0;
                color: #333333;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #0078d4;
                color: white;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background-color: #106ebe;
                color: white;
            }
            QTabBar::tab[is_worktree="true"] {
                background-color: #d4f1d4;
                color: #2d5016;
            }
            QTabBar::tab[is_worktree="true"]:selected {
                background-color: #28a745;
                color: white;
                font-weight: bold;
            }
            QTabBar::tab[is_worktree="true"]:hover {
                background-color: #218838;
                color: white;
            }
        """)
    
    def create_button_bar(self):
        """Create top button bar"""
        layout = QHBoxLayout()
        
        # General Commands group (at left edge)
        general_cmds_group = QGroupBox('General Commands')
        general_cmds_group.setStyleSheet('QGroupBox { font-weight: bold; color: #000000; }')
        general_cmds_layout = QHBoxLayout()
        general_cmds_layout.setContentsMargins(5, 5, 5, 5)
        general_cmds_layout.setSpacing(5)
        
        # Build button
        self.build_btn = QPushButton('▶ Build')
        self.build_btn.setEnabled(False)
        self.build_btn.clicked.connect(self.on_build_clicked)
        general_cmds_layout.addWidget(self.build_btn)
        
        # Stop button
        self.stop_btn = QPushButton('⏹ Stop')
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.on_stop_clicked)
        general_cmds_layout.addWidget(self.stop_btn)
        
        # Cleanup button
        self.cleanup_btn = QPushButton('🧹 Cleanup')
        self.cleanup_btn.setEnabled(False)
        self.cleanup_btn.clicked.connect(self.on_cleanup_clicked)
        general_cmds_layout.addWidget(self.cleanup_btn)
        
        # Status button
        self.status_btn = QPushButton('📊 Status')
        self.status_btn.setEnabled(False)
        self.status_btn.clicked.connect(self.on_bt_status_clicked)
        general_cmds_layout.addWidget(self.status_btn)
        
        # Fetch button
        self.fetch_btn = QPushButton('⬇ Fetch')
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.clicked.connect(self.on_bt_fetch_clicked)
        general_cmds_layout.addWidget(self.fetch_btn)
        
        # Push button
        self.push_btn = QPushButton('⬆ Push')
        self.push_btn.setEnabled(False)
        self.push_btn.clicked.connect(self.on_bt_push_clicked)
        general_cmds_layout.addWidget(self.push_btn)
        
        # Merge button
        self.merge_btn = QPushButton('🔀 Merge')
        self.merge_btn.setEnabled(False)
        self.merge_btn.clicked.connect(self.on_bt_merge_clicked)
        general_cmds_layout.addWidget(self.merge_btn)
        
        # Top button
        self.top_btn = QPushButton('📁 Top')
        self.top_btn.setEnabled(False)
        self.top_btn.clicked.connect(self.on_bt_top_clicked)
        general_cmds_layout.addWidget(self.top_btn)
        
        # Jump button with dropdown menu
        self.jump_btn = QToolButton()
        self.jump_btn.setText('🚀 Jump')
        self.jump_btn.setEnabled(False)
        self.jump_btn.setToolTip('Sync to Jump Station (mapped drive + RDP)')
        self.jump_btn.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        
        # Create menu for jump button
        jump_menu = QMenu(self)
        jump_clean_action = jump_menu.addAction('🧹 Jump /clean')
        jump_clean_action.triggered.connect(self.on_bt_jump_clean_clicked)
        
        # Set the menu and default click action
        self.jump_btn.setMenu(jump_menu)
        self.jump_btn.clicked.connect(self.on_bt_jump_clicked)
        general_cmds_layout.addWidget(self.jump_btn)
        
        general_cmds_group.setLayout(general_cmds_layout)
        layout.addWidget(general_cmds_group)
        
        layout.addStretch()
        
        # Repo Operations group
        repo_ops_group = QGroupBox('Repo Operations')
        repo_ops_group.setStyleSheet('QGroupBox { font-weight: bold; color: #000000; }')
        repo_ops_layout = QHBoxLayout()
        repo_ops_layout.setContentsMargins(5, 5, 5, 5)
        repo_ops_layout.setSpacing(5)
        
        # Add Repo button
        add_repo_btn = QPushButton('🔗 Attach')
        add_repo_btn.clicked.connect(self.on_add_repo_clicked)
        repo_ops_layout.addWidget(add_repo_btn)
        
        # Delete Repo button
        self.delete_repo_btn = QPushButton('⛓️‍💥 Detach')
        self.delete_repo_btn.setEnabled(False)
        self.delete_repo_btn.clicked.connect(self.on_delete_repo_clicked)
        repo_ops_layout.addWidget(self.delete_repo_btn)
        
        repo_ops_group.setLayout(repo_ops_layout)
        layout.addWidget(repo_ops_group)
        
        # Worktree Operations group
        worktree_ops_group = QGroupBox('Worktree Operations')
        worktree_ops_group.setStyleSheet('QGroupBox { font-weight: bold; color: #000000; }')
        worktree_ops_layout = QHBoxLayout()
        worktree_ops_layout.setContentsMargins(5, 5, 5, 5)
        worktree_ops_layout.setSpacing(5)
        
        # Create Worktree button
        self.create_worktree_btn = QPushButton('🌿 Create')
        self.create_worktree_btn.setEnabled(False)
        self.create_worktree_btn.clicked.connect(self.on_create_worktree_clicked)
        worktree_ops_layout.addWidget(self.create_worktree_btn)
        
        # Move Worktree button (worktree only)
        self.move_btn = QPushButton('📦 Move')
        self.move_btn.setEnabled(False)
        self.move_btn.clicked.connect(self.on_bt_move_clicked)
        worktree_ops_layout.addWidget(self.move_btn)
        
        # Remove Worktree button
        self.remove_worktree_btn = QPushButton('❌ Remove')
        self.remove_worktree_btn.setEnabled(False)
        self.remove_worktree_btn.clicked.connect(self.on_remove_worktree_clicked)
        worktree_ops_layout.addWidget(self.remove_worktree_btn)
        
        worktree_ops_group.setLayout(worktree_ops_layout)
        layout.addWidget(worktree_ops_group)
        
        # Refresh group
        refresh_group = QGroupBox('')
        refresh_group.setStyleSheet('QGroupBox { font-weight: bold; color: #000000; }')
        refresh_layout = QHBoxLayout()
        refresh_layout.setContentsMargins(5, 5, 5, 5)
        refresh_layout.setSpacing(5)
        
        refresh_btn = QPushButton('🔄 Refresh')
        refresh_btn.clicked.connect(self.discover_workspaces)
        refresh_layout.addWidget(refresh_btn)
        
        refresh_group.setLayout(refresh_layout)
        layout.addWidget(refresh_group)
        
        return layout
    
    def add_workspace_tab(self, workspace_path, tab_name=None):
        """Add a single workspace tab without refreshing everything"""
        if not os.path.isdir(workspace_path):
            return None
        
        # Generate tab name if not provided
        if tab_name is None:
            tab_name = os.path.basename(workspace_path)
            if not tab_name:
                tab_name = workspace_path
        
        # Create tab for this workspace
        tab = WorkspaceTab(workspace_path, self.discovery, self)
        
        # Determine if this is a worktree
        is_wt = self.is_worktree(workspace_path)
        
        # Use the original name (no prefix)
        display_name = tab_name
        
        # Find the correct insertion position (repos before worktrees)
        insert_index = self.tab_widget.count()  # Default to end
        for i in range(self.tab_widget.count()):
            existing_tab = self.tab_widget.widget(i)
            # Find the corresponding path
            existing_path = None
            for path, t in self.workspace_tabs.items():
                if t == existing_tab:
                    existing_path = path
                    break
            
            if existing_path:
                existing_is_wt = self.is_worktree(existing_path)
                # If we're adding a repo and current tab is a worktree, insert here
                if not is_wt and existing_is_wt:
                    insert_index = i
                    break
        
        tab_index = self.tab_widget.insertTab(insert_index, tab, display_name)
        
        # Store whether this is a worktree for reference
        self.tab_widget.tabBar().setTabData(tab_index, {"is_worktree": is_wt})
        
        self.workspace_tabs[workspace_path] = tab
        print(f"  Added tab: {tab_name} -> {workspace_path}")
        
        return tab
    
    def _load_email_setting(self):
        """Load and display the email setting from ~/.bt/email"""
        email_file = os.path.join(self.discovery.cache_dir, 'email')
        email = '-'
        if os.path.exists(email_file):
            try:
                with open(email_file, 'r') as f:
                    email = f.read().strip() or '-'
            except Exception:
                pass
        self.email_setting_btn.setText(email)
    
    def edit_email_setting(self):
        """Edit the email setting with validation"""
        # Get current value from ~/.bt/email
        email_file = os.path.join(self.discovery.cache_dir, 'email')
        current = ''
        if os.path.exists(email_file):
            try:
                with open(email_file, 'r') as f:
                    current = f.read().strip()
            except Exception:
                pass
        
        text, ok = QInputDialog.getText(self, 'Edit Email', 'Enter email address:', text=current)
        
        if ok:
            if text.strip():
                # Validate email format
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if re.match(email_pattern, text.strip()):
                    # Save to file
                    os.makedirs(self.discovery.cache_dir, exist_ok=True)
                    with open(email_file, 'w') as f:
                        f.write(text.strip())
                    self._load_email_setting()
                    self.status_bar.showMessage(f'Email updated: {text.strip()}', 3000)
                else:
                    QMessageBox.warning(
                        self,
                        'Invalid Email',
                        f'"{text}" is not a valid email address.\n\nPlease enter a valid email like: user@example.com'
                    )
            else:
                # Clear the email
                if os.path.exists(email_file):
                    os.remove(email_file)
                self._load_email_setting()
                self.status_bar.showMessage('Email cleared', 3000)
    
    def discover_workspaces(self):
        """Discover all workspaces and create tabs - only update what changed"""
        self.status_bar.showMessage('Discovering workspaces...')
        
        repos = self.discovery.get_repositories()
        print(f"\n=== Discovering {len(repos)} repositories/worktrees ===")
        
        # Normalize all paths for comparison
        discovered_repos = {os.path.normcase(os.path.normpath(repo)): repo for repo in repos if os.path.isdir(repo)}
        existing_tabs = {os.path.normcase(os.path.normpath(path)): path for path in self.workspace_tabs.keys()}
        
        # Find tabs to remove (workspaces that no longer exist)
        tabs_to_remove = set(existing_tabs.keys()) - set(discovered_repos.keys())
        
        # Find tabs to add (new workspaces)
        tabs_to_add = set(discovered_repos.keys()) - set(existing_tabs.keys())
        
        # Remove tabs for workspaces that no longer exist
        for normalized_path in tabs_to_remove:
            original_path = existing_tabs[normalized_path]
            tab = self.workspace_tabs[original_path]
            
            # Find the tab index
            for i in range(self.tab_widget.count()):
                if self.tab_widget.widget(i) == tab:
                    # Close the shell process
                    if hasattr(tab, 'cmd_output') and hasattr(tab.cmd_output, 'shell_process'):
                        tab.cmd_output.shell_process.kill()
                        tab.cmd_output.shell_process.waitForFinished(1000)
                    
                    # Remove the tab
                    self.tab_widget.removeTab(i)
                    del self.workspace_tabs[original_path]
                    print(f"  Removed tab: {original_path} (no longer exists)")
                    break
        
        # Add tabs for new workspaces
        for normalized_path in tabs_to_add:
            repo = discovered_repos[normalized_path]
            tab_name = os.path.basename(repo)
            if not tab_name:
                tab_name = repo
            
            # Create tab for this workspace - temporarily add it
            tab = WorkspaceTab(repo, self.discovery, self)
            self.workspace_tabs[repo] = tab
            print(f"  Added tab: {tab_name} -> {repo}")
        
        # Now reorganize all tabs: repos first (blue), then worktrees (green)
        # Clear tabs from widget but keep workspace_tabs dict
        tab_widgets = []
        for path, tab in self.workspace_tabs.items():
            tab_widgets.append((path, tab, self.is_worktree(path)))
        
        # Sort: repos (False) before worktrees (True)
        tab_widgets.sort(key=lambda x: (x[2], os.path.basename(x[0])))
        
        # Remove all tabs and re-add in correct order
        self.tab_widget.clear()
        
        # Track if we've added the divider
        divider_added = False
        has_repos = any(not is_wt for _, _, is_wt in tab_widgets)
        has_worktrees = any(is_wt for _, _, is_wt in tab_widgets)
        
        for path, tab, is_wt in tab_widgets:
            # Add divider before first worktree (if we have both repos and worktrees)
            if is_wt and not divider_added and has_repos and has_worktrees:
                divider_index = self.tab_widget.addTab(QWidget(), "│")
                self.tab_widget.setTabEnabled(divider_index, False)
                self.tab_widget.tabBar().setTabData(divider_index, {"is_divider": True})
                # Make divider tab very narrow
                self.tab_widget.tabBar().setStyleSheet("""
                    QTabBar::tab {
                        padding: 4px 8px;
                        min-width: 40px;
                        max-width: 120px;
                    }
                    QTabBar::tab:disabled {
                        padding: 0px 2px;
                        min-width: 8px;
                        max-width: 8px;
                        color: #888888;
                    }
                """)
                divider_added = True
            
            tab_name = os.path.basename(path) if os.path.basename(path) else path
            tab_index = self.tab_widget.addTab(tab, tab_name)
            
            # Store whether this is a worktree for reference
            self.tab_widget.tabBar().setTabData(tab_index, {"is_worktree": is_wt})
        
        if len(discovered_repos) == 0:
            self.status_bar.showMessage('No repositories configured. Use "Attach Repo" to add one.', 0)
        else:
            self.status_bar.showMessage(f'Found {len(discovered_repos)} workspace(s)', 3000)
        
        # Select the first tab if none selected
        if self.tab_widget.count() > 0 and self.tab_widget.currentIndex() == -1:
            self.tab_widget.setCurrentIndex(0)
        
        # Update button states and status bar
        self.update_button_states()
        self._update_status_bar_from_tab()
    
    def on_tab_changed(self, index):
        """Handle tab change"""
        self.update_button_states()
        self._update_status_bar_from_tab()
    
    def _update_status_bar_from_tab(self):
        """Update status bar settings from current workspace tab"""
        current_tab = self.get_current_tab()
        
        if current_tab and isinstance(current_tab, WorkspaceTab):
            settings = current_tab.local_settings
            
            # Update toggle buttons (values are 'on', 'off', or None) - just the value, label is above
            alert_val = settings.get('alert') or 'off'
            self.status_alert_btn.setText(alert_val)
            self.status_alert_btn.setChecked(alert_val == 'on')
            
            itp_val = settings.get('itp') or 'off'
            self.status_itp_btn.setText(itp_val)
            self.status_itp_btn.setChecked(itp_val != 'off' and itp_val != '')
            
            release_val = settings.get('release') or 'off'
            self.status_release_btn.setText(release_val)
            self.status_release_btn.setChecked(release_val == 'on')
            
            warnings_val = settings.get('warnings') or 'off'
            self.status_warnings_btn.setText(warnings_val)
            self.status_warnings_btn.setChecked(warnings_val == 'on')
            
            # Update editable settings - just the value
            self.status_bmc_btn.setText(settings.get('bmc') or '-')
            self.status_name_btn.setText(settings.get('name') or '-')
            
            # Update read-only settings - just the value
            self.status_branch_label.setText(settings.get('branch') or '-')
            self.status_cpu_label.setText(settings.get('cpu') or '-')
            self.status_platform_label.setText(settings.get('platform') or '-')
            self.status_vendor_label.setText(settings.get('vendor') or '-')
        else:
            # No tab selected - show defaults
            self.status_alert_btn.setText('-')
            self.status_alert_btn.setChecked(False)
            self.status_itp_btn.setText('-')
            self.status_itp_btn.setChecked(False)
            self.status_release_btn.setText('-')
            self.status_release_btn.setChecked(False)
            self.status_warnings_btn.setText('-')
            self.status_warnings_btn.setChecked(False)
            self.status_bmc_btn.setText('-')
            self.status_name_btn.setText('-')
            self.status_branch_label.setText('-')
            self.status_cpu_label.setText('-')
            self.status_platform_label.setText('-')
            self.status_vendor_label.setText('-')
    
    def _toggle_local_setting(self, setting_name):
        """Toggle a local setting for the current workspace"""
        current_tab = self.get_current_tab()
        if current_tab and isinstance(current_tab, WorkspaceTab):
            current_tab.toggle_setting(setting_name)
            self._update_status_bar_from_tab()
    
    def _edit_local_setting(self, setting_name):
        """Edit a local setting for the current workspace"""
        current_tab = self.get_current_tab()
        if current_tab and isinstance(current_tab, WorkspaceTab):
            if setting_name == 'bmc':
                current_tab.edit_bmc()
            elif setting_name == 'name':
                current_tab.edit_name()
            self._update_status_bar_from_tab()
    
    def get_current_tab(self):
        """Get the currently active workspace tab"""
        index = self.tab_widget.currentIndex()
        if index >= 0:
            return self.tab_widget.widget(index)
        return None
    
    def update_button_states(self):
        """Update button enabled/disabled states based on current tab"""
        current_tab = self.get_current_tab()
        
        # Check if any build is running globally (only one build allowed at a time due to U: drive mapping)
        any_build_running = self.building_tab is not None and self.building_tab.is_building()
        
        if current_tab and isinstance(current_tab, WorkspaceTab):
            has_platform = current_tab.has_platform_selected()
            is_current_tab_building = current_tab == self.building_tab and current_tab.is_building()
            is_main_repo = self.is_main_repo(current_tab.workspace_path)
            is_worktree = self.is_worktree(current_tab.workspace_path)
            is_git_repo = os.path.isdir(os.path.join(current_tab.workspace_path, '.git'))
            
            # Build is disabled if any tab is building (global lock due to U: drive)
            self.build_btn.setEnabled(has_platform and not any_build_running)
            # Stop is only enabled if the current tab is the one building
            self.stop_btn.setEnabled(is_current_tab_building)
            self.cleanup_btn.setEnabled(has_platform and not any_build_running)
            self.delete_repo_btn.setEnabled(is_main_repo)
            self.create_worktree_btn.setEnabled(is_main_repo and is_git_repo and not any_build_running)
            self.remove_worktree_btn.setEnabled(is_worktree and not any_build_running)
            
            # BT Commands - enabled for both repos and worktrees (not during any build)
            self.status_btn.setEnabled(not any_build_running)
            self.fetch_btn.setEnabled(not any_build_running)
            self.push_btn.setEnabled(not any_build_running)
            self.merge_btn.setEnabled(not any_build_running)
            self.top_btn.setEnabled(not any_build_running)
            # Move is only for worktrees
            self.move_btn.setEnabled(is_worktree and not any_build_running)
            # Jump command - enabled for repos/worktrees (not during any build)
            self.jump_btn.setEnabled(not any_build_running)
        else:
            self.build_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.cleanup_btn.setEnabled(False)
            self.delete_repo_btn.setEnabled(False)
            self.create_worktree_btn.setEnabled(False)
            self.remove_worktree_btn.setEnabled(False)
            self.status_btn.setEnabled(False)
            self.fetch_btn.setEnabled(False)
            self.push_btn.setEnabled(False)
            self.merge_btn.setEnabled(False)
            self.top_btn.setEnabled(False)
            self.move_btn.setEnabled(False)
            self.jump_btn.setEnabled(False)
    
    def on_build_clicked(self):
        """Handle build button click"""
        current_tab = self.get_current_tab()
        if current_tab and isinstance(current_tab, WorkspaceTab):
            # Check if another build is already running (should be caught by button state, but double-check)
            if self.building_tab is not None and self.building_tab.is_building():
                QMessageBox.warning(
                    self,
                    'Build In Progress',
                    'A build is already running in another tab.\n\n'
                    'Only one build can run at a time because the build maps the U: drive.'
                )
                return
            
            # Set this tab as the building tab before starting
            self.building_tab = current_tab
            
            if current_tab.start_build():
                platform_name = current_tab.local_settings.get('name', 'Unknown')
                self.status_bar.showMessage(f'Building {platform_name}...')
                self.update_button_states()
            else:
                # Build failed to start, clear the building_tab
                self.building_tab = None
                self.update_button_states()
    
    def on_stop_clicked(self):
        """Handle stop button click"""
        current_tab = self.get_current_tab()
        if current_tab and isinstance(current_tab, WorkspaceTab):
            current_tab.stop_build()
            self.status_bar.showMessage('Build stopped')
            self.update_button_states()
    
    def on_cleanup_clicked(self):
        """Handle cleanup button click - runs bt cleanup"""
        current_tab = self.get_current_tab()
        if current_tab and isinstance(current_tab, WorkspaceTab):
            self._run_bt_command('cleanup')
            self.status_bar.showMessage('Cleanup requested')
    
    def is_main_repo(self, path):
        """Check if the path is a main repository (not a worktree)"""
        if not path:
            return False
        
        path = os.path.normpath(os.path.abspath(path))
        
        # Read repositories file
        repo_file = os.path.join(self.discovery.cache_dir, 'repositories')
        if not os.path.exists(repo_file):
            return False
        
        with open(repo_file, 'r') as f:
            content = f.read().strip()
            if content:
                for line in content.split('\n'):
                    for repo in line.split(','):
                        repo = repo.strip()
                        if repo:
                            repo_normalized = os.path.normpath(os.path.abspath(repo))
                            if repo_normalized.lower() == path.lower():
                                return True
        
        return False
    
    def is_worktree(self, path):
        """Check if the given path is a git worktree (not a main repo)"""
        path = os.path.normpath(os.path.abspath(path))
        
        # Check if .git is a file (worktrees have .git as a file, not directory)
        git_path = os.path.join(path, '.git')
        if os.path.isfile(git_path):
            return True
        
        return False
    
    def get_main_repo_for_worktree(self, worktree_path):
        """Get the main repository path for a given worktree"""
        worktree_path = os.path.normpath(os.path.abspath(worktree_path))
        git_file = os.path.join(worktree_path, '.git')
        
        if not os.path.isfile(git_file):
            return None
        
        try:
            with open(git_file, 'r') as f:
                content = f.read().strip()
                # Content is like: gitdir: /path/to/main/.git/worktrees/name
                if content.startswith('gitdir: '):
                    gitdir = content[8:].strip()
                    # Extract main repo path
                    main_git_dir = gitdir.split('.git/worktrees/')[0] + '.git'
                    repo_path = os.path.dirname(main_git_dir)
                    return os.path.normpath(repo_path)
        except Exception:
            pass
        
        return None
    
    def on_delete_repo_clicked(self):
        """Handle delete repo button click"""
        current_tab = self.get_current_tab()
        if not current_tab or not isinstance(current_tab, WorkspaceTab):
            return
        
        repo_path = current_tab.workspace_path
        
        # Check if it's a git repo with worktrees
        worktrees = []
        is_git = os.path.isdir(os.path.join(repo_path, '.git'))
        if is_git:
            worktrees = self.discovery.get_worktrees(repo_path)
        
        # Confirm deletion
        if worktrees:
            # Show warning about worktrees
            worktree_list = '\n'.join([f'  - {os.path.basename(wt)}' for wt in worktrees])
            reply = QMessageBox.question(
                self,
                'Delete Repository',
                f'Are you sure you want to remove this repository from the list?\n\n'
                f'Path: {repo_path}\n\n'
                f'WARNING: This repository has {len(worktrees)} associated worktree(s):\n{worktree_list}\n\n'
                f'All worktree tabs will also be removed from the GUI.\n\n'
                f'Note: This only removes them from the GUI. The repository and worktree files will not be deleted.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
        else:
            reply = QMessageBox.question(
                self,
                'Delete Repository',
                f'Are you sure you want to remove this repository from the list?\n\n'
                f'Path: {repo_path}\n\n'
                f'Note: This only removes it from the GUI. The repository files will not be deleted.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Remove from repositories file
        repo_file = os.path.join(self.discovery.cache_dir, 'repositories')
        existing_repos = []
        
        if os.path.exists(repo_file):
            with open(repo_file, 'r') as f:
                content = f.read().strip()
                if content:
                    for line in content.split('\n'):
                        for repo in line.split(','):
                            repo = repo.strip()
                            if repo:
                                repo_normalized = os.path.normpath(os.path.abspath(repo))
                                path_normalized = os.path.normpath(os.path.abspath(repo_path))
                                if repo_normalized.lower() != path_normalized.lower():
                                    existing_repos.append(repo_normalized)
        
        # Write back to repositories file
        with open(repo_file, 'w') as f:
            if existing_repos:
                f.write(','.join(existing_repos))
            else:
                f.write('')
        
        # Also check and remove from 'repo' file (single repository file)
        single_repo_file = os.path.join(self.discovery.cache_dir, 'repo')
        should_delete_single_repo = False
        if os.path.exists(single_repo_file):
            with open(single_repo_file, 'r') as f:
                single_repo = f.read().strip()
                if single_repo:
                    single_repo_normalized = os.path.normpath(os.path.abspath(single_repo))
                    path_normalized = os.path.normpath(os.path.abspath(repo_path))
                    if single_repo_normalized.lower() == path_normalized.lower():
                        should_delete_single_repo = True
            
            # Delete after closing the file
            if should_delete_single_repo:
                try:
                    os.remove(single_repo_file)
                except Exception as e:
                    print(f"Error removing repo file: {e}")
        
        # Refresh to remove tabs - this will clear and recreate all tabs
        # which automatically removes the deleted repo's tab and any associated worktree tabs
        self.discover_workspaces()
        
        self.status_bar.showMessage(f'Removed repository: {os.path.basename(repo_path)}', 5000)
    
    def on_create_worktree_clicked(self):
        """Handle create worktree button click"""
        current_tab = self.get_current_tab()
        if not current_tab or not isinstance(current_tab, WorkspaceTab):
            return
        
        repo_path = current_tab.workspace_path
        
        # Get branch name
        branch_name, ok = QInputDialog.getText(
            self,
            'Create Worktree',
            'Enter branch name for the new worktree:'
        )
        
        if not ok or not branch_name:
            return
        
        # Normalize branch name - always use forward slashes for git branches
        branch_name = branch_name.strip().replace('\\', '/')
        
        # Get worktree directory name
        # Default to ..\<last-part-of-branch>
        default_worktree_dir = f"..\\{branch_name.split('/')[-1]}"
        worktree_name, ok = QInputDialog.getText(
            self,
            'Create Worktree',
            'Enter directory name for the worktree:',
            text=default_worktree_dir
        )
        
        if not ok or not worktree_name:
            return
        
        # Get commitish (optional, defaults to HEAD)
        commitish, ok = QInputDialog.getText(
            self,
            'Create Worktree',
            'Enter commitish (commit/tag/branch) to checkout (leave empty for HEAD):',
            text='HEAD'
        )
        
        if not ok:
            return
        
        # If empty or just whitespace, use HEAD
        if not commitish or not commitish.strip():
            commitish = 'HEAD'
        else:
            commitish = commitish.strip()
        
        # Create worktree path - resolve relative to repo directory, not parent
        if os.path.isabs(worktree_name):
            # Absolute path - use as-is
            worktree_path = os.path.normpath(worktree_name)
        else:
            # Relative path - resolve relative to repo directory
            worktree_path = os.path.normpath(os.path.join(repo_path, worktree_name))
        
        # Normalize path separators for the worktree path
        if sys.platform == 'win32':
            # Windows: convert forward slashes to backslashes
            worktree_path = worktree_path.replace('/', '\\')
        else:
            # Linux/Unix: convert backslashes to forward slashes
            worktree_path = worktree_path.replace('\\', '/')
        
        if os.path.exists(worktree_path):
            QMessageBox.warning(
                self,
                'Create Worktree',
                f'Directory already exists: {worktree_path}'
            )
            return
        
        if not hasattr(current_tab, 'cmd_output'):
            QMessageBox.warning(
                self,
                'Create Worktree',
                'Command output window is not available. Cannot execute command.'
            )
            return
        
        # Run bt create via QProcess - capture output to detect completion strings
        # while also displaying output in the output window for user visibility
        process = QProcess(self)
        process.setWorkingDirectory(repo_path)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        
        # Store context for handlers
        process.repo_path = repo_path
        process.worktree_path = worktree_path
        process.worktree_name = worktree_name
        process.current_tab = current_tab
        process.output_buffer = ""  # Accumulate output to search for completion strings
        
        # Connect handlers - need both stdout and stderr even with MergedChannels
        process.readyReadStandardOutput.connect(lambda: self._handle_create_output(process))
        process.readyReadStandardError.connect(lambda: self._handle_create_output(process))
        process.errorOccurred.connect(lambda error: self._handle_create_error(process, error))
        
        # Disable input while process is running
        current_tab.cmd_output.set_input_enabled(False)
        
        # Start the process
        # Format: bt create /repo <path-to-repo> <branch> <path-to-target-directory> [commitish]
        # Use bt.cmd on Windows (via cmd.exe /c), bt.sh on Linux
        if sys.platform == 'win32':
            bt_executable = 'bt.cmd'
            bt_cmd = ['cmd.exe', '/c', bt_executable, 'create', '/repo', repo_path, branch_name, worktree_path, commitish]
        else:
            bt_executable = 'bt.sh'
            bt_cmd = [bt_executable, 'create', '/repo', repo_path, branch_name, worktree_path, commitish]
        
        # Show command in output window BEFORE starting
        bt_cmd_str = f'{bt_executable} create /repo "{repo_path}" {branch_name} "{worktree_path}" {commitish}'
        # Insert the command at the current cursor position (after prompt)
        cursor = current_tab.cmd_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(bt_cmd_str + '\n')
        current_tab.cmd_output.setTextCursor(cursor)
        current_tab.cmd_output.ensureCursorVisible()
        
        # Start the process
        process.start(bt_cmd[0], bt_cmd[1:])
        
        # Check if process started
        if not process.waitForStarted(3000):
            current_tab.cmd_output.append(f"ERROR: Failed to start process. Is '{bt_executable}' in your PATH?\n")
            current_tab.cmd_output.append(f"Process error: {process.errorString()}\n")
            QMessageBox.warning(
                self,
                'Process Error',
                f"Failed to start bt command.\n\nError: {process.errorString()}\n\nMake sure '{bt_executable}' is in your PATH."
            )
            return
        
        self.status_bar.showMessage(f'Creating worktree: {worktree_name}...', 5000)
    
    def _handle_create_output(self, process):
        """Handle output from bt create command - display in output window and check for completion"""
        if not hasattr(process, 'current_tab') or not hasattr(process.current_tab, 'cmd_output'):
            return
        
        # Read both stdout and stderr
        stdout = process.readAllStandardOutput().data().decode('utf-8', errors='replace')
        stderr = process.readAllStandardError().data().decode('utf-8', errors='replace')
        
        output = stdout + stderr
        
        # Display in output window
        if output:
            # Handle carriage returns (\r) - git uses these for progress updates
            # Split by \r and only display the last segment to simulate overwriting behavior
            lines = output.split('\n')
            for line in lines:
                if '\r' in line:
                    # For lines with \r, only show the final segment
                    segments = line.split('\r')
                    for segment in segments[:-1]:
                        # Clear the current line and write the segment
                        cursor = process.current_tab.cmd_output.textCursor()
                        cursor.movePosition(cursor.MoveOperation.StartOfLine, cursor.MoveMode.KeepAnchor)
                        cursor.removeSelectedText()
                        process.current_tab.cmd_output.insertPlainText(segment)
                    # Write the final segment
                    if segments[-1]:
                        cursor = process.current_tab.cmd_output.textCursor()
                        cursor.movePosition(cursor.MoveOperation.StartOfLine, cursor.MoveMode.KeepAnchor)
                        cursor.removeSelectedText()
                        process.current_tab.cmd_output.insertPlainText(segments[-1])
                else:
                    process.current_tab.cmd_output.insertPlainText(line)
                
                # Add newline back except for last line
                if line != lines[-1]:
                    process.current_tab.cmd_output.insertPlainText('\n')
            
            process.current_tab.cmd_output.ensureCursorVisible()
            
            # Accumulate in buffer to search for completion strings
            # Replace \r with \n for proper string searching
            process.output_buffer += output.replace('\r', '\n')
            
            # Check for completion strings
            if "Create Worktree Passed!" in process.output_buffer:
                # Success! Handle completion
                QTimer.singleShot(500, lambda: self._handle_create_success(process))
            elif "Create Worktree FAILED!" in process.output_buffer:
                # Failed - just log, user already sees error in output window
                QTimer.singleShot(500, lambda: self._handle_create_failure(process))
    
    def _handle_create_success(self, process):
        """Handle successful worktree creation"""
        # Re-enable input in the console
        if hasattr(process, 'current_tab') and hasattr(process.current_tab, 'cmd_output'):
            process.current_tab.cmd_output.set_input_enabled(True)
        
        # Add new tab for the worktree - use basename of path for tab name
        worktree_basename = os.path.basename(process.worktree_path)
        self.add_workspace_tab(process.worktree_path, worktree_basename)
        
        # Switch to the new tab
        self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)
        
        self.status_bar.showMessage(f'Worktree created successfully: {worktree_basename}', 5000)
    
    def _handle_create_failure(self, process):
        """Handle failed worktree creation"""
        # Re-enable input in the console
        if hasattr(process, 'current_tab') and hasattr(process.current_tab, 'cmd_output'):
            process.current_tab.cmd_output.set_input_enabled(True)
        
        self.status_bar.showMessage(f'Failed to create worktree: {process.worktree_name}', 5000)
    
    def _handle_create_error(self, process, error):
        """Handle process errors during worktree creation"""
        if hasattr(process, 'current_tab') and hasattr(process.current_tab, 'cmd_output'):
            error_msg = f"\nProcess error occurred: {process.errorString()}\n"
            process.current_tab.cmd_output.append(error_msg)
            process.current_tab.cmd_output.ensureCursorVisible()
            # Re-enable input after error
            process.current_tab.cmd_output.set_input_enabled(True)
    
    def on_remove_worktree_clicked(self):
        """Handle remove worktree button click"""
        current_tab = self.get_current_tab()
        if not current_tab or not isinstance(current_tab, WorkspaceTab):
            return
        
        worktree_path = current_tab.workspace_path
        
        # Check if this is actually a worktree (not a main repo)
        git_file = os.path.join(worktree_path, '.git')
        if not os.path.isfile(git_file):
            QMessageBox.warning(
                self,
                'Remove Worktree',
                'This is not a worktree. Only worktrees can be removed using this button.'
            )
            return
        
        # Confirm deletion
        reply = QMessageBox.question(
            self,
            'Remove Worktree',
            f'Are you sure you want to remove this worktree?\n\n'
            f'Path: {worktree_path}\n\n'
            f'WARNING: This will remove the worktree from git.\n'
            f'Any uncommitted changes will be lost!\n\n'
            f'The directory will be removed from disk.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Find the main repo tab to switch to before destroying
        repo_tab_index = -1
        current_tab_index = self.tab_widget.currentIndex()
        
        # Find the main repo for this worktree
        try:
            # Read .git file to find main repo
            with open(git_file, 'r') as f:
                content = f.read().strip()
                # Content is like: gitdir: /path/to/main/.git/worktrees/name
                if content.startswith('gitdir: '):
                    gitdir = content[8:].strip()
                    # Extract main repo path
                    main_git_dir = gitdir.split('.git/worktrees/')[0] + '.git'
                    repo_path = os.path.dirname(main_git_dir)
                    
                    # Find the tab for the main repo (case-insensitive on Windows)
                    repo_path_normalized = os.path.normcase(os.path.normpath(repo_path))
                    for i in range(self.tab_widget.count()):
                        tab = self.tab_widget.widget(i)
                        if isinstance(tab, WorkspaceTab):
                            tab_path_normalized = os.path.normcase(os.path.normpath(tab.workspace_path))
                            if tab_path_normalized == repo_path_normalized:
                                repo_tab_index = i
                                break
                else:
                    raise Exception('Invalid .git file format')
        except Exception as e:
            QMessageBox.critical(
                self,
                'Error',
                f'Error finding repository:\n\n{str(e)}'
            )
            return
        
        # Switch to the repo tab if found
        if repo_tab_index >= 0:
            self.tab_widget.setCurrentIndex(repo_tab_index)
            repo_tab = self.tab_widget.widget(repo_tab_index)
        else:
            QMessageBox.critical(
                self,
                'Error',
                f'Could not find the main repository tab.\n\nPlease open the repository at:\n{repo_path}'
            )
            return
        
        # Close the worktree tab to release the file handle
        # This is necessary on Windows to allow deletion
        self.tab_widget.removeTab(current_tab_index)
        
        # Terminate the shell process in the worktree tab
        if hasattr(current_tab, 'cmd_output') and hasattr(current_tab.cmd_output, 'shell_process'):
            current_tab.cmd_output.shell_process.kill()
            current_tab.cmd_output.shell_process.waitForFinished(1000)
        
        if not hasattr(repo_tab, 'cmd_output'):
            QMessageBox.warning(
                self,
                'Remove Worktree',
                'Command output window is not available. Cannot execute command.'
            )
            return
        
        # Run bt remove via QProcess
        process = QProcess(self)
        process.setWorkingDirectory(repo_path)
        process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        
        # Store context for handlers
        process.repo_path = repo_path
        process.worktree_path = worktree_path
        process.current_tab = repo_tab  # Use repo tab, not worktree tab
        process.output_buffer = ""
        
        # Connect handlers
        process.readyReadStandardOutput.connect(lambda: self._handle_remove_output(process))
        process.readyReadStandardError.connect(lambda: self._handle_remove_output(process))
        process.finished.connect(lambda exit_code, exit_status: self._handle_remove_finished(process, exit_code))
        process.errorOccurred.connect(lambda error: self._handle_remove_error(process, error))
        
        # Use bt.cmd on Windows (via cmd.exe /c), bt.sh on Linux
        if sys.platform == 'win32':
            bt_executable = 'bt.cmd'
            bt_cmd = ['cmd.exe', '/c', bt_executable, 'remove', '/yes', worktree_path]
        else:
            bt_executable = 'bt.sh'
            bt_cmd = [bt_executable, 'remove', '/yes', worktree_path]
        
        # Show command in output window - insert at current cursor position
        cursor = current_tab.cmd_output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(f"\ncd {repo_path}\n")
        cursor.insertText(f"{bt_executable} remove /yes {worktree_path}\n")
        current_tab.cmd_output.setTextCursor(cursor)
        current_tab.cmd_output.ensureCursorVisible()
        
        # Start the process
        process.start(bt_cmd[0], bt_cmd[1:])
        
        if not process.waitForStarted(3000):
            QMessageBox.critical(
                self,
                'Error',
                f'Failed to start {bt_executable}:\n\n{process.errorString()}'
            )
            return
    
    def _handle_remove_output(self, process):
        """Handle output from bt remove command"""
        if not hasattr(process, 'current_tab') or not hasattr(process.current_tab, 'cmd_output'):
            return
        
        # Read output
        output = process.readAllStandardOutput().data().decode('utf-8', errors='replace')
        
        if output:
            process.current_tab.cmd_output.insertPlainText(output)
            process.current_tab.cmd_output.ensureCursorVisible()
            process.output_buffer += output
    
    def _handle_remove_finished(self, process, exit_code):
        """Handle completion of bt remove command"""
        if not hasattr(process, 'current_tab'):
            return
        
        if exit_code == 0:
            process.current_tab.cmd_output.append(f"\n{'='*80}\n")
            process.current_tab.cmd_output.append("Remove Worktree Completed Successfully!\n")
            process.current_tab.cmd_output.append(f"{'='*80}\n\n")
            process.current_tab.cmd_output.ensureCursorVisible()
            
            # Tab was already closed before removing, no need to refresh
            self.status_bar.showMessage(f'Worktree removed successfully', 5000)
        else:
            process.current_tab.cmd_output.append(f"\n{'='*80}\n")
            process.current_tab.cmd_output.append(f"Remove Worktree Failed! (exit code: {exit_code})\n")
            process.current_tab.cmd_output.append(f"{'='*80}\n\n")
            process.current_tab.cmd_output.ensureCursorVisible()
            
            self.status_bar.showMessage(f'Failed to remove worktree (exit code: {exit_code})', 5000)
    
    def _handle_remove_error(self, process, error):
        """Handle process errors during worktree removal"""
        if hasattr(process, 'current_tab') and hasattr(process.current_tab, 'cmd_output'):
            error_msg = f"\nProcess error occurred: {process.errorString()}\n"
            process.current_tab.cmd_output.append(error_msg)
            process.current_tab.cmd_output.ensureCursorVisible()
    
    def _run_bt_command(self, command, args=None):
        """Run a bt command in the current tab's console using the interactive shell"""
        current_tab = self.get_current_tab()
        if not current_tab or not isinstance(current_tab, WorkspaceTab):
            return
        
        if not hasattr(current_tab, 'cmd_output'):
            QMessageBox.warning(
                self,
                'Error',
                'Command output window is not available.'
            )
            return
        
        # Build the command
        if sys.platform == 'win32':
            bt_executable = 'bt.cmd'
        else:
            bt_executable = 'bt.sh'
        
        cmd_parts = [bt_executable, command]
        if args:
            # Quote arguments that contain spaces
            for arg in args:
                if ' ' in arg:
                    cmd_parts.append(f'"{arg}"')
                else:
                    cmd_parts.append(arg)
        
        cmd_str = ' '.join(cmd_parts)
        
        # Run the command through the interactive shell
        current_tab.cmd_output.run_command(cmd_str)
        
        self.status_bar.showMessage(f'Running: bt {command}', 3000)
    
    def on_bt_status_clicked(self):
        """Handle bt status button click"""
        self._run_bt_command('status')
    
    def on_bt_fetch_clicked(self):
        """Handle bt fetch button click"""
        self._run_bt_command('fetch')
    
    def on_bt_push_clicked(self):
        """Handle bt push button click"""
        self._run_bt_command('push')
    
    def on_bt_merge_clicked(self):
        """Handle bt merge button click"""
        self._run_bt_command('merge')
    
    def on_bt_top_clicked(self):
        """Handle bt top button click - changes to workspace root directory"""
        current_tab = self.get_current_tab()
        if not current_tab or not isinstance(current_tab, WorkspaceTab):
            return
        
        # Get the workspace root path
        workspace_path = current_tab.workspace_path
        
        # Change directory to workspace root using the shell
        if sys.platform == 'win32':
            current_tab.cmd_output.run_command(f'cd /d "{workspace_path}"')
        else:
            current_tab.cmd_output.run_command(f'cd "{workspace_path}"')
    
    def on_bt_jump_clicked(self):
        """Handle bt jump button click - sync to jump station"""
        current_tab = self.get_current_tab()
        if not current_tab or not isinstance(current_tab, WorkspaceTab):
            return
        
        # Check if jump station is configured
        jump_config_file = os.path.join(current_tab.workspace_path, '.bt', 'jump')
        if not os.path.exists(jump_config_file):
            result = QMessageBox.question(
                self,
                'Jump Station Not Configured',
                'Jump station is not configured for this workspace.\n\n'
                'Would you like to configure it now?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if result == QMessageBox.StandardButton.Yes:
                # Prompt for destination path
                dest_path, ok = QInputDialog.getText(
                    self,
                    'Configure Jump Station',
                    'Enter destination path on jump station:\n'
                    '(e.g., C:\\Users\\Administrator\\Desktop\\GNext)',
                    text=''
                )
                
                if ok and dest_path:
                    # Run config command
                    current_tab.cmd_output.run_command(f'bt config jump "{dest_path}"')
                    # Wait a bit for config to complete
                    QTimer.singleShot(500, lambda: self._run_bt_command('jump'))
                else:
                    return
            else:
                return
        else:
            # Run jump command
            self._run_bt_command('jump')
    
    def on_bt_jump_clean_clicked(self):
        """Handle bt jump /clean button click - clear jump station cache"""
        current_tab = self.get_current_tab()
        if not current_tab or not isinstance(current_tab, WorkspaceTab):
            return
        
        # Confirm before cleaning
        result = QMessageBox.question(
            self,
            'Clear Jump Station Cache',
            'This will clear the jump station hash cache.\n'
            'The next sync will perform a full sync (not incremental).\n\n'
            'Are you sure you want to continue?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            self._run_bt_command('jump /clean')
    
    def on_bt_move_clicked(self):
        """Handle bt move button click (worktree only)"""
        current_tab = self.get_current_tab()
        if not current_tab or not isinstance(current_tab, WorkspaceTab):
            return
        
        # Verify this is a worktree
        if not self.is_worktree(current_tab.workspace_path):
            QMessageBox.warning(
                self,
                'Move',
                'Move is only available for worktrees.'
            )
            return
        
        # Get the new location
        new_path, ok = QInputDialog.getText(
            self,
            'Move Worktree',
            'Enter the new path for the worktree:',
            text=current_tab.workspace_path
        )
        
        if not ok or not new_path or new_path.strip() == current_tab.workspace_path:
            return
        
        new_path = new_path.strip()
        
        # Confirm the move
        reply = QMessageBox.question(
            self,
            'Move Worktree',
            f'Move worktree to:\n\n{new_path}\n\nContinue?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Get the main repository for this worktree
        old_path = current_tab.workspace_path
        main_repo = self.get_main_repo_for_worktree(old_path)
        
        if not main_repo:
            QMessageBox.warning(
                self,
                'Move Error',
                'Could not find the main repository for this worktree.'
            )
            return
        
        # Change to the main repository to:
        # 1. Release the lock on the worktree (Windows won't move CWD)
        # 2. Provide git context for the move command
        if sys.platform == 'win32':
            current_tab.cmd_output.run_command(f'cd /d "{main_repo}"')
        else:
            current_tab.cmd_output.run_command(f'cd "{main_repo}"')
        
        # Run the move command with explicit paths after a delay
        # bt move <destination> [<source_path>]
        from PyQt6.QtCore import QTimer
        
        # Track retry count for checking move success
        retry_count = [0]
        max_retries = 10  # Check up to 10 times (10 seconds total)
        
        def do_move():
            # Quote paths with spaces
            old_quoted = f'"{old_path}"' if ' ' in old_path else old_path
            new_quoted = f'"{new_path}"' if ' ' in new_path else new_path
            # bt move takes destination first, then source
            if sys.platform == 'win32':
                current_tab.cmd_output.run_command(f'bt.cmd move {new_quoted} {old_quoted}')
            else:
                current_tab.cmd_output.run_command(f'bt.sh move {new_quoted} {old_quoted}')
            
            # Check for success after a delay and update the tab
            QTimer.singleShot(1000, check_move_success)
        
        def check_move_success():
            retry_count[0] += 1
            # Check if move succeeded by verifying new path exists and old doesn't
            if os.path.exists(new_path) and not os.path.exists(old_path):
                # Update the tab's workspace path
                current_tab.workspace_path = new_path
                
                # Update the tab name
                new_name = os.path.basename(new_path)
                tab_index = self.tab_widget.indexOf(current_tab)
                if tab_index >= 0:
                    self.tab_widget.setTabText(tab_index, new_name)
                    self.tab_widget.setTabToolTip(tab_index, new_path)
                
                # Change shell directory to new location
                if sys.platform == 'win32':
                    current_tab.cmd_output.run_command(f'cd /d "{new_path}"')
                else:
                    current_tab.cmd_output.run_command(f'cd "{new_path}"')
                
                self.status_bar.showMessage(f'Worktree moved to {new_path}', 5000)
            elif retry_count[0] < max_retries:
                # Move not complete yet, try again in 1 second
                QTimer.singleShot(1000, check_move_success)
        
        QTimer.singleShot(200, do_move)
    
    def on_add_repo_clicked(self):
        """Handle add repo button click"""
        # Browse for directory
        repo_path = QFileDialog.getExistingDirectory(
            self,
            'Select Repository Directory',
            os.path.expanduser('~'),
            QFileDialog.Option.ShowDirsOnly
        )
        
        if not repo_path:
            return
        
        # Normalize path
        repo_path = os.path.normpath(os.path.abspath(repo_path))
        
        # Check if it's a valid repository (has .git or .svn)
        is_git = os.path.isdir(os.path.join(repo_path, '.git'))
        is_svn = os.path.isdir(os.path.join(repo_path, '.svn'))
        
        if not is_git and not is_svn:
            QMessageBox.warning(
                self,
                'Invalid Repository',
                f'The selected directory is not a valid repository.\n\n'
                f'A repository must contain a .git or .svn directory.\n\n'
                f'Path: {repo_path}'
            )
            return
        
        # Check if it's an HPE UEFI repository (has hpbuild.bat or hpbuild.sh)
        has_hpbuild_bat = os.path.isfile(os.path.join(repo_path, 'hpbuild.bat'))
        has_hpbuild_sh = os.path.isfile(os.path.join(repo_path, 'hpbuild.sh'))
        
        if not has_hpbuild_bat and not has_hpbuild_sh:
            QMessageBox.warning(
                self,
                'Invalid HPE UEFI Repository',
                f'The selected directory is not an HPE UEFI repository.\n\n'
                f'An HPE UEFI repository must contain hpbuild.bat or hpbuild.sh.\n\n'
                f'Path: {repo_path}'
            )
            return
        
        # Add to repositories file
        repo_file = os.path.join(self.discovery.cache_dir, 'repositories')
        
        # Check if already exists
        existing_repos = []
        if os.path.exists(repo_file):
            with open(repo_file, 'r') as f:
                content = f.read().strip()
                if content:
                    for line in content.split('\n'):
                        for repo in line.split(','):
                            repo = repo.strip()
                            if repo:
                                existing_repos.append(os.path.normpath(os.path.abspath(repo)))
        
        # Case-insensitive comparison on Windows
        repo_path_lower = repo_path.lower()
        existing_repos_lower = [r.lower() for r in existing_repos]
        
        if repo_path_lower in existing_repos_lower:
            QMessageBox.information(
                self,
                'Repository Already Exists',
                f'This repository is already in the list.\n\nPath: {repo_path}'
            )
            return
        
        # Add to list
        existing_repos.append(repo_path)
        
        # Write back to file
        with open(repo_file, 'w') as f:
            f.write(','.join(existing_repos))
        
        # Refresh to show new repo and its worktrees
        self.discover_workspaces()
        
        QMessageBox.information(
            self,
            'Repository Added',
            f'Repository has been added successfully.\n\nPath: {repo_path}'
        )
        
        self.status_bar.showMessage(f'Added repository: {os.path.basename(repo_path)}')


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    window = BTGui()
    window.show()
    
    # Center the window after it's fully rendered
    def center_window():
        screen = app.primaryScreen().availableGeometry()
        window_rect = window.frameGeometry()
        center_point = screen.center()
        window_rect.moveCenter(center_point)
        window.move(window_rect.topLeft())
    
    QTimer.singleShot(0, center_window)
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
