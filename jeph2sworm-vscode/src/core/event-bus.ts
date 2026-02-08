/**
 * Client-side Event Bus — mirrors Python event_bus.py.
 * Provides typed local event pub/sub within the extension.
 */

import { SwarmEvent } from '../types/event.types';

type Handler = (event: SwarmEvent) => void;

export class EventBus {
  private handlers = new Map<string, Set<Handler>>();
  private wildcardHandlers = new Set<Handler>();

  on(type: string, handler: Handler): void {
    if (type === '*') {
      this.wildcardHandlers.add(handler);
      return;
    }
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set());
    }
    this.handlers.get(type)!.add(handler);
  }

  off(type: string, handler: Handler): void {
    if (type === '*') {
      this.wildcardHandlers.delete(handler);
      return;
    }
    this.handlers.get(type)?.delete(handler);
  }

  emit(event: SwarmEvent): void {
    this.handlers.get(event.type)?.forEach(h => h(event));
    this.wildcardHandlers.forEach(h => h(event));
  }

  clear(): void {
    this.handlers.clear();
    this.wildcardHandlers.clear();
  }
}

export const eventBus = new EventBus();
