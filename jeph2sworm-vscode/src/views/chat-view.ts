/**
 * Chat webview - the main user interaction panel in the sidebar.
 */

import * as vscode from "vscode";
import { SwarmClient, SwarmEvent } from "../client";

export class ChatViewProvider implements vscode.WebviewViewProvider {
  private view?: vscode.WebviewView;
  private client: SwarmClient;

  constructor(
    private readonly extensionUri: vscode.Uri,
    client: SwarmClient
  ) {
    this.client = client;
  }

  resolveWebviewView(
    webviewView: vscode.WebviewView,
    _context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken
  ): void {
    this.view = webviewView;

    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this.extensionUri],
    };

    webviewView.webview.html = this.getHtml();

    // Handle messages from the webview
    webviewView.webview.onDidReceiveMessage(async (msg) => {
      if (msg.type === "sendMessage") {
        await this.client.sendMessage(msg.text);
      }
    });
  }

  onEvent(event: SwarmEvent): void {
    if (this.view) {
      this.view.webview.postMessage({
        type: "swarmEvent",
        event,
      });
    }
  }

  private getHtml(): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: var(--vscode-font-family);
      font-size: var(--vscode-font-size);
      color: var(--vscode-foreground);
      background: var(--vscode-sideBar-background);
      display: flex;
      flex-direction: column;
      height: 100vh;
    }
    #messages {
      flex: 1;
      overflow-y: auto;
      padding: 8px;
    }
    .message {
      margin-bottom: 12px;
      padding: 8px 12px;
      border-radius: 6px;
      line-height: 1.4;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
    .message.user {
      background: var(--vscode-input-background);
      border: 1px solid var(--vscode-input-border);
    }
    .message.agent {
      background: var(--vscode-editor-background);
      border-left: 3px solid var(--vscode-activityBarBadge-background);
    }
    .message .source {
      font-size: 0.8em;
      color: var(--vscode-descriptionForeground);
      margin-bottom: 4px;
    }
    .event {
      font-size: 0.85em;
      color: var(--vscode-descriptionForeground);
      padding: 4px 8px;
      margin-bottom: 4px;
    }
    .event .type {
      color: var(--vscode-activityBarBadge-background);
      font-weight: 600;
    }
    #input-area {
      padding: 8px;
      border-top: 1px solid var(--vscode-panel-border);
      display: flex;
      gap: 4px;
    }
    #input {
      flex: 1;
      padding: 6px 10px;
      border-radius: 4px;
      border: 1px solid var(--vscode-input-border);
      background: var(--vscode-input-background);
      color: var(--vscode-input-foreground);
      font-family: var(--vscode-font-family);
      font-size: var(--vscode-font-size);
      resize: none;
    }
    #input:focus { outline: 1px solid var(--vscode-focusBorder); }
    button {
      padding: 6px 14px;
      border-radius: 4px;
      border: none;
      background: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      cursor: pointer;
      font-size: var(--vscode-font-size);
    }
    button:hover { background: var(--vscode-button-hoverBackground); }
    .status-bar {
      padding: 4px 8px;
      font-size: 0.8em;
      color: var(--vscode-descriptionForeground);
      border-bottom: 1px solid var(--vscode-panel-border);
      display: flex;
      justify-content: space-between;
    }
    .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; }
    .dot.connected { background: #4caf50; }
    .dot.disconnected { background: #f44336; }
  </style>
</head>
<body>
  <div class="status-bar">
    <span><span class="dot disconnected" id="status-dot"></span><span id="status-text">Disconnected</span></span>
    <span id="agent-count">0 agents</span>
  </div>
  <div id="messages"></div>
  <div id="input-area">
    <textarea id="input" rows="2" placeholder="Describe your project or ask a question..."></textarea>
    <button id="send">Send</button>
  </div>

  <script>
    const vscode = acquireVsCodeApi();
    const messages = document.getElementById("messages");
    const input = document.getElementById("input");
    const sendBtn = document.getElementById("send");
    const statusDot = document.getElementById("status-dot");
    const statusText = document.getElementById("status-text");

    function addMessage(role, text, source) {
      const div = document.createElement("div");
      div.className = "message " + role;
      if (source) {
        const srcDiv = document.createElement("div");
        srcDiv.className = "source";
        srcDiv.textContent = source;
        div.appendChild(srcDiv);
      }
      const content = document.createElement("div");
      content.textContent = text;
      div.appendChild(content);
      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;
    }

    function escapeHtml(str) {
      const d = document.createElement('div');
      d.textContent = str;
      return d.innerHTML;
    }

    function addEvent(type, source, data) {
      const div = document.createElement("div");
      div.className = "event";
      const typeSpan = document.createElement("span");
      typeSpan.className = "type";
      typeSpan.textContent = "[" + type + "]";
      div.appendChild(typeSpan);
      div.appendChild(document.createTextNode(" " + source + ": " + (data.message || JSON.stringify(data).substring(0, 100))));
      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;
    }

    sendBtn.addEventListener("click", () => {
      const text = input.value.trim();
      if (!text) return;
      addMessage("user", text, "You");
      vscode.postMessage({ type: "sendMessage", text });
      input.value = "";
    });

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendBtn.click();
      }
    });

    window.addEventListener("message", (e) => {
      const msg = e.data;
      if (msg.type === "swarmEvent") {
        const event = msg.event;
        if (event.event_type === "agent_message" && event.data?.message) {
          addMessage("agent", event.data.message, event.source);
        } else {
          addEvent(event.event_type || event.type, event.source || "", event.data || {});
        }

        if (event.type === "initial_state") {
          statusDot.className = "dot connected";
          statusText.textContent = "Connected";
        }
      }
    });
  </script>
</body>
</html>`;
  }
}
