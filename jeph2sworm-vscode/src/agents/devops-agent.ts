/**
 * DevOps Agent — DevOps Engineer proxy.
 * Sets up Docker, CI/CD, hosting, environment variables, deploys.
 */

import { BaseAgent } from './base-agent';
import { WebSocketService } from '../services/websocket-service';

export class DevOpsAgent extends BaseAgent {
  constructor(ws: WebSocketService) {
    super('devops', ws);
  }

  get description(): string {
    return 'Sets up Docker, CI/CD, hosting, environment variables, and deploys the application';
  }

  get icon(): string {
    return '🚀';
  }

  async setupDocker(): Promise<void> {
    await this.sendCommand('setup_docker');
  }

  async setupCICD(): Promise<void> {
    await this.sendCommand('setup_cicd');
  }

  async deploy(target: string): Promise<void> {
    await this.sendCommand('deploy', { target });
  }

  async configureEnv(): Promise<void> {
    await this.sendCommand('configure_env');
  }

  async setupMonitoring(): Promise<void> {
    await this.sendCommand('setup_monitoring');
  }
}
