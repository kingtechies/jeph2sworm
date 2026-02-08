/**
 * TaskStatus — widget showing current swarm task status.
 */

export interface TaskStatus {
  id: string;
  title: string;
  status: 'pending' | 'in-progress' | 'completed' | 'failed';
  assignee?: string;
  progress?: number;
}

const STATUS_ICONS: Record<string, string> = {
  'pending': '◌',
  'in-progress': '⚡',
  'completed': '✓',
  'failed': '✗',
};

const STATUS_COLORS: Record<string, string> = {
  'pending': '#888',
  'in-progress': '#569cd6',
  'completed': '#4ec9b0',
  'failed': '#f44747',
};

export class TaskStatusWidget {
  private container!: HTMLElement;
  private tasks: Map<string, TaskStatus> = new Map();

  mount(container: HTMLElement): void {
    this.container = container;
    this.render();
  }

  update(task: TaskStatus): void {
    this.tasks.set(task.id, task);
    this.render();
  }

  private render(): void {
    if (!this.container) { return; }

    if (this.tasks.size === 0) {
      this.container.innerHTML = '<p class="empty">No active tasks</p>';
      return;
    }

    const items = Array.from(this.tasks.values())
      .sort((a, b) => {
        const order = ['in-progress', 'pending', 'completed', 'failed'];
        return order.indexOf(a.status) - order.indexOf(b.status);
      })
      .map((t) => {
        const icon = STATUS_ICONS[t.status];
        const color = STATUS_COLORS[t.status];
        const bar = t.progress != null
          ? `<div class="task-progress"><div class="task-progress-fill" style="width:${t.progress}%"></div></div>`
          : '';
        return `
          <div class="task-item" style="border-left: 3px solid ${color}">
            <div class="task-header">
              <span style="color:${color}">${icon}</span>
              <span class="task-title">${t.title}</span>
            </div>
            ${t.assignee ? `<span class="task-assignee">${t.assignee}</span>` : ''}
            ${bar}
          </div>
        `;
      })
      .join('');

    this.container.innerHTML = items;
  }
}
