/**
 * WebSocket Service - Manages WebSocket connection to the Python backend.
 */

import * as vscode from 'vscode';
import WebSocket from 'ws';
import { SwarmEvent } from '../types/event.types';

type EventCallback = (event: SwarmEvent) => void;

export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private listeners: Map<string, EventCallback[]> = new Map();
  private url: string;
  private connected = false;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 20;

  constructor(host: string = 'localhost', port: number = 8765) {
    this.url = `ws://${host}:${port}/ws/vscode`;
  }

  connect(): void {
    try {
      this.ws = new WebSocket(this.url);

      this.ws.on('open', () => {
        this.connected = true;
        this.reconnectAttempts = 0;
        this.emit('connection', { type: 'system_message', agent: 'system', data: { status: 'connected' }, timestamp: Date.now() });
      });

      this.ws.on('message', (data: WebSocket.Data) => {
        try {
          const event: SwarmEvent = JSON.parse(data.toString());
          this.emit(event.type, event);
          this.emit('*', event); // wildcard for all events
        } catch (e) {
          // ignore parse errors
        }
      });

      this.ws.on('close', () => {
        this.connected = false;
        this.scheduleReconnect();
      });

      this.ws.on('error', () => {
        this.connected = false;
      });
    } catch {
      this.scheduleReconnect();
    }
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.connected = false;
  }

  send(type: string, data: Record<string, unknown>): void {
    if (this.ws && this.connected) {
      this.ws.send(JSON.stringify({ type, data, timestamp: Date.now() }));
    }
  }

  on(eventType: string, callback: EventCallback): void {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType)!.push(callback);
  }

  off(eventType: string, callback: EventCallback): void {
    const cbs = this.listeners.get(eventType);
    if (cbs) {
      const idx = cbs.indexOf(callback);
      if (idx >= 0) { cbs.splice(idx, 1); }
    }
  }

  get isConnected(): boolean {
    return this.connected;
  }

  private emit(eventType: string, event: SwarmEvent): void {
    const cbs = this.listeners.get(eventType);
    if (cbs) {
      for (const cb of cbs) {
        try { cb(event); } catch { /* swallow */ }
      }
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) { return; }
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    this.reconnectAttempts++;
    this.reconnectTimer = setTimeout(() => this.connect(), delay);
  }
}
