/**
 * Orchestrator — top-level coordinator for the VS Code extension.
 * Wires together services, core modules, and views.
 */

import * as vscode from 'vscode';
import { WebSocketService } from '../services/websocket-service';
import { BrainClient } from './brain-client';
import { LLMRouterClient } from './llm-router';
import { FileManager } from './file-manager';
import { TerminalManager } from './terminal-manager';
import { CredentialManager } from './credential-manager';
import { RulesEngine } from './rules-engine';
import { EventBus, eventBus } from './event-bus';
import { TokenTrackerService } from '../services/token-tracker';

export class Orchestrator {
  readonly ws: WebSocketService;
  readonly brain: BrainClient;
  readonly llm: LLMRouterClient;
  readonly files: FileManager;
  readonly terminals: TerminalManager;
  readonly credentials: CredentialManager;
  readonly rules: RulesEngine;
  readonly events: EventBus;
  readonly tokenTracker: TokenTrackerService;

  private baseUrl: string;
  private disposables: vscode.Disposable[] = [];

  constructor(context: vscode.ExtensionContext) {
    const config = vscode.workspace.getConfiguration('jeph2sworm');
    const host = config.get<string>('serverHost', 'localhost');
    const port = config.get<number>('serverPort', 8000);
    this.baseUrl = `http://${host}:${port}`;

    const workspaceRoot =
      vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? '';

    this.ws = new WebSocketService(`ws://${host}:${port}/ws`);
    this.brain = new BrainClient(this.baseUrl);
    this.llm = new LLMRouterClient(this.baseUrl);
    this.files = new FileManager(workspaceRoot);
    this.terminals = new TerminalManager(workspaceRoot);
    this.credentials = new CredentialManager(workspaceRoot);
    this.rules = new RulesEngine(workspaceRoot);
    this.events = eventBus;
    this.tokenTracker = new TokenTrackerService();

    // Forward WebSocket events to local EventBus
    this.ws.on('*', (event: any) => {
      eventBus.emit(event);
    });
  }

  async activate(): Promise<void> {
    this.ws.connect();
    this.tokenTracker.activate(this.ws);
  }

  async startProject(description: string): Promise<void> {
    const resp = await fetch(`${this.baseUrl}/project/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description }),
    });
    if (!resp.ok) {
      throw new Error(`Failed to start project: ${resp.statusText}`);
    }
  }

  async sendMessage(message: string): Promise<void> {
    const resp = await fetch(`${this.baseUrl}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    if (!resp.ok) {
      throw new Error(`Failed to send message: ${resp.statusText}`);
    }
  }

  async getStatus(): Promise<Record<string, unknown>> {
    const resp = await fetch(`${this.baseUrl}/status`);
    return resp.json() as Promise<Record<string, unknown>>;
  }

  deactivate(): void {
    this.ws.disconnect();
    this.tokenTracker.deactivate();
    this.terminals.disposeAll();
    this.events.clear();
    this.disposables.forEach(d => d.dispose());
  }
}
