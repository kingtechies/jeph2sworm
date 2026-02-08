/**
 * TestDashboard — webview panel showing test execution results.
 */

import * as vscode from 'vscode';

interface TestResult {
  name: string;
  suite: string;
  status: 'passed' | 'failed' | 'skipped';
  duration: number;
  error?: string;
}

export class TestDashboardPanel {
  private static panel?: vscode.WebviewPanel;
  private static results: TestResult[] = [];

  static show(extensionUri: vscode.Uri): void {
    if (this.panel) {
      this.panel.reveal();
      return;
    }
    this.panel = vscode.window.createWebviewPanel(
      'jeph2sworm.testDashboard',
      'Test Dashboard',
      vscode.ViewColumn.Two,
      { enableScripts: true, localResourceRoots: [extensionUri] }
    );
    this.panel.onDidDispose(() => (this.panel = undefined));
    this.render();
  }

  static setResults(results: TestResult[]): void {
    this.results = results;
    this.render();
  }

  private static render(): void {
    if (!this.panel) { return; }
    const passed = this.results.filter((r) => r.status === 'passed').length;
    const failed = this.results.filter((r) => r.status === 'failed').length;
    const skipped = this.results.filter((r) => r.status === 'skipped').length;

    const rows = this.results
      .map(
        (r) =>
          `<tr class="${r.status}">
            <td>${r.suite}</td><td>${r.name}</td>
            <td>${r.status}</td><td>${r.duration}ms</td>
            <td>${r.error ?? ''}</td>
          </tr>`
      )
      .join('\n');

    this.panel.webview.html = `<!DOCTYPE html>
<html><head><style>
  body { font-family: var(--vscode-font-family); padding: 12px; }
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 4px 8px; border-bottom: 1px solid var(--vscode-panel-border); }
  .passed td:nth-child(3) { color: #4ec9b0; }
  .failed td:nth-child(3) { color: #f44747; }
  .skipped td:nth-child(3) { color: #ccc; }
  .summary { margin-bottom: 12px; }
  .summary span { margin-right: 16px; }
</style></head><body>
<h2>Test Dashboard</h2>
<div class="summary">
  <span>✅ ${passed} passed</span>
  <span>❌ ${failed} failed</span>
  <span>⏭ ${skipped} skipped</span>
</div>
<table><thead><tr><th>Suite</th><th>Test</th><th>Status</th><th>Duration</th><th>Error</th></tr></thead>
<tbody>${rows}</tbody></table>
</body></html>`;
  }
}
