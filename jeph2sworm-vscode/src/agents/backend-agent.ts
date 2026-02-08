/**
 * Backend Agent — Backend Developer proxy.
 * Implements APIs, database, authentication, business logic.
 */

import { BaseAgent } from './base-agent';
import { WebSocketService } from '../services/websocket-service';

export class BackendAgent extends BaseAgent {
  constructor(ws: WebSocketService) {
    super('backend', ws);
  }

  get description(): string {
    return 'Implements APIs, database, authentication, and business logic';
  }

  get icon(): string {
    return '⚙️';
  }

  async setupProject(): Promise<void> {
    await this.sendCommand('setup_project');
  }

  async implementEndpoint(endpoint: string): Promise<void> {
    await this.sendCommand('implement_endpoint', { endpoint });
  }

  async setupDatabase(): Promise<void> {
    await this.sendCommand('setup_database');
  }

  async implementAuth(): Promise<void> {
    await this.sendCommand('implement_auth');
  }
}
