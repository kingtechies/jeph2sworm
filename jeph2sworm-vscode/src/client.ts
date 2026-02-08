/**
 * WebSocket client for communicating with the Jeph2Sworm backend.
 */

import WebSocket from "ws";

export interface SwarmEvent {
  type: string;
  event_type?: string;
  source?: string;
  data?: Record<string, unknown>;
  timestamp?: string;
}

type EventHandler = (event: SwarmEvent) => void;

export class SwarmClient {
  private ws: WebSocket | null = null;
  private host: string;
  private port: number;
  private clientId: string;
  private eventHandlers: EventHandler[] = [];
  private reconnectTimer: NodeJS.Timeout | null = null;
  private connected = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;

  constructor(host: string, port: number) {
    this.host = host;
    this.port = port;
    this.clientId = `vscode-${Date.now()}`;
  }

  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const url = `ws://${this.host}:${this.port}/ws/${this.clientId}?client_type=vscode`;
      this.ws = new WebSocket(url);

      this.ws.on("open", () => {
        this.connected = true;
        this.reconnectAttempts = 0;
        resolve();
      });

      this.ws.on("message", (data: WebSocket.Data) => {
        try {
          const event: SwarmEvent = JSON.parse(data.toString());
          this.eventHandlers.forEach((h) => h(event));
        } catch {
          // Ignore malformed messages
        }
      });

      this.ws.on("close", () => {
        this.connected = false;
        this.scheduleReconnect();
      });

      this.ws.on("error", (err) => {
        if (!this.connected) {
          reject(err);
        }
      });
    });
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.connected = false;
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) return;
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
    this.reconnectAttempts++;
    const delay = Math.min(3000 * Math.pow(1.5, this.reconnectAttempts - 1), 30000);
    this.reconnectTimer = setTimeout(async () => {
      this.reconnectTimer = null;
      try {
        await this.connect();
      } catch {
        this.scheduleReconnect();
      }
    }, delay);
  }

  onEvent(handler: EventHandler): void {
    this.eventHandlers.push(handler);
  }

  async sendMessage(message: string): Promise<void> {
    this.send({ type: "user_message", message });
  }

  async configureProvider(provider: string, apiKey: string): Promise<void> {
    try {
      const res = await fetch(
        `http://${this.host}:${this.port}/api/v1/llm/provider`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ provider, api_key: apiKey }),
        }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
    } catch (err) {
      console.error("Failed to configure provider:", err);
      throw err;
    }
  }

  async getStatus(): Promise<Record<string, unknown>> {
    try {
      const res = await fetch(
        `http://${this.host}:${this.port}/api/v1/status`
      );
      return res.json();
    } catch {
      return { running: false, agents: {} };
    }
  }

  async getAgents(): Promise<Array<{ role: string; status: string; current_task?: string }>> {
    try {
      const res = await fetch(
        `http://${this.host}:${this.port}/api/v1/agents`
      );
      const data = await res.json();
      // Backend returns { agents: { "pm-agent": {...}, ... } } — convert to array
      const agents = data.agents || {};
      return Object.entries(agents).map(([id, info]: [string, any]) => ({
        role: info.role,
        status: info.status,
        current_task: info.current_task,
      }));
    } catch {
      return [];
    }
  }

  async getBrainSummary(): Promise<Record<string, unknown>> {
    try {
      const res = await fetch(
        `http://${this.host}:${this.port}/api/v1/brain/stats`
      );
      return res.json();
    } catch {
      return {};
    }
  }

  async getCredentials(): Promise<Array<{ key_name: string; purpose: string; value?: string }>> {
    try {
      const res = await fetch(
        `http://${this.host}:${this.port}/api/v1/credentials`
      );
      const data = await res.json();
      return data.credentials || [];
    } catch {
      return [];
    }
  }

  async getTasks(): Promise<Record<string, unknown>> {
    try {
      const res = await fetch(
        `http://${this.host}:${this.port}/api/v1/tasks`
      );
      return res.json();
    } catch {
      return { task_board: {} };
    }
  }

  async exportReport(): Promise<Record<string, unknown>> {
    const [status, brain, agents] = await Promise.all([
      this.getStatus(),
      this.getBrainSummary(),
      this.getAgents(),
    ]);
    return {
      generated_at: new Date().toISOString(),
      status,
      brain,
      agents,
    };
  }

  send(data: Record<string, unknown>): void {
    if (this.ws && this.connected) {
      this.ws.send(JSON.stringify(data));
    }
  }

  get isConnected(): boolean {
    return this.connected;
  }
}
