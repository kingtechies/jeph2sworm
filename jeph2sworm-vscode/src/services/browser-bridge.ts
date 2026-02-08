/**
 * Browser Bridge - Communication bridge between VS Code and Chrome extension.
 */

import { WebSocketService } from './websocket-service';
import { SwarmEvent } from '../types/event.types';

export interface BrowserCommand {
  action: 'navigate' | 'click' | 'fill' | 'screenshot' | 'extract' | 'evaluate';
  target?: string;
  value?: string;
  selector?: string;
}

export interface BrowserResult {
  success: boolean;
  data?: unknown;
  error?: string;
  screenshot?: string; // base64
}

export class BrowserBridge {
  private ws: WebSocketService;
  private pendingCommands: Map<string, {
    resolve: (value: BrowserResult) => void;
    timeout: NodeJS.Timeout;
  }> = new Map();

  constructor(ws: WebSocketService) {
    this.ws = ws;
    this.ws.on('browser_action', (event: SwarmEvent) => {
      this.handleBrowserResponse(event);
    });
  }

  async sendCommand(command: BrowserCommand, timeoutMs = 30000): Promise<BrowserResult> {
    const commandId = `cmd_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;

    return new Promise((resolve) => {
      const timeout = setTimeout(() => {
        this.pendingCommands.delete(commandId);
        resolve({ success: false, error: 'Command timeout' });
      }, timeoutMs);

      this.pendingCommands.set(commandId, { resolve, timeout });

      this.ws.send('browser_command', {
        commandId,
        ...command,
      });
    });
  }

  async navigate(url: string): Promise<BrowserResult> {
    return this.sendCommand({ action: 'navigate', target: url });
  }

  async click(selector: string): Promise<BrowserResult> {
    return this.sendCommand({ action: 'click', selector });
  }

  async fill(selector: string, value: string): Promise<BrowserResult> {
    return this.sendCommand({ action: 'fill', selector, value });
  }

  async screenshot(): Promise<BrowserResult> {
    return this.sendCommand({ action: 'screenshot' });
  }

  async extractContent(selector?: string): Promise<BrowserResult> {
    return this.sendCommand({ action: 'extract', selector });
  }

  async evaluateJs(code: string): Promise<BrowserResult> {
    return this.sendCommand({ action: 'evaluate', value: code });
  }

  private handleBrowserResponse(event: SwarmEvent): void {
    const commandId = event.data.commandId as string;
    const pending = this.pendingCommands.get(commandId);
    if (pending) {
      clearTimeout(pending.timeout);
      this.pendingCommands.delete(commandId);
      pending.resolve({
        success: !event.data.error,
        data: event.data.result,
        error: event.data.error as string | undefined,
        screenshot: event.data.screenshot as string | undefined,
      });
    }
  }

  dispose(): void {
    for (const [, pending] of this.pendingCommands) {
      clearTimeout(pending.timeout);
    }
    this.pendingCommands.clear();
  }
}
