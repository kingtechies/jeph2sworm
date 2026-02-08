/**
 * Git Service - Git operations integration for the VS Code extension.
 */

import * as vscode from 'vscode';

export class GitService {
  private workspaceRoot: string;

  constructor(workspaceRoot: string) {
    this.workspaceRoot = workspaceRoot;
  }

  async getStatus(): Promise<{ staged: string[]; modified: string[]; untracked: string[] }> {
    try {
      const gitExt = vscode.extensions.getExtension('vscode.git');
      if (!gitExt) {
        return { staged: [], modified: [], untracked: [] };
      }

      const git = gitExt.exports.getAPI(1);
      const repo = git.repositories[0];
      if (!repo) {
        return { staged: [], modified: [], untracked: [] };
      }

      const state = repo.state;
      return {
        staged: state.indexChanges.map((c: any) => c.uri.fsPath),
        modified: state.workingTreeChanges.map((c: any) => c.uri.fsPath),
        untracked: state.workingTreeChanges
          .filter((c: any) => c.status === 7) // Untracked
          .map((c: any) => c.uri.fsPath),
      };
    } catch {
      return { staged: [], modified: [], untracked: [] };
    }
  }

  async getCurrentBranch(): Promise<string> {
    try {
      const gitExt = vscode.extensions.getExtension('vscode.git');
      if (!gitExt) { return 'unknown'; }
      const git = gitExt.exports.getAPI(1);
      const repo = git.repositories[0];
      return repo?.state?.HEAD?.name || 'unknown';
    } catch {
      return 'unknown';
    }
  }

  async getRecentCommits(count = 10): Promise<{ hash: string; message: string; date: string }[]> {
    try {
      const gitExt = vscode.extensions.getExtension('vscode.git');
      if (!gitExt) { return []; }
      const git = gitExt.exports.getAPI(1);
      const repo = git.repositories[0];
      if (!repo) { return []; }

      const log = await repo.log({ maxEntries: count });
      return log.map((entry: any) => ({
        hash: entry.hash.substring(0, 8),
        message: entry.message,
        date: entry.authorDate?.toISOString() || '',
      }));
    } catch {
      return [];
    }
  }
}
