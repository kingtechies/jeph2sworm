/**
 * Tasks tree view - shows the swarm task board.
 */

import * as vscode from "vscode";
import { SwarmClient } from "../client";

interface TaskItem {
  id: string;
  title: string;
  assigned_to: string;
  priority: string;
  status: string;
}

export class TasksTreeProvider implements vscode.TreeDataProvider<TaskGroupItem | TaskTreeItem> {
  private _onDidChangeTreeData = new vscode.EventEmitter<TaskGroupItem | TaskTreeItem | undefined | null>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  private taskBoard: Record<string, TaskItem[]> = {};

  constructor(private client: SwarmClient) {}

  refresh(): void {
    this.fetchTasks();
    this._onDidChangeTreeData.fire(undefined);
  }

  private async fetchTasks(): Promise<void> {
    if (!this.client.isConnected) return;
    try {
      const res = await fetch(
        `http://${(this.client as any).host}:${(this.client as any).port}/api/v1/tasks`
      );
      const data = await res.json();
      this.taskBoard = data.task_board || {};
    } catch {
      // Ignore
    }
  }

  getTreeItem(element: TaskGroupItem | TaskTreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: TaskGroupItem): (TaskGroupItem | TaskTreeItem)[] {
    if (!element) {
      // Root level: show groups (backlog, in_progress, done, etc.)
      return Object.entries(this.taskBoard).map(
        ([status, tasks]) => new TaskGroupItem(status, tasks as TaskItem[])
      );
    }

    // Child level: show tasks in the group
    return element.tasks.map((t) => new TaskTreeItem(t));
  }
}

class TaskGroupItem extends vscode.TreeItem {
  constructor(
    public readonly groupName: string,
    public readonly tasks: TaskItem[]
  ) {
    super(
      `${groupName} (${tasks.length})`,
      tasks.length > 0
        ? vscode.TreeItemCollapsibleState.Expanded
        : vscode.TreeItemCollapsibleState.None
    );

    const iconMap: Record<string, string> = {
      backlog: "inbox",
      assigned: "person",
      in_progress: "sync~spin",
      review: "eye",
      done: "check",
    };
    this.iconPath = new vscode.ThemeIcon(iconMap[groupName] || "list-flat");
  }
}

class TaskTreeItem extends vscode.TreeItem {
  constructor(task: TaskItem) {
    super(task.title || task.id, vscode.TreeItemCollapsibleState.None);

    this.description = `${task.assigned_to || ""} [${task.priority || ""}]`;
    this.tooltip = `${task.id}: ${task.title}\nAssigned: ${task.assigned_to}\nPriority: ${task.priority}`;

    const priorityIcon: Record<string, string> = {
      high: "flame",
      medium: "circle-filled",
      low: "circle-outline",
    };
    this.iconPath = new vscode.ThemeIcon(
      priorityIcon[task.priority] || "circle-outline"
    );
  }
}
