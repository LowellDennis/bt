"""
WorkspaceTab - Individual workspace/repository tab widget
"""

import os
import sys
import re
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
                             QProgressBar, QInputDialog, QMessageBox)
from PyQt6.QtCore import QProcess
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from widgets.console import InteractiveConsole


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
                            from PyQt6.QtGui import QTextCursor
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
        # Import here to avoid circular import
        from ui import BTGui
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
            # Import here to avoid circular import
            from ui import BTGui
            if isinstance(main_window, BTGui):
                main_window.building_tab = None
                main_window.update_button_states()
    
    def has_platform_selected(self):
        """Check if a platform is selected"""
        return bool(self.local_settings.get('name', ''))
    
    def is_building(self):
        """Check if currently building"""
        return self.build_process is not None and self.build_process.state() != QProcess.ProcessState.NotRunning
