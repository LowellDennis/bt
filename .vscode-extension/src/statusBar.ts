import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';

/**
 * Manages status bar item showing current repo, worktree, and platform
 */
export class BTStatusBar {
    private statusBarItem: vscode.StatusBarItem;
    
    constructor() {
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Left,
            100
        );
        this.statusBarItem.command = 'BIOSTool.use';
        this.statusBarItem.show();
        this.updatePlatform();
    }
    
    /**
     * Update status bar with VCS type, repo/worktree, and platform
     */
    async updatePlatform(): Promise<void> {
        const workspaceRoot = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
        if (!workspaceRoot) {
            this.statusBarItem.hide();
            return;
        }
        
        // Find VCS root by searching up from current directory
        const vcsInfo = await this.findVCSRoot(workspaceRoot);
        
        // Get platform from .bt/name
        const platform = await this.getCurrentPlatform(workspaceRoot);
        
        // Build status bar text
        const parts: string[] = [];
        
        if (vcsInfo) {
            // Add VCS icon and repo info
            const vcsIcon = '$(wrench)';
            const repoName = path.basename(vcsInfo.repoRoot);
            
            if (vcsInfo.type === 'git' && vcsInfo.worktreeName) {
                // Git with worktree: show repo/worktree
                parts.push(`${vcsIcon} ${repoName}/${vcsInfo.worktreeName}`);
            } else {
                // Git without worktree or SVN: just show repo
                parts.push(`${vcsIcon} ${repoName}`);
            }
        }
        
        // Add platform info
        if (platform) {
            parts.push(`$(wrench) ${platform}`);
        }
        
        if (parts.length > 0) {
            this.statusBarItem.text = parts.join(' | ');
            const tooltipParts: string[] = [];
            if (vcsInfo) {
                tooltipParts.push(`VCS: ${vcsInfo.type.toUpperCase()}`);
                tooltipParts.push(`Repository: ${vcsInfo.repoRoot}`);
                if (vcsInfo.worktreeName) {
                    tooltipParts.push(`Worktree: ${vcsInfo.worktreeName}`);
                }
            }
            if (platform) {
                tooltipParts.push(`Platform: ${platform}`);
            }
            tooltipParts.push('\nClick to use different workspace');
            this.statusBarItem.tooltip = tooltipParts.join('\n');
            this.statusBarItem.show();
        } else {
            this.statusBarItem.text = '$(question) No Info';
            this.statusBarItem.tooltip = 'No repository or platform information available';
            this.statusBarItem.show();
        }
    }
    
    /**
     * Find VCS root by searching up from directory
     */
    private async findVCSRoot(startDir: string): Promise<{type: 'git' | 'svn', repoRoot: string, worktreeName?: string} | null> {
        let currentDir = startDir;
        
        while (true) {
            // Check for .git
            const gitDir = path.join(currentDir, '.git');
            if (fs.existsSync(gitDir)) {
                // Check if this is a worktree by looking for .git file instead of directory
                const gitStat = fs.statSync(gitDir);
                let worktreeName: string | undefined;
                
                if (gitStat.isFile()) {
                    // This is a worktree - the .git file contains "gitdir: <path>"
                    const gitContent = fs.readFileSync(gitDir, 'utf-8');
                    const match = gitContent.match(/gitdir:\s*(.+)/);
                    if (match) {
                        // Extract worktree name from current directory
                        worktreeName = path.basename(currentDir);
                        // The gitdir points to <repo>/.git/worktrees/<name>
                        // Go up 3 levels to get to the actual repo root
                        const gitWorktreePath = match[1].trim();
                        const repoRoot = path.dirname(path.dirname(path.dirname(gitWorktreePath)));
                        return { type: 'git', repoRoot, worktreeName };
                    }
                }
                
                return { type: 'git', repoRoot: currentDir };
            }
            
            // Check for .svn
            const svnDir = path.join(currentDir, '.svn');
            if (fs.existsSync(svnDir)) {
                return { type: 'svn', repoRoot: currentDir };
            }
            
            // Move up one level
            const parentDir = path.dirname(currentDir);
            if (parentDir === currentDir) {
                // Reached root of filesystem
                break;
            }
            currentDir = parentDir;
        }
        
        // Not found - check %USERPROFILE%\.bt\repo
        const userProfile = process.env.USERPROFILE || process.env.HOME;
        if (userProfile) {
            const repoFile = path.join(userProfile, '.bt', 'repo');
            if (fs.existsSync(repoFile)) {
                try {
                    const repoPath = fs.readFileSync(repoFile, 'utf-8').trim();
                    if (repoPath && fs.existsSync(repoPath)) {
                        // Determine VCS type
                        if (fs.existsSync(path.join(repoPath, '.git'))) {
                            return { type: 'git', repoRoot: repoPath };
                        } else if (fs.existsSync(path.join(repoPath, '.svn'))) {
                            return { type: 'svn', repoRoot: repoPath };
                        }
                    }
                } catch (err) {
                    // Ignore errors reading repo file
                }
            }
        }
        
        return null;
    }
    
    /**
     * Get current platform from .bt/name
     */
    private async getCurrentPlatform(startDir: string): Promise<string | null> {
        // Search up from current directory for VCS root, then look for .bt/name
        let currentDir = startDir;
        
        while (true) {
            // Check if we're at a VCS root
            const isVCSRoot = fs.existsSync(path.join(currentDir, '.git')) || 
                            fs.existsSync(path.join(currentDir, '.svn'));
            
            if (isVCSRoot) {
                // Look for .bt/name at this level
                const btNameFile = path.join(currentDir, '.bt', 'name');
                if (fs.existsSync(btNameFile)) {
                    try {
                        const name = fs.readFileSync(btNameFile, 'utf-8');
                        const platformName = name.trim();
                        if (platformName) {
                            return platformName;
                        }
                    } catch (err) {
                        // Ignore read errors
                    }
                }
                break; // Found VCS root, don't search further
            }
            
            // Move up one level
            const parentDir = path.dirname(currentDir);
            if (parentDir === currentDir) {
                // Reached root of filesystem
                break;
            }
            currentDir = parentDir;
        }
        
        return null;
    }
    
    dispose(): void {
        this.statusBarItem.dispose();
    }
}
