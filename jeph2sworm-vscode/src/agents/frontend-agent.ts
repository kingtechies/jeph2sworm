/**
 * Frontend Agent — Frontend Developer proxy.
 * Implements UI components, state management, routing.
 */

import { BaseAgent } from './base-agent';
import { WebSocketService } from '../services/websocket-service';

export class FrontendAgent extends BaseAgent {
  constructor(ws: WebSocketService) {
    super('frontend', ws);
  }

  get description(): string {
    return 'Implements UI components, state management, routing, and API integration';
  }

  get icon(): string {
    return '🎨';
  }

  async setupProject(): Promise<void> {
    await this.sendCommand('setup_project');
  }

  async implementComponent(component: string): Promise<void> {
    await this.sendCommand('implement_component', { component });
  }

  async connectApi(endpoint: string): Promise<void> {
    await this.sendCommand('connect_api', { endpoint });
  }

  async implementRouting(): Promise<void> {
    await this.sendCommand('implement_routing');
  }
}
