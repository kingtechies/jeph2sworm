/**
 * Event Feed View - Displays real-time swarm events in a webview panel.
 */

import * as vscode from 'vscode';
import { SwarmEvent } from '../types/event.types';

export class EventFeedProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = 'jeph2sworm.eventFeed';
  private view?: vscode.WebviewView;
  private events: SwarmEvent[] = [];
  private maxEvents = 200;

  constructor(private readonly extensionUri: vscode.Uri) {}

  resolveWebviewView(webviewView: vscode.WebviewView): void {
    this.view = webviewView;

    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this.extensionUri],
    };

    webviewView.webview.html = this.getHtml();
  }

  addEvent(event: SwarmEvent): void {
    this.events.push(event);
    if (this.events.length > this.maxEvents) {
      this.events = this.events.slice(-this.maxEvents);
    }
    if (this.view) {
      this.view.webview.postMessage({ type: 'event', event });
    }
  }

  private getHtml(): string {
    return `<!DOCTYPE html>
<html>
<head>
<style>
  body { font: 12px var(--vscode-font-family); color: var(--vscode-foreground); padding: 0; margin: 0; }
  .event { padding: 4px 8px; border-bottom: 1px solid var(--vscode-panel-border); display: flex; gap: 6px; }
  .event:hover { background: var(--vscode-list-hoverBackground); }
  .time { color: var(--vscode-descriptionForeground); min-width: 60px; font-size: 10px; }
  .agent { font-weight: bold; min-width: 60px; }
  .agent.pm { color: #4fc1ff; }
  .agent.brain { color: #c586c0; }
  .agent.backend { color: #dcdcaa; }
  .agent.frontend { color: #9cdcfe; }
  .agent.ux { color: #ce9178; }
  .agent.tester { color: #4ec9b0; }
  .agent.devops { color: #d7ba7d; }
  .type { color: var(--vscode-descriptionForeground); font-size: 10px; }
  .data { color: var(--vscode-foreground); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  #feed { overflow-y: auto; height: 100vh; }
  .empty { text-align: center; padding: 20px; color: var(--vscode-descriptionForeground); }
</style>
</head>
<body>
  <div id="feed"><div class="empty">Waiting for events...</div></div>
  <script>
    const feed = document.getElementById('feed');
    let hasEvents = false;

    window.addEventListener('message', e => {
      if (e.data.type === 'event') {
        if (!hasEvents) { feed.innerHTML = ''; hasEvents = true; }
        const ev = e.data.event;
        const div = document.createElement('div');
        div.className = 'event';
        const time = new Date(ev.timestamp * 1000).toLocaleTimeString();
        const dataStr = typeof ev.data === 'object' ? JSON.stringify(ev.data).substring(0, 200) : String(ev.data);
        div.innerHTML = '<span class="time">' + time + '</span>'
          + '<span class="agent ' + ev.agent + '">' + ev.agent + '</span>'
          + '<span class="type">' + ev.type + '</span>'
          + '<span class="data">' + dataStr + '</span>';
        feed.appendChild(div);
        feed.scrollTop = feed.scrollHeight;
      }
    });
  </script>
</body>
</html>`;
  }
}
