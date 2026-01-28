"""Interactive console widget with command input and persistent shell session"""

import sys
import os
import glob
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import Qt, QTimer, QProcess, QProcessEnvironment
from PyQt6.QtGui import QFont, QTextCursor, QKeyEvent


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
