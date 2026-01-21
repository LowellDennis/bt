#!/usr/bin/env python
"""
BIOS Tool GUI - Graphical interface for bt build system
Provides workspace discovery, build management, and progress tracking
"""

import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path

try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                 QHBoxLayout, QTreeWidget, QTreeWidgetItem, QPushButton,
                                 QTextEdit, QProgressBar, QLabel, QComboBox, QSplitter,
                                 QGroupBox, QStatusBar, QTabWidget, QMessageBox)
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
    from PyQt6.QtGui import QFont, QColor, QTextCharFormat, QTextCursor
except ImportError:
    print("PyQt6 not found. Install with: pip install PyQt6")
    sys.exit(1)

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class WorkspaceDiscovery:
    """Discovers repositories, platforms, and build configurations"""
    
    def __init__(self, bt_path):
        self.bt_path = bt_path
        self.cache_dir = os.path.join(os.path.expanduser('~'), '.bt')
    
    def get_repositories(self):
        """Read repositories from .bt cache and discover worktrees"""
        repos = []
        
        # Check for 'repositories' file in cache (stores known repos)
        repo_file = os.path.join(self.cache_dir, 'repositories')
        if os.path.exists(repo_file):
            try:
                with open(repo_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        # Split by newline or comma
                        for line in content.split('\n'):
                            for repo in line.split(','):
                                repo = repo.strip()
                                if repo and os.path.isdir(repo):
                                    if repo not in repos:
                                        repos.append(repo)
                                        # Also discover git worktrees
                                        repos.extend(self.get_worktrees(repo))
            except Exception as e:
                print(f"Error reading repositories: {e}")
        
        # Also check 'repo' file (single repository)
        repo_file = os.path.join(self.cache_dir, 'repo')
        if os.path.exists(repo_file):
            try:
                with open(repo_file, 'r') as f:
                    repo = f.read().strip()
                    if repo and os.path.isdir(repo) and repo not in repos:
                        repos.append(repo)
                        # Also discover git worktrees
                        repos.extend(self.get_worktrees(repo))
            except Exception as e:
                print(f"Error reading repo: {e}")
        
        # If no repos found, add some common locations
        if not repos:
            common_locations = [
                r'D:\HPE\Dev\ROMS\GNext',
                r'D:\HPE\Dev\ROMS\G12',
                r'D:\HPE\Dev\ROMS\G11',
                r'D:\HPE\Dev\ROMS'
            ]
            for loc in common_locations:
                if os.path.isdir(loc) and loc not in repos:
                    repos.append(loc)
        
        return repos
    
    def get_worktrees(self, repo_path):
        """Get all git worktrees for a repository"""
        worktrees = []
        try:
            # Check if this is a git repository
            git_dir = os.path.join(repo_path, '.git')
            if not os.path.isdir(git_dir):
                return worktrees
            
            # Run git worktree list
            result = subprocess.run(
                ['git', 'worktree', 'list'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                # Skip first line (the main repo itself)
                for line in lines[1:]:
                    if line.strip():
                        # Format: <path> <commit> [<branch>]
                        parts = line.split()
                        if parts:
                            worktree_path = parts[0].strip()
                            if os.path.isdir(worktree_path):
                                worktrees.append(worktree_path)
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


class BuildThread(QThread):
    """Background thread for running builds"""
    output_ready = pyqtSignal(str)
    progress_update = pyqtSignal(int, int, int)  # current, total, percentage
    build_finished = pyqtSignal(bool)  # success
    
    def __init__(self, workspace, platform, build_type):
        super().__init__()
        self.workspace = workspace
        self.platform = platform
        self.build_type = build_type
        self.process = None
        
    def run(self):
        """Run the build command"""
        try:
            # Change to workspace directory
            os.chdir(self.workspace)
            
            # Build command
            bt_cmd = os.path.join(os.path.dirname(__file__), 'bt.ps1')
            cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-File', bt_cmd, 
                   'build', self.platform, self.build_type]
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=False
            )
            
            # Read output line by line
            for line in iter(self.process.stdout.readline, b''):
                if line:
                    line_str = line.decode('utf-8', errors='ignore')
                    self.output_ready.emit(line_str)
                    
                    # Parse progress if present
                    if b'Modules' in line and b'/' in line:
                        try:
                            # Extract module counts: "Modules [bar](123/456)78%"
                            parts = line_str.split('(')
                            if len(parts) > 1:
                                counts = parts[1].split(')')[0].split('/')
                                if len(counts) == 2:
                                    current = int(counts[0])
                                    total = int(counts[1])
                                    pct = int((current / total) * 100) if total > 0 else 0
                                    self.progress_update.emit(current, total, pct)
                        except:
                            pass
            
            self.process.wait()
            success = self.process.returncode == 0
            self.build_finished.emit(success)
            
        except Exception as e:
            self.output_ready.emit(f"\n*** ERROR ***: {str(e)}\n")
            self.build_finished.emit(False)
    
    def stop(self):
        """Stop the build process"""
        if self.process:
            self.process.terminate()


class BTGui(QMainWindow):
    """Main GUI window for BIOS Tool"""
    
    def __init__(self):
        super().__init__()
        self.bt_path = os.path.dirname(os.path.abspath(__file__))
        self.discovery = WorkspaceDiscovery(self.bt_path)
        self.build_thread = None
        self.current_workspace = None
        self.current_platform = None
        
        self.init_ui()
        self.discover_workspaces()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle('BIOS Build Tool - GUI')
        self.setGeometry(100, 100, 1400, 900)
        
        # Central widget with main layout
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Top toolbar
        toolbar = self.create_toolbar()
        main_layout.addLayout(toolbar)
        
        # Main content area (splitter)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Workspace tree
        left_panel = self.create_workspace_panel()
        splitter.addWidget(left_panel)
        
        # Right panel: Build output and controls
        right_panel = self.create_build_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([400, 1000])
        main_layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('Ready')
        
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
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
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
        """)
    
    def create_toolbar(self):
        """Create top toolbar with action buttons"""
        layout = QHBoxLayout()
        
        # Workspace selector
        layout.addWidget(QLabel('Workspace:'))
        self.workspace_combo = QComboBox()
        self.workspace_combo.setMinimumWidth(300)
        self.workspace_combo.currentTextChanged.connect(self.on_workspace_changed)
        layout.addWidget(self.workspace_combo)
        
        layout.addStretch()
        
        # Action buttons
        refresh_btn = QPushButton('🔄 Refresh')
        refresh_btn.clicked.connect(self.discover_workspaces)
        layout.addWidget(refresh_btn)
        
        return layout
    
    def create_workspace_panel(self):
        """Create left panel with workspace tree"""
        group = QGroupBox('Available Platforms')
        group.setStyleSheet('QGroupBox { font-weight: bold; color: #000000; }')
        layout = QVBoxLayout()
        
        # Platform tree
        self.platform_tree = QTreeWidget()
        self.platform_tree.setHeaderLabels(['Platform', 'Info'])
        self.platform_tree.setColumnWidth(0, 200)
        self.platform_tree.setColumnWidth(1, 300)
        self.platform_tree.setAlternatingRowColors(False)  # Disable to avoid spacing issues
        self.platform_tree.setUniformRowHeights(True)
        self.platform_tree.setRootIsDecorated(False)  # Remove expand/collapse icons
        self.platform_tree.setIndentation(0)  # Remove indentation
        self.platform_tree.setStyleSheet('''
            QTreeWidget { 
                background-color: white; 
                color: black;
                outline: 0;
            }
            QTreeWidget::item {
                padding: 4px 2px;
                margin: 0px;
                border: 0px;
            }
            QTreeWidget::item:hover {
                background-color: #e5f3ff;
                color: black;
            }
            QTreeWidget::item:selected {
                background-color: #0078d4;
                color: white;
            }
        ''')
        self.platform_tree.itemDoubleClicked.connect(self.on_platform_selected)
        layout.addWidget(self.platform_tree)
        
        group.setLayout(layout)
        return group
    
    def create_build_panel(self):
        """Create right panel with build controls and output"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Build configuration
        config_group = QGroupBox('Build Configuration')
        config_group.setStyleSheet('QGroupBox { font-weight: bold; color: #000000; }')
        config_layout = QVBoxLayout()
        
        # Platform info
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel('Platform:'))
        self.platform_label = QLabel('<none selected>')
        self.platform_label.setStyleSheet('font-weight: bold; color: #0078d4;')
        info_layout.addWidget(self.platform_label)
        info_layout.addStretch()
        config_layout.addLayout(info_layout)
        
        # Build type selector
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel('Build Type:'))
        self.build_type_combo = QComboBox()
        self.build_type_combo.addItems(['DEBUG', 'RELEASE'])
        type_layout.addWidget(self.build_type_combo)
        type_layout.addStretch()
        config_layout.addLayout(type_layout)
        
        # Build buttons
        btn_layout = QHBoxLayout()
        self.build_btn = QPushButton('▶ Build')
        self.build_btn.setEnabled(False)
        self.build_btn.clicked.connect(self.start_build)
        btn_layout.addWidget(self.build_btn)
        
        self.stop_btn = QPushButton('⏹ Stop')
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_build)
        btn_layout.addWidget(self.stop_btn)
        
        self.clean_btn = QPushButton('🧹 Clean')
        self.clean_btn.setEnabled(False)
        btn_layout.addWidget(self.clean_btn)
        
        btn_layout.addStretch()
        config_layout.addLayout(btn_layout)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Progress
        progress_group = QGroupBox('Build Progress')
        progress_group.setStyleSheet('QGroupBox { font-weight: bold; color: #000000; }')
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel('Modules: 0/0 (0%)')
        progress_layout.addWidget(self.progress_label)
        
        progress_group.setLayout(progress_layout)
        layout.addWidget(progress_group)
        
        # Build output
        output_group = QGroupBox('Build Output')
        output_group.setStyleSheet('QGroupBox { font-weight: bold; color: #000000; }')
        output_layout = QVBoxLayout()
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont('Consolas', 9))
        output_layout.addWidget(self.output_text)
        
        # Clear button
        clear_btn = QPushButton('Clear Output')
        clear_btn.clicked.connect(self.output_text.clear)
        output_layout.addWidget(clear_btn)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        widget.setLayout(layout)
        return widget
    
    def discover_workspaces(self):
        """Discover all workspaces and platforms"""
        self.status_bar.showMessage('Discovering workspaces...')
        
        repos = self.discovery.get_repositories()
        print(f"Found {len(repos)} repositories/worktrees: {repos}")
        
        # Update workspace combo
        self.workspace_combo.clear()
        for repo in repos:
            if os.path.isdir(repo):
                self.workspace_combo.addItem(repo)
                print(f"  Added to dropdown: {repo}")
        
        self.status_bar.showMessage(f'Found {len(repos)} workspace(s)', 3000)
        
        # Trigger discovery for first workspace if available
        if self.workspace_combo.count() > 0:
            self.on_workspace_changed(self.workspace_combo.currentText())
    
    def on_workspace_changed(self, workspace):
        """Handle workspace selection change"""
        if not workspace:
            print("No workspace selected")
            return
        
        print(f"\n=== Scanning workspace: {workspace} ===")
        self.current_workspace = workspace
        self.platform_tree.clear()
        self.status_bar.showMessage(f'Scanning {workspace}...')
        
        # Discover platforms
        platforms = self.discovery.discover_platforms(workspace)
        print(f"Found {len(platforms)} platforms")
        
        for platform in platforms:
            # Skip platforms with empty names (shouldn't happen, but be safe)
            if not platform.get('name') or not platform['name'].strip():
                continue
                
            print(f"  Platform: {platform['name']} at {platform['path']}")
            item = QTreeWidgetItem(self.platform_tree)
            
            # Add star for currently active platform
            name = platform['name']
            if platform.get('is_current'):
                name = f"★ {name}"
            item.setText(0, name)
            
            # Build info text
            info_parts = []
            if platform.get('is_current'):
                info_parts.append('ACTIVE')
            if platform['cached_count']:
                info_parts.append(f"{platform['cached_count']} modules")
            if platform['last_build']:
                time_ago = datetime.now() - platform['last_build']
                if time_ago.days > 0:
                    info_parts.append(f"Built {time_ago.days}d ago")
                elif time_ago.seconds > 3600:
                    info_parts.append(f"Built {time_ago.seconds // 3600}h ago")
                else:
                    info_parts.append(f"Built {time_ago.seconds // 60}m ago")
            
            info_text = ', '.join(info_parts) if info_parts else 'Not built'
            item.setText(1, info_text)
            item.setData(0, Qt.ItemDataRole.UserRole, platform)
            print(f"    Info: {info_text}")
        
        self.platform_tree.expandAll()
        self.platform_tree.update()  # Force Qt to refresh the widget
        self.status_bar.showMessage(f'Found {len(platforms)} platform(s) in {os.path.basename(workspace)}', 3000)
        print(f"Tree now has {self.platform_tree.topLevelItemCount()} items\n")
    
    def on_platform_selected(self, item, column):
        """Handle platform selection"""
        platform = item.data(0, Qt.ItemDataRole.UserRole)
        if platform:
            self.current_platform = platform
            self.platform_label.setText(f"{platform['name']} ({platform['path']})")
            self.build_btn.setEnabled(True)
            self.clean_btn.setEnabled(True)
            self.status_bar.showMessage(f"Selected: {platform['name']}")
    
    def start_build(self):
        """Start a build"""
        if not self.current_workspace or not self.current_platform:
            QMessageBox.warning(self, 'No Selection', 'Please select a workspace and platform first.')
            return
        
        platform_name = self.current_platform['name']
        build_type = self.build_type_combo.currentText()
        
        # Clear output
        self.output_text.clear()
        self.output_text.append(f"=== Building {platform_name} ({build_type}) ===\n")
        
        # Reset progress
        self.progress_bar.setValue(0)
        self.progress_label.setText('Starting build...')
        
        # Disable build button, enable stop
        self.build_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # Start build thread
        self.build_thread = BuildThread(self.current_workspace, platform_name, build_type)
        self.build_thread.output_ready.connect(self.append_output)
        self.build_thread.progress_update.connect(self.update_progress)
        self.build_thread.build_finished.connect(self.build_completed)
        self.build_thread.start()
        
        self.status_bar.showMessage(f'Building {platform_name}...')
    
    def stop_build(self):
        """Stop the current build"""
        if self.build_thread:
            self.build_thread.stop()
            self.output_text.append("\n*** Build stopped by user ***\n")
            self.stop_btn.setEnabled(False)
            self.build_btn.setEnabled(True)
            self.status_bar.showMessage('Build stopped')
    
    def append_output(self, text):
        """Append text to build output"""
        # Color-code errors and warnings
        if 'ERROR' in text:
            self.output_text.setTextColor(QColor('#ff6b6b'))
        elif 'WARNING' in text:
            self.output_text.setTextColor(QColor('#ffd93d'))
        else:
            self.output_text.setTextColor(QColor('#d4d4d4'))
        
        self.output_text.insertPlainText(text)
        self.output_text.setTextColor(QColor('#d4d4d4'))
        
        # Auto-scroll to bottom
        cursor = self.output_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.output_text.setTextCursor(cursor)
    
    def update_progress(self, current, total, percentage):
        """Update progress bar"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.progress_label.setText(f'Modules: {current}/{total} ({percentage}%)')
    
    def build_completed(self, success):
        """Handle build completion"""
        self.build_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        if success:
            self.output_text.append("\n=== Build completed successfully ===\n")
            self.status_bar.showMessage('Build completed successfully!', 5000)
            QMessageBox.information(self, 'Build Complete', 
                                   f'{self.current_platform["name"]} built successfully!')
        else:
            self.output_text.append("\n=== Build failed ===\n")
            self.status_bar.showMessage('Build failed', 5000)
            QMessageBox.warning(self, 'Build Failed', 
                               f'{self.current_platform["name"]} build failed. Check output for errors.')
        
        # Refresh platform info (cache may have updated)
        self.on_workspace_changed(self.current_workspace)


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Modern look
    
    window = BTGui()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
