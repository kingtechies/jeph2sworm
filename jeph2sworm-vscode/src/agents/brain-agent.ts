/**
 * Brain Agent — Architect proxy.
 * Designs architecture, chooses tech stack, defines API contracts.
 */

import { BaseAgent } from './base-agent';
import { WebSocketService } from '../services/websocket-service';

export class BrainAgent extends BaseAgent {
  constructor(ws: WebSocketService) {
    super('brain', ws);
  }

  get description(): string {
    return 'Designs system architecture, chooses tech stack, defines API contracts and database schema';
  }

  get icon(): string {
    return '🧠';
  }

  async designArchitecture(): Promise<void> {
    await this.sendCommand('design_architecture');
  }

  async defineApiContracts(): Promise<void> {
    await this.sendCommand('define_api_contracts');
  }

  async defineDatabase(): Promise<void> {
    await this.sendCommand('define_database');
  }

  async resolveConflict(description: string): Promise<void> {
    await this.sendCommand('resolve_conflict', { description });
  }
}
