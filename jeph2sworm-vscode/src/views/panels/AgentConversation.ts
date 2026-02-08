/**
 * AgentConversation — webview panel showing inter-agent conversations.
 */

import * as vscode from 'vscode';

interface Message {
  from: string;
  to: string;
  content: string;
  timestamp: number;
}

export class AgentConversationPanel {
  private static panel?: vscode.WebviewPanel;
  private static messages: Message[] = [];

  static show(extensionUri: vscode.Uri): void {
    if (this.panel) {
      this.panel.reveal();
      return;
    }
    this.panel = vscode.window.createWebviewPanel(
      'jeph2sworm.agentConversation',
      'Agent Conversations',
      vscode.ViewColumn.Two,
      { enableScripts: true, localResourceRoots: [extensionUri] }
    );
    this.panel.onDidDispose(() => (this.panel = undefined));
    this.render();
  }

  static addMessage(msg: Message): void {
    this.messages.push(msg);
    this.render();
  }

  private static render(): void {
    if (!this.panel) { return; }
    const rows = this.messages
      .map(
        (m) =>
          `<div class="msg"><span class="from">${m.from}</span> → <span class="to">${m.to}</span>: ${m.content}</div>`
      )
      .join('\n');

    this.panel.webview.html = `<!DOCTYPE html>
<html><head><style>
  body { font-family: var(--vscode-font-family); padding: 12px; }
  .msg { padding: 6px 0; border-bottom: 1px solid var(--vscode-panel-border); }
  .from { font-weight: bold; color: var(--vscode-textLink-foreground); }
  .to { color: var(--vscode-descriptionForeground); }
</style></head><body>
<h2>Agent Conversations</h2>
${rows || '<p>No messages yet.</p>'}
</body></html>`;
  }
}
