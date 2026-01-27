import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';

/**
 * Represents a BT command in the tree
 */
export class BTCommand extends vscode.TreeItem {
    constructor(
        public readonly commandName: string,
        public readonly displayName: string,
        public readonly description: string = '',
        public readonly icon: string = 'symbol-misc'
    ) {
        super(displayName, vscode.TreeItemCollapsibleState.None);
        
        this.tooltip = description;
        this.description = ''; // Don't show description inline, only in tooltip
        this.contextValue = 'btCommand';
        this.iconPath = new vscode.ThemeIcon(icon);
        this.command = {
            command: `BIOSTool.${commandName}`,
            title: displayName
        };
    }
}

/**
 * Represents a BIOS platform in the tree
 */
export class Platform extends vscode.TreeItem {
    constructor(
        public readonly name: string,
        public readonly platformPath: string,
        public readonly workspacePath: string,
        public readonly isCurrent: boolean = false
    ) {
        super(name, vscode.TreeItemCollapsibleState.None);
        
        this.tooltip = platformPath;
        this.description = isCurrent ? '(active)' : '';
        this.contextValue = 'platform';
        
        // Icon for platform
        this.iconPath = new vscode.ThemeIcon(
            isCurrent ? 'check' : 'circuit-board',
            isCurrent ? new vscode.ThemeColor('charts.green') : undefined
        );
    }
}

/**
 * Tree data provider for BIOS platforms
 */
export class PlatformTreeProvider implements vscode.TreeDataProvider<BTCommand | Platform> {
    private _onDidChangeTreeData: vscode.EventEmitter<BTCommand | Platform | undefined | null | void> = new vscode.EventEmitter<BTCommand | Platform | undefined | null | void>();
    readonly onDidChangeTreeData: vscode.Event<BTCommand | Platform | undefined | null | void> = this._onDidChangeTreeData.event;
    
    constructor(private workspaceRoot: string | undefined) {}
    
    refresh(): void {
        this._onDidChangeTreeData.fire();
    }
    
    getTreeItem(element: BTCommand | Platform): vscode.TreeItem {
        return element;
    }
    
    async getChildren(element?: BTCommand | Platform): Promise<(BTCommand | Platform)[]> {
        if (!this.workspaceRoot) {
            return [];
        }
        
        if (element) {
            // No children for commands or platforms
            return [];
        } else {
            // Show commands at root level
            return this.getCommands();
        }
    }
    
    /**
     * Get list of available BT commands
     */
    private getCommands(): BTCommand[] {
        return [
            new BTCommand('attach', 'Attach', 'Attach a repository', 'add'),
            new BTCommand('build', 'Build', 'Build current platform', 'gear'),
            new BTCommand('cleanup', 'Cleanup', 'Cleanup build artifacts', 'trash'),
            new BTCommand('config', 'Config', 'View/change configuration settings', 'settings-gear'),
            new BTCommand('create', 'Create', 'Create a new worktree', 'new-folder'),
            new BTCommand('remove', 'Remove', 'Remove a worktree', 'trash'),
            new BTCommand('detach', 'Detach', 'Detach a repository', 'remove'),
            new BTCommand('init', 'Init', 'Initialize platform settings', 'symbol-namespace'),
            new BTCommand('jump', 'Jump', 'Sync to Jump Station', 'debug-disconnect'),
            new BTCommand('merge', 'Merge', 'Merge updates from upstream', 'git-merge'),
            new BTCommand('move', 'Move', 'Move BIOS worktree', 'file-symlink-directory'),
            new BTCommand('fetch', 'Fetch', 'Fetch from remote location', 'cloud-download'),
            new BTCommand('push', 'Push', 'Push updates to remote', 'cloud-upload'),
            new BTCommand('select', 'Select', 'Select BIOS repository', 'folder-opened'),
            new BTCommand('status', 'Status', 'Show repository status', 'list-tree'),
            new BTCommand('use', 'Use', 'Use different worktree', 'arrow-swap'),
            new BTCommand('top', 'Top', 'Go to repository top', 'arrow-up'),
            new BTCommand('worktrees', 'Worktrees', 'List all worktrees', 'list-tree')
        ];
    }
    
    /**
     * Discover platforms in the workspace
     */
    async discoverPlatforms(): Promise<Platform[]> {
        if (!this.workspaceRoot) {
            return [];
        }
        
        const platforms: Platform[] = [];
        const currentPlatform = await this.getCurrentPlatform();
        
        // Search for PlatformPkg.dsc files
        const pattern = new vscode.RelativePattern(this.workspaceRoot, '**/PlatformPkg.dsc');
        const files = await vscode.workspace.findFiles(pattern, '**/node_modules/**', 50);
        
        for (const file of files) {
            const platformDir = path.dirname(file.fsPath);
            const platformName = this.extractPlatformName(platformDir);
            
            if (platformName && this.isValidPlatform(platformName)) {
                platforms.push(new Platform(
                    platformName,
                    platformDir,
                    this.workspaceRoot,
                    platformName.toLowerCase() === currentPlatform?.toLowerCase()
                ));
            }
        }
        
        // Sort: current platform first, then alphabetically
        platforms.sort((a, b) => {
            if (a.isCurrent && !b.isCurrent) {
                return -1;
            }
            if (!a.isCurrent && b.isCurrent) {
                return 1;
            }
            return a.name.localeCompare(b.name);
        });
        
        return platforms;
    }
    
    /**
     * Extract platform name from directory path
     */
    private extractPlatformName(dirPath: string): string | null {
        const dirName = path.basename(dirPath);
        // Remove 'Pkg' suffix if present
        if (dirName.endsWith('Pkg')) {
            return dirName.slice(0, -3);
        }
        return dirName;
    }
    
    /**
     * Check if platform name is valid (e.g., U68, G11)
     */
    private isValidPlatform(name: string): boolean {
        // Match pattern: Letter + 2 digits
        return /^[A-Z]\d{2}$/i.test(name);
    }
    
    /**
     * Get current platform from .bt/name or local.txt
     */
    private async getCurrentPlatform(): Promise<string | null> {
        if (!this.workspaceRoot) {
            return null;
        }
        
        // First check .bt/name (created by bt init)
        const btNameFile = path.join(this.workspaceRoot, '.bt', 'name');
        if (fs.existsSync(btNameFile)) {
            try {
                const name = await fs.promises.readFile(btNameFile, 'utf-8');
                const platformName = name.trim();
                if (platformName) {
                    return platformName;
                }
            } catch (err) {
                // Ignore errors and try local.txt
            }
        }
        
        // Fall back to local.txt
        const localFile = path.join(this.workspaceRoot, 'local.txt');
        if (!fs.existsSync(localFile)) {
            return null;
        }
        
        try {
            const content = await fs.promises.readFile(localFile, 'utf-8');
            for (const line of content.split('\n')) {
                if (line.trim().startsWith('platform')) {
                    // Format: platform, <path>
                    const parts = line.split(',');
                    if (parts.length > 1) {
                        const platformPath = parts[1].trim();
                        const platformName = path.basename(platformPath);
                        if (platformName.endsWith('Pkg')) {
                            return platformName.slice(0, -3);
                        }
                        return platformName;
                    }
                }
            }
        } catch (err) {
            // Ignore errors
        }
        
        return null;
    }
}
