/**
 * SetupWizard — webview panel for initial project setup / onboarding.
 */

import * as vscode from 'vscode';

export class SetupWizardPanel {
  private static panel?: vscode.WebviewPanel;

  static show(extensionUri: vscode.Uri): void {
    if (this.panel) {
      this.panel.reveal();
      return;
    }
    this.panel = vscode.window.createWebviewPanel(
      'jeph2sworm.setupWizard',
      'Jeph2Sworm Setup',
      vscode.ViewColumn.One,
      { enableScripts: true, localResourceRoots: [extensionUri] }
    );
    this.panel.onDidDispose(() => (this.panel = undefined));
    this.panel.webview.onDidReceiveMessage(async (msg) => {
      switch (msg.command) {
        case 'selectFolder':
          const uris = await vscode.window.showOpenDialog({ canSelectFolders: true, canSelectMany: false });
          if (uris?.[0]) {
            this.panel?.webview.postMessage({ command: 'folderSelected', path: uris[0].fsPath });
          }
          break;
        case 'startProject':
          await vscode.commands.executeCommand('jeph2sworm.startProject', msg.config);
          this.panel?.dispose();
          break;
      }
    });
    this.render();
  }

  private static render(): void {
    if (!this.panel) { return; }
    this.panel.webview.html = `<!DOCTYPE html>
<html><head><style>
  body { font-family: var(--vscode-font-family); padding: 24px; max-width: 640px; margin: 0 auto; }
  h1 { color: var(--vscode-textLink-foreground); }
  .step { margin: 20px 0; padding: 16px; border: 1px solid var(--vscode-panel-border); border-radius: 6px; }
  label { display: block; margin: 8px 0 4px; font-weight: bold; }
  input, select, textarea { width: 100%; padding: 6px; box-sizing: border-box; background: var(--vscode-input-background); color: var(--vscode-input-foreground); border: 1px solid var(--vscode-input-border); border-radius: 3px; }
  button { background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; padding: 8px 20px; cursor: pointer; border-radius: 3px; margin-top: 12px; }
  button:hover { background: var(--vscode-button-hoverBackground); }
</style></head><body>
<h1>🐝 Jeph2Sworm Setup Wizard</h1>
<div class="step">
  <h3>Step 1 — Project Info</h3>
  <label>Project Name</label>
  <input id="name" placeholder="my-awesome-project" />
  <label>Description</label>
  <textarea id="desc" rows="3" placeholder="What should the swarm build?"></textarea>
</div>
<div class="step">
  <h3>Step 2 — Tech Stack</h3>
  <label>Frontend</label>
  <select id="frontend">
    <option>React</option><option>Vue</option><option>Svelte</option><option>Next.js</option><option>None</option>
  </select>
  <label>Backend</label>
  <select id="backend">
    <option>FastAPI</option><option>Express</option><option>Django</option><option>Flask</option><option>None</option>
  </select>
  <label>Database</label>
  <select id="db">
    <option>PostgreSQL</option><option>MongoDB</option><option>SQLite</option><option>None</option>
  </select>
</div>
<div class="step">
  <h3>Step 3 — LLM Providers</h3>
  <label>Primary Provider</label>
  <select id="llm">
    <option>openai</option><option>anthropic</option><option>gemini</option><option>grok</option>
    <option>deepseek</option><option>mistral</option><option>llama</option><option>cohere</option>
  </select>
  <label>API Key</label>
  <input id="apikey" type="password" placeholder="sk-..." />
</div>
<div class="step">
  <h3>Step 4 — Workspace</h3>
  <button onclick="selectFolder()">Select Project Folder</button>
  <p id="folder" style="margin-top:8px;color:var(--vscode-descriptionForeground);">No folder selected</p>
</div>
<button onclick="start()" style="font-size:16px;padding:12px 32px;">🚀 Start Swarm</button>
<script>
  const vscode = acquireVsCodeApi();
  let folderPath = '';
  window.addEventListener('message', (e) => {
    if (e.data.command === 'folderSelected') {
      folderPath = e.data.path;
      document.getElementById('folder').textContent = folderPath;
    }
  });
  function selectFolder() { vscode.postMessage({ command: 'selectFolder' }); }
  function start() {
    vscode.postMessage({
      command: 'startProject',
      config: {
        name: document.getElementById('name').value,
        description: document.getElementById('desc').value,
        frontend: document.getElementById('frontend').value,
        backend: document.getElementById('backend').value,
        database: document.getElementById('db').value,
        llmProvider: document.getElementById('llm').value,
        apiKey: document.getElementById('apikey').value,
        folder: folderPath,
      },
    });
  }
</script>
</body></html>`;
  }
}
