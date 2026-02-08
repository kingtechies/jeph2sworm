/**
 * AiEnvViewer — webview panel showing AI-managed environment variables.
 */

import * as vscode from 'vscode';

interface EnvVar {
  key: string;
  maskedValue: string;
  provider: string;
  rotatedAt: string;
}

export class AiEnvViewerPanel {
  private static panel?: vscode.WebviewPanel;
  private static vars: EnvVar[] = [];

  static show(extensionUri: vscode.Uri): void {
    if (this.panel) {
      this.panel.reveal();
      return;
    }
    this.panel = vscode.window.createWebviewPanel(
      'jeph2sworm.aiEnvViewer',
      'AI Environment Variables',
      vscode.ViewColumn.Two,
      { enableScripts: true, localResourceRoots: [extensionUri] }
    );
    this.panel.onDidDispose(() => (this.panel = undefined));
    this.panel.webview.onDidReceiveMessage((msg) => {
      if (msg.command === 'rotate') {
        vscode.commands.executeCommand('jeph2sworm.rotateEnvVar', msg.key);
      }
    });
    this.render();
  }

  static setVars(vars: EnvVar[]): void {
    this.vars = vars;
    this.render();
  }

  private static render(): void {
    if (!this.panel) { return; }
    const rows = this.vars
      .map(
        (v) =>
          `<tr>
            <td>${v.key}</td><td>${v.maskedValue}</td>
            <td>${v.provider}</td><td>${v.rotatedAt}</td>
            <td><button onclick="rotate('${v.key}')">Rotate</button></td>
          </tr>`
      )
      .join('\n');

    this.panel.webview.html = `<!DOCTYPE html>
<html><head><style>
  body { font-family: var(--vscode-font-family); padding: 12px; }
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 4px 8px; border-bottom: 1px solid var(--vscode-panel-border); }
  button { background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; padding: 2px 10px; cursor: pointer; border-radius: 2px; }
</style></head><body>
<h2>AI Environment Variables</h2>
<table><thead><tr><th>Key</th><th>Value</th><th>Provider</th><th>Last Rotated</th><th></th></tr></thead>
<tbody>${rows}</tbody></table>
<script>
  const vscode = acquireVsCodeApi();
  function rotate(key) { vscode.postMessage({ command: 'rotate', key }); }
</script>
</body></html>`;
  }
}
