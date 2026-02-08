/**
 * DeployStatus — webview panel showing deployment status and logs.
 */

import * as vscode from 'vscode';

interface DeployEntry {
  environment: string;
  status: 'pending' | 'building' | 'deploying' | 'success' | 'failed';
  version: string;
  timestamp: number;
  logs: string[];
}

export class DeployStatusPanel {
  private static panel?: vscode.WebviewPanel;
  private static entries: DeployEntry[] = [];

  static show(extensionUri: vscode.Uri): void {
    if (this.panel) {
      this.panel.reveal();
      return;
    }
    this.panel = vscode.window.createWebviewPanel(
      'jeph2sworm.deployStatus',
      'Deploy Status',
      vscode.ViewColumn.Two,
      { enableScripts: true, localResourceRoots: [extensionUri] }
    );
    this.panel.onDidDispose(() => (this.panel = undefined));
    this.render();
  }

  static update(entry: DeployEntry): void {
    const idx = this.entries.findIndex((e) => e.environment === entry.environment);
    if (idx >= 0) {
      this.entries[idx] = entry;
    } else {
      this.entries.push(entry);
    }
    this.render();
  }

  private static render(): void {
    if (!this.panel) { return; }
    const statusColor: Record<string, string> = {
      pending: '#ccc',
      building: '#dcdcaa',
      deploying: '#569cd6',
      success: '#4ec9b0',
      failed: '#f44747',
    };

    const cards = this.entries
      .map(
        (e) => `
        <div class="card">
          <h3>${e.environment} <span style="color:${statusColor[e.status]}">[${e.status}]</span></h3>
          <p>Version: ${e.version} · ${new Date(e.timestamp).toLocaleString()}</p>
          <pre>${e.logs.slice(-20).join('\n')}</pre>
        </div>`
      )
      .join('\n');

    this.panel.webview.html = `<!DOCTYPE html>
<html><head><style>
  body { font-family: var(--vscode-font-family); padding: 12px; }
  .card { border: 1px solid var(--vscode-panel-border); border-radius: 4px; padding: 12px; margin-bottom: 12px; }
  pre { max-height: 200px; overflow-y: auto; font-size: 12px; background: var(--vscode-editor-background); padding: 8px; }
</style></head><body>
<h2>Deploy Status</h2>
${cards || '<p>No deployments yet.</p>'}
</body></html>`;
  }
}
