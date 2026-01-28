"""
Main GUI window for BIOS Tool
"""

import os
import sys
import re
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QGroupBox, QStatusBar, QTabWidget, QMessageBox,
                             QInputDialog, QFileDialog, QToolButton, QMenu)
from PyQt6.QtCore import Qt, QTimer, QProcess
from PyQt6.QtGui import QTextCursor, QIcon

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from widgets import WorkspaceTab
from core import WorkspaceDiscovery


class BTGui(QMainWindow):
    """Main GUI window for BIOS Tool"""
    
    def __init__(self):
        super().__init__()
        self.bt_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.discovery = WorkspaceDiscovery(self.bt_path)
        self.workspace_tabs = {}
        self.building_tab = None  # Track which tab has an active build (only one at a time due to U: drive mapping)
        
        self.init_ui()
        self.discover_workspaces()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle('BIOS Build Tool - GUI')
        
        # Set window icon (try .icns for macOS, .ico for Windows/Linux)
        for icon_file in ['biostool.icns', 'biostool.ico']:
            icon_path = os.path.join(self.bt_path, icon_file)
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                break
        
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
        
        # If no repositories found, prompt user to select one or more
        if not repos:
            result = QMessageBox.question(
                self,
                'No Repositories Found',
                'No BIOS repositories have been attached yet.\n\n'
                'Would you like to select repository directories now?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if result == QMessageBox.StandardButton.Yes:
                # Prompt for multiple repository selections
                selected_repos = []
                while True:
                    repo_path = QFileDialog.getExistingDirectory(
                        self,
                        'Select BIOS Repository Directory',
                        os.path.expanduser('~'),
                        QFileDialog.Option.ShowDirsOnly
                    )
                    
                    if repo_path:
                        selected_repos.append(repo_path)
                        
                        # Ask if they want to add another
                        add_more = QMessageBox.question(
                            self,
                            'Add Another Repository?',
                            f'Added: {os.path.basename(repo_path)}\n\n'
                            'Would you like to add another repository?',
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                        )
                        
                        if add_more == QMessageBox.StandardButton.No:
                            break
                    else:
                        # User canceled
                        break
                
                # Attach selected repositories
                if selected_repos:
                    cache_dir = os.path.join(os.path.expanduser('~'), '.bt')
                    os.makedirs(cache_dir, exist_ok=True)
                    repo_file = os.path.join(cache_dir, 'repositories')
                    
                    # Append to existing repos if any
                    existing = []
                    if os.path.exists(repo_file):
                        with open(repo_file, 'r') as f:
                            existing = [line.strip() for line in f if line.strip()]
                    
                    # Add new repos
                    all_repos = existing + selected_repos
                    with open(repo_file, 'w') as f:
                        for repo in all_repos:
                            f.write(f'{repo}\n')
                    
                    # Re-discover with new repos
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
