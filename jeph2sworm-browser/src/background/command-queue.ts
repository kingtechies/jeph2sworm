/**
 * Command Queue — queues and processes browser automation commands sequentially.
 */

interface Command {
  id: string;
  type: string;
  params: Record<string, unknown>;
  resolve: (result: unknown) => void;
  reject: (error: Error) => void;
}

export class CommandQueue {
  private queue: Command[] = [];
  private processing = false;
  private handlers = new Map<string, (params: Record<string, unknown>) => Promise<unknown>>();

  registerHandler(type: string, handler: (params: Record<string, unknown>) => Promise<unknown>): void {
    this.handlers.set(type, handler);
  }

  async enqueue(type: string, params: Record<string, unknown>): Promise<unknown> {
    return new Promise((resolve, reject) => {
      const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
      this.queue.push({ id, type, params, resolve, reject });
      this.processNext();
    });
  }

  private async processNext(): Promise<void> {
    if (this.processing || this.queue.length === 0) return;
    this.processing = true;

    const cmd = this.queue.shift()!;
    const handler = this.handlers.get(cmd.type);

    if (!handler) {
      cmd.reject(new Error(`No handler for command type: ${cmd.type}`));
      this.processing = false;
      this.processNext();
      return;
    }

    try {
      const result = await handler(cmd.params);
      cmd.resolve(result);
    } catch (err) {
      cmd.reject(err instanceof Error ? err : new Error(String(err)));
    }

    this.processing = false;
    this.processNext();
  }

  get pendingCount(): number {
    return this.queue.length;
  }

  clear(): void {
    for (const cmd of this.queue) {
      cmd.reject(new Error('Queue cleared'));
    }
    this.queue = [];
  }
}
