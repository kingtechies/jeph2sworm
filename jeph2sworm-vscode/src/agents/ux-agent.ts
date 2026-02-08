/**
 * UX Agent — UI/UX Designer proxy.
 * Creates design system, page layouts, component specs.
 */

import { BaseAgent } from './base-agent';
import { WebSocketService } from '../services/websocket-service';

export class UXAgent extends BaseAgent {
  constructor(ws: WebSocketService) {
    super('ux', ws);
  }

  get description(): string {
    return 'Creates design system, page layouts, component specs, and visual identity';
  }

  get icon(): string {
    return '🖌️';
  }

  async createDesignSystem(): Promise<void> {
    await this.sendCommand('create_design_system');
  }

  async designPage(page: string): Promise<void> {
    await this.sendCommand('design_page', { page });
  }

  async createComponentSpec(component: string): Promise<void> {
    await this.sendCommand('create_component_spec', { component });
  }

  async reviewImplementation(): Promise<void> {
    await this.sendCommand('review_implementation');
  }
}
