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
  const port = config.get<number>("serverPort", 8765);

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
          await context.secrets.store(`jeph2sworm.apiKey.${provider}`, apiKey);
          await client.configureProvider(provider, apiKey);
          vscode.window.showInformationMessage(
            `Jeph2Sworm: ${provider} configured`
          );
        }
      }
    }),

    vscode.commands.registerCommand("jeph2sworm.showStatus", async () => {
      try {
        const status = await client.getStatus();
        const channel = vscode.window.createOutputChannel("Jeph2Sworm Status");
        channel.appendLine(JSON.stringify(status, null, 2));
        channel.show();
      } catch (err) {
        vscode.window.showErrorMessage(`Jeph2Sworm: Failed to get status — ${err}`);
      }
    }),

    // ---- Plan Section 4.3: Additional Commands ----

    vscode.commands.registerCommand("jeph2sworm.viewAgentActivity", async () => {
      try {
        const agents = await client.getAgents();
        const channel = vscode.window.createOutputChannel("Jeph2Sworm Agent Activity");
        channel.clear();
        for (const agent of agents) {
          channel.appendLine(
            `[${agent.role}] ${agent.status} — ${agent.current_task || "idle"}`
          );
        }
        channel.show();
      } catch (err) {
        vscode.window.showErrorMessage(`Jeph2Sworm: ${err}`);
      }
    }),

    vscode.commands.registerCommand("jeph2sworm.viewBrainMemory", async () => {
      try {
        const brain = await client.getBrainSummary();
        const doc = await vscode.workspace.openTextDocument({
          content: JSON.stringify(brain, null, 2),
          language: "json",
        });
        await vscode.window.showTextDocument(doc, { preview: true });
      } catch (err) {
        vscode.window.showErrorMessage(`Jeph2Sworm: ${err}`);
      }
    }),

    vscode.commands.registerCommand("jeph2sworm.pauseAgents", async () => {
      client.send({ type: "pause_agents" });
      vscode.window.showInformationMessage("Jeph2Sworm: All agents paused");
    }),

    vscode.commands.registerCommand("jeph2sworm.resumeAgents", async () => {
      client.send({ type: "resume_agents" });
      vscode.window.showInformationMessage("Jeph2Sworm: All agents resumed");
    }),

    vscode.commands.registerCommand("jeph2sworm.viewAiEnv", async () => {
      try {
        const credentials = await client.getCredentials();
        const channel = vscode.window.createOutputChannel("Jeph2Sworm ai.env");
        channel.clear();
        channel.appendLine("# ai.env — Managed by Jeph2Sworm");
        channel.appendLine("# Values are masked. Use 'Reveal Credential' to see full values.\n");
        for (const cred of credentials) {
          const masked = cred.value
            ? cred.value.slice(0, 4) + "****" + cred.value.slice(-4)
            : "****";
          channel.appendLine(`${cred.key_name}=${masked}  # ${cred.purpose}`);
        }
        channel.show();
      } catch (err) {
        vscode.window.showErrorMessage(`Jeph2Sworm: ${err}`);
      }
    }),

    vscode.commands.registerCommand("jeph2sworm.runTests", async () => {
      vscode.window.showInformationMessage("Jeph2Sworm: Starting test suite...");
      client.send({ type: "command", command: "run_tests" });
    }),

    vscode.commands.registerCommand("jeph2sworm.deployProject", async () => {
      const target = await vscode.window.showQuickPick(
        ["vercel", "railway", "docker", "aws", "custom"],
        { placeHolder: "Select deployment target" }
      );
      if (target) {
        client.send({ type: "command", command: "deploy", target });
        vscode.window.showInformationMessage(
          `Jeph2Sworm: Deploying to ${target}...`
        );
      }
    }),

    vscode.commands.registerCommand("jeph2sworm.exportReport", async () => {
      const uri = await vscode.window.showSaveDialog({
        defaultUri: vscode.Uri.file("jeph2sworm-report.json"),
        filters: { "JSON Report": ["json"], "All Files": ["*"] },
      });
      if (uri) {
        const report = await client.exportReport();
        const content = Buffer.from(JSON.stringify(report, null, 2));
        await vscode.workspace.fs.writeFile(uri, content);
        vscode.window.showInformationMessage(
          `Jeph2Sworm: Report exported to ${uri.fsPath}`
        );
      }
    }),

    vscode.commands.registerCommand("jeph2sworm.connectBrowser", async () => {
      const browserPort = config.get<number>("browserExtensionPort", 9222);
      client.send({
        type: "connect_browser",
        port: browserPort,
      });
      vscode.window.showInformationMessage(
        `Jeph2Sworm: Connecting browser extension on port ${browserPort}...`
      );
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
