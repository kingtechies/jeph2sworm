/**
 * BrainViewer — webview panel for exploring the Brain's memory, context and decision log.
 */

import * as vscode from 'vscode';

interface MemoryEntry {
  id: string;
  type: 'context' | 'decision' | 'knowledge';
  summary: string;
  timestamp: number;
  relevance: number;
}

export class BrainViewerPanel {
  private static panel?: vscode.WebviewPanel;
  private static entries: MemoryEntry[] = [];
  private static filter: MemoryEntry['type'] | 'all' = 'all';

  static show(extensionUri: vscode.Uri): void {
    if (this.panel) {
      this.panel.reveal();
      return;
    }
    this.panel = vscode.window.createWebviewPanel(
      'jeph2sworm.brainViewer',
      'Brain Viewer',
      vscode.ViewColumn.Two,
      { enableScripts: true, localResourceRoots: [extensionUri] }
    );
    this.panel.onDidDispose(() => (this.panel = undefined));
    this.panel.webview.onDidReceiveMessage((msg) => {
      if (msg.command === 'setFilter') {
        this.filter = msg.value;
        this.render();
      }
    });
    this.render();
  }

  static setEntries(entries: MemoryEntry[]): void {
    this.entries = entries;
    this.render();
  }

  private static render(): void {
    if (!this.panel) { return; }
    const filtered =
      this.filter === 'all' ? this.entries : this.entries.filter((e) => e.type === this.filter);

    const rows = filtered
      .sort((a, b) => b.relevance - a.relevance)
      .map(
        (e) =>
          `<tr>
            <td><span class="badge ${e.type}">${e.type}</span></td>
            <td>${e.summary}</td>
            <td>${(e.relevance * 100).toFixed(0)}%</td>
            <td>${new Date(e.timestamp).toLocaleString()}</td>
          </tr>`
      )
      .join('\n');

    this.panel.webview.html = `<!DOCTYPE html>
<html><head><style>
  body { font-family: var(--vscode-font-family); padding: 12px; }
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 4px 8px; border-bottom: 1px solid var(--vscode-panel-border); }
  .filters button { margin-right: 8px; background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground); border: none; padding: 4px 12px; cursor: pointer; border-radius: 2px; }
  .badge { padding: 2px 6px; border-radius: 3px; font-size: 11px; }
  .context { background: #264f78; } .decision { background: #4e3a18; } .knowledge { background: #1e4620; }
</style></head><body>
<h2>Brain Viewer</h2>
<div class="filters">
  <button onclick="setFilter('all')">All</button>
  <button onclick="setFilter('context')">Context</button>
  <button onclick="setFilter('decision')">Decisions</button>
  <button onclick="setFilter('knowledge')">Knowledge</button>
</div>
<table><thead><tr><th>Type</th><th>Summary</th><th>Relevance</th><th>Time</th></tr></thead>
<tbody>${rows}</tbody></table>
<script>
  const vscode = acquireVsCodeApi();
  function setFilter(v) { vscode.postMessage({ command: 'setFilter', value: v }); }
</script>
</body></html>`;
  }
}
