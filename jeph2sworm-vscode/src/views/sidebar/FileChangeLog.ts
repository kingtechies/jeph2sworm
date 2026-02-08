/**
 * FileChangeLog — sidebar tree view showing files modified by the swarm.
 */

import * as vscode from 'vscode';

interface FileChange {
  filePath: string;
  agent: string;
  action: 'created' | 'modified' | 'deleted';
  timestamp: number;
}

class FileChangeItem extends vscode.TreeItem {
  constructor(public readonly change: FileChange) {
    super(change.filePath, vscode.TreeItemCollapsibleState.None);
    const icons: Record<string, string> = { created: 'new-file', modified: 'edit', deleted: 'trash' };
    this.iconPath = new vscode.ThemeIcon(icons[change.action] ?? 'file');
    this.description = `${change.agent} · ${change.action}`;
    this.tooltip = `${change.action} by ${change.agent} at ${new Date(change.timestamp).toLocaleTimeString()}`;
    this.command = {
      command: 'vscode.open',
      title: 'Open File',
      arguments: [vscode.Uri.file(change.filePath)],
    };
  }

  contextValue = 'fileChange';
}

export class FileChangeLogProvider implements vscode.TreeDataProvider<FileChangeItem> {
  private changes: FileChange[] = [];
  private _onDidChangeTreeData = new vscode.EventEmitter<void>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  getTreeItem(element: FileChangeItem): vscode.TreeItem {
    return element;
  }

  getChildren(): FileChangeItem[] {
    return this.changes
      .sort((a, b) => b.timestamp - a.timestamp)
      .map((c) => new FileChangeItem(c));
  }

  addChange(change: FileChange): void {
    this.changes.push(change);
    this._onDidChangeTreeData.fire();
  }

  clear(): void {
    this.changes = [];
    this._onDidChangeTreeData.fire();
  }
}
