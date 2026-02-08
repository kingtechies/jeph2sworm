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
    this.reconnectTimer = setTimeout(async () => {
      this.reconnectTimer = null;
      try {
        await this.connect();
      } catch {
        this.scheduleReconnect();
      }
    }, 3000);
  }

  onEvent(handler: EventHandler): void {
    this.eventHandlers.push(handler);
  }

  async sendMessage(message: string): Promise<void> {
    this.send({ type: "user_message", message });
  }

  async configureProvider(provider: string, apiKey: string): Promise<void> {
    const res = await fetch(
      `http://${this.host}:${this.port}/api/v1/llm/provider`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider, api_key: apiKey }),
      }
    );
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
  }

  async getStatus(): Promise<Record<string, unknown>> {
    const res = await fetch(
      `http://${this.host}:${this.port}/api/v1/status`
    );
    return res.json();
  }

  private send(data: Record<string, unknown>): void {
    if (this.ws && this.connected) {
      this.ws.send(JSON.stringify(data));
    }
  }

  get isConnected(): boolean {
    return this.connected;
  }
}
