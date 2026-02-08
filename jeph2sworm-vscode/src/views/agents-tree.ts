/**
 * Agents tree view - shows the status of all swarm agents.
 */

import * as vscode from "vscode";
import { SwarmClient } from "../client";

export class AgentsTreeProvider implements vscode.TreeDataProvider<AgentItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<AgentItem | undefined | null>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  private agents: Record<string, { role: string; status: string; current_task: unknown }> = {};

  constructor(private client: SwarmClient) {}

  refresh(): void {
    this.fetchAgents().then(() => {
      this._onDidChangeTreeData.fire(undefined);
    });
  }

  private async fetchAgents(): Promise<void> {
    if (!this.client.isConnected) return;
    try {
      const status = await this.client.getStatus();
      this.agents = (status.agents as Record<string, { role: string; status: string; current_task: unknown }>) || {};
    } catch {
      // Ignore fetch errors
    }
  }

  getTreeItem(element: AgentItem): vscode.TreeItem {
    return element;
  }

  getChildren(): AgentItem[] {
    return Object.entries(this.agents).map(
      ([id, info]) => new AgentItem(id, info.role, info.status)
    );
  }
}

class AgentItem extends vscode.TreeItem {
  constructor(
    public readonly agentId: string,
    public readonly role: string,
    public readonly status: string
  ) {
    super(role.toUpperCase(), vscode.TreeItemCollapsibleState.None);

    this.description = status;
    this.tooltip = `${agentId} - ${status}`;

    const iconMap: Record<string, string> = {
      working: "sync~spin",
      idle: "circle-outline",
      blocked: "warning",
      paused: "debug-pause",
      stopped: "circle-slash",
    };
    this.iconPath = new vscode.ThemeIcon(iconMap[status] || "circle-outline");
  }
}
