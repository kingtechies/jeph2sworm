/**
 * Jeph2Sworm VS Code Extension - Main entry point.
 *
 * Activates the sidebar, connects to the Python backend via WebSocket,
 * and provides commands for managing the AI swarm.
 */

import * as vscode from "vscode";
import { SwarmClient } from "./client";
import { ChatViewProvider } from "./views/chat-view";
import { AgentsTreeProvider } from "./views/agents-tree";
import { TasksTreeProvider } from "./views/tasks-tree";

let client: SwarmClient;

export function activate(context: vscode.ExtensionContext) {
  const config = vscode.workspace.getConfiguration("jeph2sworm");
  const host = config.get<string>("serverHost", "127.0.0.1");
  const port = config.get<number>("serverPort", 7777);

  // Create WebSocket client
  client = new SwarmClient(host, port);

  // Register views
  const chatProvider = new ChatViewProvider(context.extensionUri, client);
  const agentsProvider = new AgentsTreeProvider(client);
  const tasksProvider = new TasksTreeProvider(client);

  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider("jeph2sworm.chatView", chatProvider),
    vscode.window.registerTreeDataProvider("jeph2sworm.agentsView", agentsProvider),
    vscode.window.registerTreeDataProvider("jeph2sworm.tasksView", tasksProvider)
  );

  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand("jeph2sworm.startSwarm", async () => {
      await startSwarm(host, port);
    }),

    vscode.commands.registerCommand("jeph2sworm.stopSwarm", async () => {
      await client.disconnect();
      vscode.window.showInformationMessage("Jeph2Sworm: Swarm stopped");
    }),

    vscode.commands.registerCommand("jeph2sworm.newProject", async () => {
      const name = await vscode.window.showInputBox({
        prompt: "Project name",
        placeHolder: "my-awesome-app",
      });
      if (name) {
        const desc = await vscode.window.showInputBox({
          prompt: "Describe your project in one sentence",
          placeHolder: "A SaaS platform for...",
        });
        if (desc) {
          await client.sendMessage(
            `Create a new project called "${name}": ${desc}`
          );
        }
      }
    }),

    vscode.commands.registerCommand("jeph2sworm.configureProvider", async () => {
      const provider = await vscode.window.showQuickPick(
        ["openai", "anthropic", "xai", "google", "deepseek", "mistral", "together", "cohere"],
        { placeHolder: "Select LLM provider" }
      );
      if (provider) {
        const apiKey = await vscode.window.showInputBox({
          prompt: `Enter API key for ${provider}`,
          password: true,
        });
        if (apiKey) {
          await client.configureProvider(provider, apiKey);
          vscode.window.showInformationMessage(
            `Jeph2Sworm: ${provider} configured`
          );
        }
      }
    }),

    vscode.commands.registerCommand("jeph2sworm.showStatus", async () => {
      const status = await client.getStatus();
      const channel = vscode.window.createOutputChannel("Jeph2Sworm Status");
      channel.appendLine(JSON.stringify(status, null, 2));
      channel.show();
    })
  );

  // Listen for events from backend
  client.onEvent((event) => {
    agentsProvider.refresh();
    tasksProvider.refresh();
    chatProvider.onEvent(event);
  });

  // Auto-connect if configured
  if (config.get<boolean>("autoStart", false)) {
    startSwarm(host, port);
  }
}

async function startSwarm(host: string, port: number): Promise<void> {
  try {
    await client.connect();
    vscode.window.showInformationMessage("Jeph2Sworm: Connected to swarm");
  } catch (err) {
    vscode.window.showErrorMessage(
      `Jeph2Sworm: Failed to connect to ${host}:${port}. Is the backend running?`
    );
  }
}

export function deactivate() {
  client?.disconnect();
}
