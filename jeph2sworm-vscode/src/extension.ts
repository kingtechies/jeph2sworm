/**
 * Jeph2Sworm VS Code Extension - Main entry point.
 *
 * Activates the sidebar, connects to the Python backend via WebSocket,
 * and provides commands for managing the AI swarm.
 */

import * as vscode from "vscode";
import { SwarmClient, SwarmEvent } from "./client";
import { ChatViewProvider } from "./views/chat-view";
import { AgentsTreeProvider } from "./views/agents-tree";
import { TasksTreeProvider } from "./views/tasks-tree";
import { EventFeedProvider } from "./views/event-feed";
import { FileChangeLogProvider } from "./views/sidebar/FileChangeLog";
import { TestDashboardPanel } from "./views/panels/TestDashboard";
import { AgentConversationPanel } from "./views/panels/AgentConversation";
import { SetupWizardPanel } from "./views/panels/SetupWizard";
import { AiEnvViewerPanel } from "./views/panels/AiEnvViewer";
import { BrainViewerPanel } from "./views/panels/BrainViewer";
import { DeployStatusPanel } from "./views/panels/DeployStatus";

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
  const eventFeedProvider = new EventFeedProvider(context.extensionUri);
  const fileChangeLogProvider = new FileChangeLogProvider();

  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider("jeph2sworm.chatView", chatProvider),
    vscode.window.registerTreeDataProvider("jeph2sworm.agentsView", agentsProvider),
    vscode.window.registerTreeDataProvider("jeph2sworm.tasksView", tasksProvider),
    vscode.window.registerWebviewViewProvider("jeph2sworm.eventFeed", eventFeedProvider),
    vscode.window.registerTreeDataProvider("jeph2sworm.fileChanges", fileChangeLogProvider)
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
      SetupWizardPanel.show(context.extensionUri);
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
        BrainViewerPanel.show(context.extensionUri);
        const brain = await client.getBrainSummary();
        // Convert brain stats to entries for the viewer
        const entries = Object.entries(brain).map(([key, value], i) => ({
          id: `brain-${i}`,
          type: "knowledge" as const,
          summary: `${key}: ${JSON.stringify(value).substring(0, 200)}`,
          timestamp: Date.now(),
          relevance: 1,
        }));
        BrainViewerPanel.setEntries(entries);
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
        AiEnvViewerPanel.show(context.extensionUri);
        const credentials = await client.getCredentials();
        const vars = credentials.map((cred: { key_name: string; purpose?: string; value?: string }) => ({
          key: cred.key_name,
          maskedValue: cred.value
            ? cred.value.slice(0, 4) + "****" + cred.value.slice(-4)
            : "****",
          provider: cred.purpose || "unknown",
          rotatedAt: new Date().toISOString(),
        }));
        AiEnvViewerPanel.setVars(vars);
      } catch (err) {
        vscode.window.showErrorMessage(`Jeph2Sworm: ${err}`);
      }
    }),

    vscode.commands.registerCommand("jeph2sworm.runTests", async () => {
      TestDashboardPanel.show(context.extensionUri);
      vscode.window.showInformationMessage("Jeph2Sworm: Starting test suite...");
      client.send({ type: "command", command: "run_tests" });
    }),

    vscode.commands.registerCommand("jeph2sworm.deployProject", async () => {
      const target = await vscode.window.showQuickPick(
        ["vercel", "railway", "docker", "aws", "custom"],
        { placeHolder: "Select deployment target" }
      );
      if (target) {
        DeployStatusPanel.show(context.extensionUri);
        client.send({ type: "command", command: "deploy", target });
        DeployStatusPanel.update({
          environment: target,
          status: "pending",
          version: "0.1.0",
          timestamp: Date.now(),
          logs: ["Deployment initiated..."],
        });
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
    }),

    // ---- Panels ----

    vscode.commands.registerCommand("jeph2sworm.viewConversations", async () => {
      AgentConversationPanel.show(context.extensionUri);
    }),

    vscode.commands.registerCommand("jeph2sworm.startProject", async (projectConfig: any) => {
      // Called by SetupWizard panel after user completes setup
      if (!projectConfig) { return; }
      if (projectConfig.apiKey && projectConfig.llmProvider) {
        await client.configureProvider(projectConfig.llmProvider, projectConfig.apiKey);
      }
      const message = `Create a new project called "${projectConfig.name}": ${projectConfig.description}. `
        + `Frontend: ${projectConfig.frontend}, Backend: ${projectConfig.backend}, `
        + `Database: ${projectConfig.database}`;
      await client.sendMessage(message);
      vscode.window.showInformationMessage(`Jeph2Sworm: Project "${projectConfig.name}" creation started!`);
    }),

    vscode.commands.registerCommand("jeph2sworm.rotateEnvVar", async (key: string) => {
      if (!key) { return; }
      client.send({ type: "command", command: "rotate_credential", key });
      vscode.window.showInformationMessage(`Jeph2Sworm: Rotating ${key}...`);
    })
  );

  // Listen for events from backend
  client.onEvent((event: SwarmEvent) => {
    agentsProvider.refresh();
    tasksProvider.refresh();
    chatProvider.onEvent(event);

    // Periodically push full state to React webview so all tabs update
    const et = event.type || event.event_type || "";
    if (et === "AGENT_STATUS_CHANGED" || et === "TASK_COMPLETED" || et === "TASK_CREATED" || et === "PROGRESS_UPDATE") {
      chatProvider.pushFullState();
    }

    // Feed events to EventFeedProvider (adapt shape)
    eventFeedProvider.addEvent({
      type: (event.type || event.event_type || "unknown") as any,
      agent: event.source || "system",
      data: event.data || {},
      timestamp: event.timestamp ? new Date(event.timestamp).getTime() / 1000 : Date.now() / 1000,
    });

    // Route file events to FileChangeLogProvider
    const eventType = event.type || event.event_type || "";
    if (eventType === "file_created" || eventType === "file_modified") {
      const data = event.data || {};
      fileChangeLogProvider.addChange({
        filePath: (data.file_path as string) || "unknown",
        agent: event.source || "system",
        action: eventType === "file_created" ? "created" : "modified",
        timestamp: Date.now(),
      });
    }

    // Route agent messages to AgentConversationPanel
    if (eventType === "agent_message") {
      const data = event.data || {};
      AgentConversationPanel.addMessage({
        from: event.source || "system",
        to: (data.target as string) || "user",
        content: (data.message as string) || JSON.stringify(data),
        timestamp: Date.now(),
      });
    }

    // Route test results to TestDashboardPanel
    if (eventType === "test_passed" || eventType === "test_failed") {
      const data = event.data || {};
      TestDashboardPanel.setResults([
        {
          name: (data.test_name as string) || "test",
          suite: (data.suite as string) || "default",
          status: eventType === "test_passed" ? "passed" : "failed",
          duration: (data.duration as number) || 0,
          error: data.error as string | undefined,
        },
      ]);
    }

    // Route deploy events to DeployStatusPanel
    if (eventType === "deploy_started" || eventType === "deploy_completed") {
      const data = event.data || {};
      DeployStatusPanel.update({
        environment: (data.target as string) || "unknown",
        status: eventType === "deploy_started" ? "deploying" : (data.success ? "success" : "failed"),
        version: (data.version as string) || "0.1.0",
        timestamp: Date.now(),
        logs: [(data.message as string) || eventType],
      });
    }
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
