import * as vscode from 'vscode';
import * as cp from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

/**
 * Manages execution of BT commands
 */
export class BTCommandRunner {
    private outputChannel: vscode.OutputChannel;
    private diagnosticCollection: vscode.DiagnosticCollection;
    private btPath: string;
    private btType: 'python' | 'powershell';
    private terminal: vscode.Terminal | undefined;
    
    constructor(workspaceRoot: string, extensionPath: string) {
        this.outputChannel = vscode.window.createOutputChannel('BIOS Tool');
        this.diagnosticCollection = vscode.languages.createDiagnosticCollection('bt');
        
        // Try to find bt in multiple locations:
        // 1. Installed in PATH (preferred - uses system-installed version)
        // 2. Bundled with extension (fallback for users without bt installed)
        
        const bundledBtDir = path.join(extensionPath, 'bt-tool');
        const bundledBtPy = path.join(bundledBtDir, 'bt.py');
        const bundledBtPs1 = path.join(bundledBtDir, 'bt.ps1');
        
        // First, try to find bt in PATH
        const btInPath = this.findBtInPath();
        
        if (btInPath) {
            // Use system-installed version
            this.btPath = btInPath.path;
            this.btType = btInPath.type;
            console.log(`Using bt from PATH: ${this.btPath}`);
        } else if (process.platform === 'win32' && fs.existsSync(bundledBtPs1)) {
            // Fall back to bundled PowerShell version
            this.btPath = bundledBtPs1;
            this.btType = 'powershell';
            console.log(`Using bundled bt.ps1: ${this.btPath}`);
        } else if (fs.existsSync(bundledBtPy)) {
            // Fall back to bundled Python version
            this.btPath = bundledBtPy;
            this.btType = 'python';
            console.log(`Using bundled bt.py: ${this.btPath}`);
        } else {
            // Last resort - assume bt is in PATH (will fail if not)
            this.btPath = 'bt';
            this.btType = process.platform === 'win32' ? 'powershell' : 'python';
            console.log('bt not found - will attempt to use from PATH');
        }
    }
    
    /**
     * Check if local BMC setting is configured
     */
    async isBmcConfigured(): Promise<boolean> {
        try {
            // Query bt config to check if BMC is configured
            const bmcValue = await this.getBmcConfig();
            return bmcValue.length > 0;
        } catch (err) {
            console.error('Error checking BMC configuration:', err);
            return false;
        }
    }
    
    /**
     * Check if local ITP setting is enabled
     */
    async isItpEnabled(): Promise<boolean> {
        try {
            const output = await this.runCommandCapture('config', []);
            const match = output.match(/local\.itp\s*=\s*"([^"]*)"/i);
            if (match && match[1].trim()) {
                const value = match[1].trim().toLowerCase();
                return ['on', 'enabled', 'true', 'yes', '1'].includes(value);
            }
        } catch (err) {
            console.error('Error checking ITP configuration:', err);
        }
        return false;
    }
    
    /**
     * Check if BMC is configured by running bt config command
     */
    private async getBmcConfig(): Promise<string> {
        try {
            const output = await this.runCommandCapture('config', []);
            // Parse output for local.bmc setting
            const match = output.match(/local\.bmc\s*=\s*"([^"]*)"/i);
            if (match && match[1].trim()) {
                return match[1].trim();
            }
        } catch (err) {
            console.error('Error getting BMC config:', err);
        }
        return '';
    }
    
    /**
     * Find bt in system PATH
     */
    private findBtInPath(): { path: string, type: 'python' | 'powershell' } | null {
        try {
            // On Windows, check for bt.cmd, bt.ps1, or bt.py in PATH
            if (process.platform === 'win32') {
                // Try PowerShell version first
                const wherePs1 = cp.execSync('where bt.ps1 2>nul', { encoding: 'utf-8' }).trim();
                if (wherePs1) {
                    return { path: wherePs1.split('\n')[0], type: 'powershell' };
                }
                
                // Try CMD wrapper
                const whereCmd = cp.execSync('where bt.cmd 2>nul', { encoding: 'utf-8' }).trim();
                if (whereCmd) {
                    return { path: whereCmd.split('\n')[0], type: 'powershell' };
                }
                
                // Try Python version
                const wherePy = cp.execSync('where bt.py 2>nul', { encoding: 'utf-8' }).trim();
                if (wherePy) {
                    return { path: wherePy.split('\n')[0], type: 'python' };
                }
            } else {
                // On Unix-like systems
                const whichBt = cp.execSync('which bt 2>/dev/null', { encoding: 'utf-8' }).trim();
                if (whichBt) {
                    return { path: whichBt, type: 'python' };
                }
            }
        } catch (err) {
            // Command not found - will fall back to bundled version
        }
        
        return null;
    }
    
    /**
     * Run a BT command in the integrated terminal
     */
    async runInTerminal(command: string, args: string[] = []): Promise<void> {
        // Get or create terminal
        if (!this.terminal || this.terminal.exitStatus !== undefined) {
            this.terminal = vscode.window.createTerminal({
                name: 'BIOS Tool',
                cwd: vscode.workspace.workspaceFolders?.[0].uri.fsPath
            });
        }
        
        this.terminal.show();
        
        // Build command
        const cmdExe = this.btType === 'powershell' ? 'powershell' : 'python';
        const cmdArgs = this.btType === 'powershell'
            ? `-ExecutionPolicy Bypass -File "${this.btPath}" ${command} ${args.join(' ')}`
            : `"${this.btPath}" ${command} ${args.join(' ')}`;
        
        const fullCommand = this.btType === 'powershell' 
            ? `${cmdExe} ${cmdArgs}`
            : `${cmdExe} ${cmdArgs}`;
        
        this.terminal.sendText(fullCommand);
    }
    
    /**
     * Run a BT command and return output as string
     */
    async runCommandCapture(command: string, args: string[] = []): Promise<string> {
        const cmdArgs = this.btType === 'powershell'
            ? ['-ExecutionPolicy', 'Bypass', '-File', this.btPath, command, ...args]
            : [this.btPath, command, ...args];
        const cmdExe = this.btType === 'powershell' ? 'powershell' : 'python';
        
        return new Promise((resolve, reject) => {
            const proc = cp.spawn(cmdExe, cmdArgs, {
                cwd: vscode.workspace.workspaceFolders?.[0].uri.fsPath,
                shell: true
            });
            
            let output = '';
            
            proc.stdout.on('data', (data: Buffer) => {
                output += data.toString();
            });
            
            proc.stderr.on('data', (data: Buffer) => {
                output += data.toString();
            });
            
            proc.on('close', (code) => {
                if (code === 0) {
                    resolve(output);
                } else {
                    reject(new Error(`Command failed with exit code ${code}`));
                }
            });
        });
    }
    
    /**
     * Run a BT command
     */
    async runCommand(command: string, args: string[] = [], options?: { showProgress?: boolean }): Promise<void> {
        this.outputChannel.show(true);
        this.outputChannel.appendLine(`\n▶ Running: bt ${command} ${args.join(' ')}`);
        this.outputChannel.appendLine('─'.repeat(80));
        
        const cmdArgs = this.btType === 'powershell'
            ? ['-ExecutionPolicy', 'Bypass', '-File', this.btPath, command, ...args]
            : [this.btPath, command, ...args];
        const cmdExe = this.btType === 'powershell' ? 'powershell' : 'python';
        
        return new Promise((resolve, reject) => {
            if (options?.showProgress) {
                vscode.window.withProgress({
                    location: vscode.ProgressLocation.Notification,
                    title: `BT: ${command}`,
                    cancellable: true
                }, (progress, token) => {
                    return this.executeWithProgress(cmdExe, cmdArgs, progress, token);
                }).then(resolve, reject);
            } else {
                this.execute(cmdExe, cmdArgs).then(resolve, reject);
            }
        });
    }
    
    /**
     * Execute command with progress reporting
     */
    private executeWithProgress(
        command: string,
        args: string[],
        progress: vscode.Progress<{ message?: string; increment?: number }>,
        token: vscode.CancellationToken
    ): Promise<void> {
        return new Promise((resolve, reject) => {
            const proc = cp.spawn(command, args, {
                cwd: vscode.workspace.workspaceFolders?.[0].uri.fsPath,
                shell: true
            });
            
            let moduleCount = 0;
            let totalModules = 0;
            const diagnostics: vscode.Diagnostic[] = [];
            
            // Handle cancellation
            token.onCancellationRequested(() => {
                proc.kill();
                this.outputChannel.appendLine('\n✖ Cancelled by user');
            });
            
            proc.stdout.on('data', (data: Buffer) => {
                const output = data.toString();
                this.outputChannel.append(output);
                
                // Parse progress - new format: mm:ss, ####:#####/##### bar##%, Error #
                // Captures: elapsed time, module count, line count/total, progress bar, percentage, errors
                const progressMatch = output.match(/(\d+:\d+),\s+(\d+):(\d+)\/(\d+)\s+[^\d]*(\d+)%,\s+Error\s+(\d+)/);
                if (progressMatch) {
                    const elapsedTime = progressMatch[1];
                    moduleCount = parseInt(progressMatch[2]);
                    const linesProcessed = parseInt(progressMatch[3]);
                    const totalLines = parseInt(progressMatch[4]);
                    const percentage = parseInt(progressMatch[5]);
                    const errorCount = parseInt(progressMatch[6]);
                    
                    progress.report({
                        message: `${moduleCount} modules, ${linesProcessed}/${totalLines} lines (${percentage}%) - ${errorCount} errors`,
                        increment: percentage
                    });
                }
                
                // Parse errors/warnings
                this.parseProblems(output, diagnostics);
            });
            
            proc.stderr.on('data', (data: Buffer) => {
                this.outputChannel.append(data.toString());
            });
            
            proc.on('close', (code) => {
                this.outputChannel.appendLine(`\n${'─'.repeat(80)}`);
                if (code === 0) {
                    this.outputChannel.appendLine('✓ Command completed successfully');
                    resolve();
                } else {
                    this.outputChannel.appendLine(`✖ Command failed with exit code ${code}`);
                    reject(new Error(`Command failed with exit code ${code}`));
                }
                
                // Update diagnostics
                this.updateDiagnostics(diagnostics);
            });
        });
    }
    
    /**
     * Execute command without progress
     */
    private execute(command: string, args: string[]): Promise<void> {
        return new Promise((resolve, reject) => {
            const proc = cp.spawn(command, args, {
                cwd: vscode.workspace.workspaceFolders?.[0].uri.fsPath,
                shell: true
            });
            
            const diagnostics: vscode.Diagnostic[] = [];
            
            proc.stdout.on('data', (data: Buffer) => {
                const output = data.toString();
                this.outputChannel.append(output);
                this.parseProblems(output, diagnostics);
            });
            
            proc.stderr.on('data', (data: Buffer) => {
                this.outputChannel.append(data.toString());
            });
            
            proc.on('close', (code) => {
                this.outputChannel.appendLine(`\n${'─'.repeat(80)}`);
                if (code === 0) {
                    this.outputChannel.appendLine('✓ Command completed successfully');
                    resolve();
                } else {
                    this.outputChannel.appendLine(`✖ Command failed with exit code ${code}`);
                    reject(new Error(`Command failed with exit code ${code}`));
                }
                
                this.updateDiagnostics(diagnostics);
            });
        });
    }
    
    /**
     * Parse errors and warnings from output
     */
    private parseProblems(output: string, diagnostics: vscode.Diagnostic[]): void {
        // Match format: filepath(line): error/warning CODE: message
        const problemRegex = /^(.+?)\((\d+)\):\s+(error|warning)\s+(\w+):\s+(.+)$/gim;
        let match;
        
        while ((match = problemRegex.exec(output)) !== null) {
            const [, filePath, lineStr, severity, code, message] = match;
            const line = parseInt(lineStr) - 1; // Convert to 0-based
            
            const diagnostic = new vscode.Diagnostic(
                new vscode.Range(line, 0, line, Number.MAX_SAFE_INTEGER),
                `${code}: ${message}`,
                severity.toLowerCase() === 'error' 
                    ? vscode.DiagnosticSeverity.Error 
                    : vscode.DiagnosticSeverity.Warning
            );
            diagnostic.source = 'bt';
            
            diagnostics.push(diagnostic);
        }
    }
    
    /**
     * Update diagnostics collection
     */
    private updateDiagnostics(diagnostics: vscode.Diagnostic[]): void {
        this.diagnosticCollection.clear();
        
        // Group diagnostics by file
        const fileMap = new Map<string, vscode.Diagnostic[]>();
        for (const diag of diagnostics) {
            // Note: We'd need the full file path from bt output
            // For now, this is a placeholder
        }
        
        // Set diagnostics
        for (const [file, diags] of fileMap) {
            this.diagnosticCollection.set(vscode.Uri.file(file), diags);
        }
    }
    
    dispose(): void {
        this.outputChannel.dispose();
        this.diagnosticCollection.dispose();
    }
}
