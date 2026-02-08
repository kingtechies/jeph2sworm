/**
 * Base Agent — abstract base class for all client-side agent representations.
 * These are thin proxies that communicate with the Python backend agents.
 */

import { AgentRole, AgentStatus, AgentInfo } from '../types/agent.types';
import { WebSocketService } from '../services/websocket-service';
import { eventBus } from '../core/event-bus';

export abstract class BaseAgent {
  readonly role: AgentRole;
  status: AgentStatus = 'idle';
  currentTask?: string;
  tasksCompleted = 0;

  protected ws: WebSocketService;

  constructor(role: AgentRole, ws: WebSocketService) {
    this.role = role;
    this.ws = ws;

    // Listen for status updates from backend
    eventBus.on('agent_status_changed', (event) => {
      if (event.data?.agent === this.role) {
        this.status = event.data.status as AgentStatus;
        this.currentTask = event.data.current_task as string | undefined;
      }
    });

    eventBus.on('task_completed', (event) => {
      if (event.agent === this.role) {
        this.tasksCompleted++;
      }
    });
  }

  get info(): AgentInfo {
    return {
      role: this.role,
      status: this.status,
      currentTask: this.currentTask,
      tasksCompleted: this.tasksCompleted,
      errorsCount: 0,
    };
  }

  async sendCommand(command: string, params: Record<string, unknown> = {}): Promise<void> {
    this.ws.send('agent_command', {
      agent: this.role,
      command,
      params,
    });
  }

  abstract get description(): string;
  abstract get icon(): string;
}
