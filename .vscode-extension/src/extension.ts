// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
import * as vscode from 'vscode';
import { PlatformTreeProvider, Platform, BTCommand } from './platformProvider';
import { BTCommandRunner } from './btRunner';
import { BTStatusBar } from './statusBar';

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
export function activate(context: vscode.ExtensionContext) {
	console.log('BIOS Tool extension is now active!');
	
	const workspaceRoot = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
	if (!workspaceRoot) {
		return;
	}
	
	// Initialize components
	const platformProvider = new PlatformTreeProvider(workspaceRoot);
	const btRunner = new BTCommandRunner(workspaceRoot, context.extensionPath);
	const statusBar = new BTStatusBar();
	
	// Register tree view
	const treeView = vscode.window.createTreeView('biosToolPlatforms', {
		treeDataProvider: platformProvider,
		showCollapseAll: false
	});
	
	// Register commands
	context.subscriptions.push(
		vscode.commands.registerCommand('BIOSTool.refreshPlatforms', () => {
			platformProvider.refresh();
			statusBar.updatePlatform();
		}),
		
		vscode.commands.registerCommand('BIOSTool.attach', async () => {
			// Open folder picker
			const folderUri = await vscode.window.showOpenDialog({
				canSelectFiles: false,
				canSelectFolders: true,
				canSelectMany: false,
				openLabel: 'Select Repository'
			});
			
			if (!folderUri || folderUri.length === 0) {
				return;
			}
			
			const folderPath = folderUri[0].fsPath;
			const fs = require('fs');
			const path = require('path');
			
			// Validate it's a git or svn repository
			const isGit = fs.existsSync(path.join(folderPath, '.git'));
			const isSvn = fs.existsSync(path.join(folderPath, '.svn'));
			
			if (!isGit && !isSvn) {
				vscode.window.showErrorMessage('Selected folder is not a git or svn repository');
				return;
			}
			
			// Get user profile directory
			const userProfile = process.env.USERPROFILE || process.env.HOME;
			if (!userProfile) {
				vscode.window.showErrorMessage('Could not determine user profile directory');
				return;
			}
			
			const btDir = path.join(userProfile, '.bt');
			const reposFile = path.join(btDir, 'repositories');
			
			// Create .bt directory if it doesn't exist
			if (!fs.existsSync(btDir)) {
				fs.mkdirSync(btDir, { recursive: true });
			}
			
			// Read existing repositories
			let repos: string[] = [];
			if (fs.existsSync(reposFile)) {
				const content = fs.readFileSync(reposFile, 'utf-8');
				repos = content.split(';').filter((r: string) => r.trim().length > 0);
			}
			
			// Check if already attached
			const normalizedPath = folderPath.toLowerCase();
			if (repos.some((r: string) => r.toLowerCase() === normalizedPath)) {
				vscode.window.showInformationMessage('Repository already attached');
				return;
			}
			
			// Add new repository
			repos.push(folderPath);
			
			// Write back to file
			fs.writeFileSync(reposFile, repos.join(';'), 'utf-8');
			
			vscode.window.showInformationMessage(`Repository attached: ${folderPath}`);
			platformProvider.refresh();
		}),
		
		vscode.commands.registerCommand('BIOSTool.detach', async () => {
			const fs = require('fs');
			const path = require('path');
			
			// Get user profile directory
			const userProfile = process.env.USERPROFILE || process.env.HOME;
			if (!userProfile) {
				vscode.window.showErrorMessage('Could not determine user profile directory');
				return;
			}
			
			const reposFile = path.join(userProfile, '.bt', 'repositories');
			
			// Read existing repositories
			if (!fs.existsSync(reposFile)) {
				vscode.window.showWarningMessage('No repositories found');
				return;
			}
			
			const content = fs.readFileSync(reposFile, 'utf-8');
			const repos = content.split(';').filter((r: string) => r.trim().length > 0);
			
			if (repos.length === 0) {
				vscode.window.showWarningMessage('No repositories found');
				return;
			}
			
			// Show quick pick
			const selected = await vscode.window.showQuickPick(repos, {
				placeHolder: 'Select repository to detach'
			});
			
			if (!selected) {
				return;
			}
			
			// Remove selected repository
			const updatedRepos = repos.filter((r: string) => r !== selected);
			
			// Write back to file
			fs.writeFileSync(reposFile, updatedRepos.join(';'), 'utf-8');
			
			vscode.window.showInformationMessage(`Repository detached: ${selected}`);
			platformProvider.refresh();
		}),
		
		vscode.commands.registerCommand('BIOSTool.init', async () => {
			// Get all platforms
			const platforms = await platformProvider.discoverPlatforms();
			if (platforms.length === 0) {
				vscode.window.showWarningMessage('No platforms found in workspace');
				return;
			}
			
			// Show quick pick
			const items = platforms.map(p => ({
				label: p.name,
				description: p.isCurrent ? '(current)' : '',
				platform: p
			}));
			
			const selected = await vscode.window.showQuickPick(items, {
				placeHolder: 'Choose platform to initialize'
			});
			
			if (selected) {
				await btRunner.runCommand('init', [selected.platform.name]);
				platformProvider.refresh();
				statusBar.updatePlatform();
			}
		}),
		
		vscode.commands.registerCommand('BIOSTool.build', async (platform?: Platform) => {
			// Build command uses currently initialized platform from 'bt init'
			// Run in terminal so progress bar displays properly
			await btRunner.runInTerminal('build');
		}),
		
		vscode.commands.registerCommand('BIOSTool.clean', async (platform?: Platform) => {
			await btRunner.runInTerminal('clean');
		}),
		
			vscode.commands.registerCommand('BIOSTool.config', async () => {
			// Show config menu
			const action = await vscode.window.showQuickPick([
				{ label: '$(list-tree) View All Settings', value: 'viewAll' },
				{ label: '$(edit) Edit Setting', value: 'edit' },
				{ label: '$(eye) View Setting', value: 'view' }
			], {
				placeHolder: 'Choose a config action',
				matchOnDescription: true
			});

			if (!action) {
				return;
			}

			if (action.value === 'viewAll') {
				// Show all settings in terminal
				await btRunner.runInTerminal('config');
			} else if (action.value === 'view' || action.value === 'edit') {
				// Get all settings
				const configOutput = await btRunner.runCommandCapture('config', []);
				
				if (!configOutput) {
					vscode.window.showErrorMessage('Failed to retrieve config settings');
					return;
				}

				// Parse the config output to extract settings
				// Only these settings are editable via the UI
				const editableSettings = new Set([
					'global.email',
					'local.alert',
					'local.bmc',
					'local.release',
					'local.warnings'
				]);

				const settings: { label: string; description: string; value: string; settingName: string; isReadOnly: boolean; scope: string }[] = [];
				const lines = configOutput.split('\n');
				let scope = 'global';

				for (const line of lines) {
					// Detect section headers
					if (line.includes('Global Configurable Items') || line.includes('Global Read-Only Items')) {
						scope = 'global';
						continue;
					} else if (line.includes('Local Configurable Items') || line.includes('Local Read-Only Items')) {
						scope = 'local';
						continue;
					}

					// Parse setting lines (format: "  global.setting  = "value"")
					const match = line.match(/^\s+(global|local)\.(\w+)\s*=\s*"([^"]*)"/);
					if (match) {
						const settingName = match[2];
						const value = match[3];
						const fullSettingName = `${scope}.${settingName}`;
						const isReadOnly = !editableSettings.has(fullSettingName);
						const icon = isReadOnly ? '$(lock)' : '$(edit)';
						const scopeLabel = scope === 'global' ? 'Global' : 'Local';
						
						settings.push({
							label: `${icon} ${scopeLabel}.${settingName}`,
							description: value || '(empty)',
							value: value,
							settingName: settingName,
							isReadOnly: isReadOnly,
							scope: scope
						});
					}
				}

				if (settings.length === 0) {
					vscode.window.showWarningMessage('No settings found');
					return;
				}

				// Show settings list (filter to editable only for edit mode)
				const displaySettings = action.value === 'edit' 
					? settings.filter(s => !s.isReadOnly)
					: settings;
				
				if (action.value === 'edit' && displaySettings.length === 0) {
					vscode.window.showWarningMessage('No editable settings available');
					return;
				}

				const selected = await vscode.window.showQuickPick(displaySettings, {
					placeHolder: action.value === 'view' ? 'Select setting to view' : 'Select setting to edit',
					matchOnDescription: true
				});

				if (!selected) {
					return;
				}

				if (action.value === 'view') {
					// Just show the value
					const detail = selected.isReadOnly ? ' (Read-Only)' : '';
					vscode.window.showInformationMessage(
						`${selected.scope}.${selected.settingName}${detail} = "${selected.value}"`
					);
				} else {
					// Edit mode
					if (selected.isReadOnly) {
						vscode.window.showWarningMessage(`${selected.settingName} is read-only and cannot be edited`);
						return;
					}

					let newValue: string | undefined;

					// For boolean-like settings, show a quick pick
					if (['alert', 'release', 'warnings'].includes(selected.settingName)) {
						const choice = await vscode.window.showQuickPick([
							{ label: 'on', description: 'Enable this setting' },
							{ label: 'off', description: 'Disable this setting' },
							{ label: '(default)', description: 'Reset to default value', value: '' }
						], {
							placeHolder: `Select value for ${selected.scope}.${selected.settingName}`,
							matchOnDescription: true
						});

						if (!choice) {
							return; // User cancelled
						}

						newValue = choice.value !== undefined ? choice.value : choice.label;
					} else {
						// Show input box with current value for other settings
						newValue = await vscode.window.showInputBox({
							prompt: `Enter new value for ${selected.scope}.${selected.settingName}`,
							value: selected.value,
							placeHolder: '(Leave empty to set to default)',
							validateInput: (value) => {
								const trimmedValue = value.trim();
								
								// Special validation for email setting
								if (selected.settingName === 'email' && trimmedValue) {
									// Basic email validation
									const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
									if (!emailRegex.test(trimmedValue)) {
										return 'Please enter a valid email address';
									}
								}
								
								// Special validation for BMC setting
								if (selected.settingName === 'bmc' && trimmedValue) {
									// Format: ilo|openbmc;<ip>;<username>;<password>
									// Or short format: ilo|openbmc;<ip> (uses defaults)
									const parts = trimmedValue.split(';');
									if (parts.length !== 4 && parts.length !== 2) {
										return 'BMC format should be: ilo|openbmc;<ip-address>;<username>;<password> or ilo|openbmc;<ip-address>';
									}
									if (!['ilo', 'openbmc'].includes(parts[0].toLowerCase())) {
										return 'BMC type must be "ilo" or "openbmc"';
									}
									// Validate IP address format
									const ipParts = parts[1].split('.');
									if (ipParts.length !== 4 || !ipParts.every(p => {
										const num = parseInt(p);
										return !isNaN(num) && num >= 0 && num <= 255;
									})) {
										return 'Invalid IP address format';
									}
								}
								return null;
							}
						});

						if (newValue === undefined) {
							return; // User cancelled
						}
					}

					// Run the config command to set the value
					const args = newValue.trim() ? [selected.settingName, newValue] : [selected.settingName, '/default'];
					await btRunner.runInTerminal('config', args);
					
					// Refresh the view
					platformProvider.refresh();
				}
			}
		}),
		
		vscode.commands.registerCommand('BIOSTool.create', async () => {
			// Prompt for branch name
			const branch = await vscode.window.showInputBox({
				prompt: 'Enter branch name for the new worktree',
				placeHolder: 'e.g., feature/my-feature',
				validateInput: (value) => {
					return value.trim() ? null : 'Branch name is required';
				}
			});
			
			if (!branch) {
				return;
			}
			
			// Prompt for worktree path
			const worktree = await vscode.window.showInputBox({
				prompt: 'Enter worktree path (relative to repository)',
				placeHolder: 'e.g., ../my-worktree',
				validateInput: (value) => {
					return value.trim() ? null : 'Worktree path is required';
				}
			});
			
			if (!worktree) {
				return;
			}
			
			// Optionally prompt for commit-ish
			const commitish = await vscode.window.showInputBox({
				prompt: 'Enter commit-ish (optional, default: HEAD)',
				placeHolder: 'commit ID, branch name, or leave empty for HEAD'
			});
			
			// Build command arguments
			const args = [branch, worktree];
			if (commitish && commitish.trim()) {
				args.push(commitish.trim());
			}
			
			await btRunner.runInTerminal('create', args);
			platformProvider.refresh();
			
			// Resolve the full path to the new worktree
			const workspaceRoot = vscode.workspace.workspaceFolders?.[0].uri.fsPath;
			if (workspaceRoot) {
				const path = require('path');
				const worktreePath = path.resolve(workspaceRoot, worktree);
				
				// Open the new worktree in a new VS Code window
				const uri = vscode.Uri.file(worktreePath);
				await vscode.commands.executeCommand('vscode.openFolder', uri, true);
			}
		}),
		
		vscode.commands.registerCommand('BIOSTool.destroy', async () => {
			try {
				// Run bt to get list of worktrees
				const output = await btRunner.runCommandCapture('config', ['worktrees']);
				
				// Parse worktrees from output
				// Expected format: 
				//   global.worktrees  = "D:\path\to\worktree1"
				//                       "D:\path\to\worktree2"
				//                       "D:\path\to\worktree3"
				const lines = output.split('\n');
				const worktrees: string[] = [];
				
				for (const line of lines) {
					const trimmed = line.trim();
					// Match lines with = or continuation lines with just quoted paths
					const match = trimmed.match(/"([^"]+)"/);
					if (match && match[1]) {
						worktrees.push(match[1]);
					}
				}
				
				if (worktrees.length === 0) {
					vscode.window.showWarningMessage('No worktrees found');
					return;
				}
				
				// Show quick pick
				const items = worktrees.map(wt => {
					const path = require('path');
					return {
						label: path.basename(wt),
						description: wt,
						path: wt
					};
				});
				
				const selected = await vscode.window.showQuickPick(items, {
					placeHolder: 'Select worktree to destroy'
				});
				
				if (!selected) {
					return;
				}
				
				await btRunner.runInTerminal('destroy', [selected.path]);
				platformProvider.refresh();
			} catch (err) {
				vscode.window.showErrorMessage(`Failed to destroy worktree: ${err}`);
			}
		}),
		
		vscode.commands.registerCommand('BIOSTool.status', async () => {
			await btRunner.runInTerminal('status');
		}),
		
		vscode.commands.registerCommand('BIOSTool.switch', async () => {
			try {
				// Run bt switch with no args to get list of workspaces
				const output = await btRunner.runCommandCapture('switch', []);
				
				// Parse output - bt switch shows repositories and worktrees
				const lines = output.split('\n');
				const items: Array<{label: string, description: string, path: string, isCurrent: boolean}> = [];
				
				let inRepositories = false;
				let inWorktrees = false;
				
				for (const line of lines) {
					const trimmed = line.trim();
					
					// Detect section headers
					if (trimmed.includes('Available repositories')) {
						inRepositories = true;
						inWorktrees = false;
						continue;
					} else if (trimmed.includes('Available worktrees')) {
						inRepositories = false;
						inWorktrees = true;
						continue;
					}
					
					// Skip header/separator lines
					if (trimmed.startsWith('vcs ') || trimmed.startsWith('---') || !trimmed) {
						continue;
					}
					
					// Parse repository line: "* git d:\hpe\dev\roms\gnext"
					if (inRepositories) {
						const isCurrent = trimmed.startsWith('*');
						const cleaned = trimmed.replace(/^\*\s*/, '').trim();
						const parts = cleaned.split(/\s+/);
						if (parts.length >= 2) {
							const vcs = parts[0];
							const path = parts.slice(1).join(' ').toLowerCase();
							const name = path.split(/[\\/]/).filter(p => p).pop() || path;
							items.push({
								label: name + (isCurrent ? ' ★' : ''),
								description: `Repository: ${path}`,
								path: path,
								isCurrent: isCurrent
							});
						}
					}
					
					// Parse worktree line: "git d:\hpe\dev\roms\bootmenu, D:/HPE/Dev/ROMS/GNext, private/openbmc/bootmenu"
					else if (inWorktrees) {
						const isCurrent = trimmed.startsWith('*');
						const cleaned = trimmed.replace(/^\*\s*/, '').trim();
						const parts = cleaned.split(',');
						if (parts.length >= 2) {
							// First part is "vcs path"
							const firstPart = parts[0].trim().split(/\s+/);
							if (firstPart.length >= 2) {
								const vcs = firstPart[0];
								const path = firstPart.slice(1).join(' ').toLowerCase();
								const branch = parts.length >= 3 ? parts[2].trim() : '';
								const name = path.split(/[\\/]/).filter(p => p).pop() || path;
								items.push({
									label: name + (isCurrent ? ' ★' : ''),
									description: `Worktree: ${path} [${branch}]`,
									path: path,
									isCurrent: isCurrent
								});
							}
						}
					}
				}
				
				if (items.length === 0) {
					vscode.window.showWarningMessage('No repositories or worktrees found');
					return;
				}
				
				// Sort: current items first
				items.sort((a, b) => {
					if (a.isCurrent && !b.isCurrent) {
						return -1;
					}
					if (!a.isCurrent && b.isCurrent) {
						return 1;
					}
					return a.label.localeCompare(b.label);
				});
				
				const selected = await vscode.window.showQuickPick(items, {
					placeHolder: 'Choose workspace to switch to'
				});
				
				if (selected) {
					// Ask if user wants to open in new window or current window
					const openIn = await vscode.window.showQuickPick(
						[{label: 'Current Window', value: false}, {label: 'New Window', value: true}],
						{placeHolder: 'Open workspace in...'}
					);
					
					if (openIn) {
						// Open the workspace
						const uri = vscode.Uri.file(selected.path);
						await vscode.commands.executeCommand('vscode.openFolder', uri, openIn.value);
					}
				}
			} catch (err) {
				vscode.window.showErrorMessage(`Failed to switch: ${err}`);
			}
		}),
		
		vscode.commands.registerCommand('BIOSTool.pull', async () => {
			await btRunner.runInTerminal('pull');
			platformProvider.refresh();
		}),
		
		vscode.commands.registerCommand('BIOSTool.push', async () => {
			await btRunner.runInTerminal('push');
		}),
		
		vscode.commands.registerCommand('BIOSTool.merge', async () => {
			await btRunner.runInTerminal('merge');
			platformProvider.refresh();
		}),
		
		vscode.commands.registerCommand('BIOSTool.select', async () => {
			try {
				// Run bt select with no args to get list of repositories
				const output = await btRunner.runCommandCapture('select', []);
				
				// Parse output - bt select shows available repositories
				const lines = output.split('\n');
				const items: Array<{label: string, description: string, path: string, isCurrent: boolean}> = [];
				
				for (const line of lines) {
					const trimmed = line.trim();
					
					// Skip header/separator lines
					if (trimmed.startsWith('vcs ') || trimmed.startsWith('---') || !trimmed || trimmed.includes('Available repositories')) {
						continue;
					}
					
					// Parse repository line: "* git d:\hpe\dev\roms\gnext"
					const isCurrent = trimmed.startsWith('*');
					const cleaned = trimmed.replace(/^\*\s*/, '').trim();
					const parts = cleaned.split(/\s+/);
					if (parts.length >= 2) {
						const vcs = parts[0];
						const path = parts.slice(1).join(' ').toLowerCase();
						const name = path.split(/[\\/]/).filter(p => p).pop() || path;
						items.push({
							label: name + (isCurrent ? ' ★' : ''),
							description: `${vcs.toUpperCase()}: ${path}`,
							path: path,
							isCurrent: isCurrent
						});
					}
				}
				
				if (items.length === 0) {
					vscode.window.showInformationMessage('No repos to choose from');
					return;
				}
				
				if (items.length === 1) {
					vscode.window.showInformationMessage('Only one repo');
					return;
				}
				
				// Sort: current items first
				items.sort((a, b) => {
					if (a.isCurrent && !b.isCurrent) {
						return -1;
					}
					if (!a.isCurrent && b.isCurrent) {
						return 1;
					}
					return a.label.localeCompare(b.label);
				});
				
				const selected = await vscode.window.showQuickPick(items, {
					placeHolder: 'Choose repository to select'
				});
				
				if (selected) {
					// Run bt select with the chosen repository path
					await btRunner.runCommand('select', [selected.path]);
					platformProvider.refresh();
					statusBar.updatePlatform();
				}
			} catch (err) {
				vscode.window.showErrorMessage(`Failed to select repository: ${err}`);
			}
		}),
		
		vscode.commands.registerCommand('BIOSTool.move', async () => {
			const newPath = await vscode.window.showInputBox({
				prompt: 'Enter new path for worktree',
				placeHolder: 'Path to new location'
			});
			if (newPath) {
				await btRunner.runInTerminal('move', [newPath]);
			}
		}),
		
		vscode.commands.registerCommand('BIOSTool.top', async () => {
			await btRunner.runInTerminal('top');
		}),
		
		vscode.commands.registerCommand('BIOSTool.selectPlatform', async (platform: Platform) => {
			if (platform) {
				await btRunner.runCommand('switch', [platform.name]);
				platformProvider.refresh();
				statusBar.updatePlatform();
			}
		}),
		
		treeView,
		btRunner,
		statusBar
	);
}

// This method is called when your extension is deactivated
export function deactivate() {}

