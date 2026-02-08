/**
 * PM Agent — Project Manager proxy.
 * Gathers requirements, breaks project into tasks, communicates with user.
 */

import { BaseAgent } from './base-agent';
import { WebSocketService } from '../services/websocket-service';

export class PMAgent extends BaseAgent {
  constructor(ws: WebSocketService) {
    super('pm', ws);
  }

  get description(): string {
    return 'Gathers requirements, creates milestones, assigns tasks, and communicates status';
  }

  get icon(): string {
    return '📋';
  }

  async gatherRequirements(userInput: string): Promise<void> {
    await this.sendCommand('gather_requirements', { input: userInput });
  }

  async createMilestones(): Promise<void> {
    await this.sendCommand('create_milestones');
  }

  async assignTasks(): Promise<void> {
    await this.sendCommand('assign_tasks');
  }

  async requestClarification(question: string): Promise<void> {
    await this.sendCommand('request_clarification', { question });
  }
}
