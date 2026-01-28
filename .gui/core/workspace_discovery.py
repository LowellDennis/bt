"""Workspace discovery - discovers repositories, platforms, and build configurations"""

import os
import subprocess
from datetime import datetime


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
