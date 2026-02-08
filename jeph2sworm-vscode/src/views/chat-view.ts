/**
 * Chat webview - the main user interaction panel in the sidebar.
 *
 * Serves the React webview-ui build (built via Vite) which provides
 * the tabbed Chat / Agents / Progress UI.
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
      localResourceRoots: [
        vscode.Uri.joinPath(this.extensionUri, "dist", "webview"),
      ],
    };

    webviewView.webview.html = this.getHtml(webviewView.webview);

    // Handle messages from the React webview
    webviewView.webview.onDidReceiveMessage(async (msg) => {
      switch (msg.type) {
        case "chat":
          // React ChatPanel sends { type: 'chat', message }
          await this.client.sendMessage(msg.message);
          break;
        case "sendMessage":
          // Legacy inline message format
          await this.client.sendMessage(msg.text);
          break;
        case "requestStatus":
          try {
            const status = await this.client.getStatus();
            webviewView.webview.postMessage({
              type: "statusUpdate",
              status,
            });
          } catch { /* ignore */ }
          break;
      }
    });
  }

  onEvent(event: SwarmEvent): void {
    if (!this.view) { return; }

    const eventType = event.type || event.event_type || "";
    const data = event.data || {};

    // Forward as agent_message for ChatPanel React component
    if (eventType === "agent_message" && data.message) {
      this.view.webview.postMessage({
        type: "agent_message",
        agent: event.source || "system",
        content: data.message as string,
      });
    } else {
      // Forward all other events with a generic format
      this.view.webview.postMessage({
        type: "chat_response",
        agent: event.source || "system",
        content: `[${eventType}] ${(data.message as string) || JSON.stringify(data).substring(0, 200)}`,
      });
    }

    // Forward status updates for the agents/progress tabs
    if (eventType === "status_update" || eventType === "initial_state") {
      this.view.webview.postMessage({
        type: "statusUpdate",
        status: data,
      });
    }
  }

  /**
   * Generates the HTML that loads the Vite-built React app.
   * Falls back to an inline UI if the build output isn't found.
   */
  private getHtml(webview: vscode.Webview): string {
    const scriptUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this.extensionUri, "dist", "webview", "assets", "index.js")
    );
    const cssUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this.extensionUri, "dist", "webview", "assets", "index.css")
    );

    const nonce = getNonce();

    return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta http-equiv="Content-Security-Policy"
    content="default-src 'none';
      style-src ${webview.cspSource} 'unsafe-inline';
      script-src 'nonce-${nonce}';
      font-src ${webview.cspSource};" />
  <link href="${cssUri}" rel="stylesheet" />
  <style>
    html, body, #root { height: 100%; margin: 0; padding: 0; overflow: hidden; }
  </style>
</head>
<body>
  <div id="root"></div>
  <script nonce="${nonce}" type="module" src="${scriptUri}"></script>
</body>
</html>`;
  }
}

function getNonce(): string {
  let text = "";
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  for (let i = 0; i < 32; i++) {
    text += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return text;
}
