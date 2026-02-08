/**
 * File Manager — VS Code workspace file operations with backup support.
 */

import * as vscode from 'vscode';
import * as path from 'path';
import { BackupService } from '../services/backup-service';
import { RulesEngine } from './rules-engine';

export class FileManager {
  private backupService: BackupService;
  private rulesEngine: RulesEngine;

  constructor(workspaceRoot: string) {
    this.backupService = new BackupService(workspaceRoot);
    this.rulesEngine = new RulesEngine(workspaceRoot);
  }

  async readFile(filePath: string): Promise<string> {
    const check = this.rulesEngine.validateFilePath(filePath);
    if (!check.valid) { throw new Error(check.reason); }
    const uri = vscode.Uri.file(filePath);
    const content = await vscode.workspace.fs.readFile(uri);
    return Buffer.from(content).toString('utf-8');
  }

  async writeFile(filePath: string, content: string): Promise<void> {
    const check = this.rulesEngine.validateFilePath(filePath);
    if (!check.valid) { throw new Error(check.reason); }

    const uri = vscode.Uri.file(filePath);
    // Backup before overwrite
    try {
      await vscode.workspace.fs.stat(uri);
      await this.backupService.backupFile(filePath);
    } catch {
      // File doesn't exist yet — no backup needed
    }

    const dir = vscode.Uri.file(path.dirname(filePath));
    await vscode.workspace.fs.createDirectory(dir);
    await vscode.workspace.fs.writeFile(uri, Buffer.from(content, 'utf-8'));
  }

  async listFiles(dirPath: string, recursive = false): Promise<string[]> {
    const check = this.rulesEngine.validateFilePath(dirPath);
    if (!check.valid) { throw new Error(check.reason); }

    const uri = vscode.Uri.file(dirPath);
    const entries = await vscode.workspace.fs.readDirectory(uri);
    const results: string[] = [];

    for (const [name, type] of entries) {
      const fullPath = path.join(dirPath, name);
      if (type === vscode.FileType.File) {
        results.push(fullPath);
      } else if (type === vscode.FileType.Directory && recursive) {
        results.push(...(await this.listFiles(fullPath, true)));
      }
    }
    return results;
  }

  async fileExists(filePath: string): Promise<boolean> {
    try {
      await vscode.workspace.fs.stat(vscode.Uri.file(filePath));
      return true;
    } catch {
      return false;
    }
  }

  async restoreBackup(filePath: string): Promise<boolean> {
    return this.backupService.restoreFile(filePath);
  }
}
