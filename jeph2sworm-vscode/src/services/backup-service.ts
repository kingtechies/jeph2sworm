/**
 * Backup Service - Auto-backup of project files before agent modifications.
 */

import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

export class BackupService {
  private backupDir: string;
  private maxBackups: number;

  constructor(workspaceRoot: string, maxBackups = 100) {
    this.backupDir = path.join(workspaceRoot, '.jeph2sworm', 'backups');
    this.maxBackups = maxBackups;

    if (!fs.existsSync(this.backupDir)) {
      fs.mkdirSync(this.backupDir, { recursive: true });
    }
  }

  backup(filePath: string): string | null {
    if (!fs.existsSync(filePath)) { return null; }

    try {
      const relativePath = path.relative(
        vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '',
        filePath
      );
      const timestamp = Date.now();
      const safeName = relativePath.replace(/[/\\]/g, '_');
      const backupPath = path.join(this.backupDir, `${safeName}_${timestamp}`);

      fs.copyFileSync(filePath, backupPath);
      this.pruneOldBackups();

      return backupPath;
    } catch {
      return null;
    }
  }

  restore(filePath: string): boolean {
    try {
      const relativePath = path.relative(
        vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || '',
        filePath
      );
      const safeName = relativePath.replace(/[/\\]/g, '_');

      const backups = fs.readdirSync(this.backupDir)
        .filter(f => f.startsWith(safeName + '_'))
        .sort()
        .reverse();

      if (backups.length === 0) { return false; }

      const latestBackup = path.join(this.backupDir, backups[0]);
      fs.copyFileSync(latestBackup, filePath);
      return true;
    } catch {
      return false;
    }
  }

  listBackups(): { path: string; size: number; created: number }[] {
    try {
      return fs.readdirSync(this.backupDir)
        .map(f => {
          const fullPath = path.join(this.backupDir, f);
          const stats = fs.statSync(fullPath);
          return { path: fullPath, size: stats.size, created: stats.mtimeMs };
        })
        .sort((a, b) => b.created - a.created);
    } catch {
      return [];
    }
  }

  private pruneOldBackups(): void {
    try {
      const files = fs.readdirSync(this.backupDir)
        .map(f => ({ name: f, time: fs.statSync(path.join(this.backupDir, f)).mtimeMs }))
        .sort((a, b) => a.time - b.time);

      while (files.length > this.maxBackups) {
        const oldest = files.shift();
        if (oldest) {
          fs.unlinkSync(path.join(this.backupDir, oldest.name));
        }
      }
    } catch {
      // ignore prune errors
    }
  }
}
