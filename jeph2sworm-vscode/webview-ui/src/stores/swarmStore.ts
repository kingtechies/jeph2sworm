/**
 * SwarmStore — lightweight global state store for the webview.
 */

type Listener = () => void;

export interface StoreState {
  messages: Array<{
    id: string;
    sender: string;
    role?: string;
    content: string;
    timestamp: number;
  }>;
  agents: Array<{
    role: string;
    status: 'idle' | 'working' | 'error';
    task?: string;
  }>;
  tasks: Array<{
    id: string;
    title: string;
    status: 'pending' | 'in-progress' | 'completed' | 'failed';
    assignee?: string;
  }>;
  settings: Record<string, unknown>;
}

const initialState: StoreState = {
  messages: [],
  agents: [],
  tasks: [],
  settings: {},
};

class SwarmStore {
  private state: StoreState = { ...initialState };
  private listeners = new Set<Listener>();

  getState(): Readonly<StoreState> {
    return this.state;
  }

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notify(): void {
    this.listeners.forEach((l) => l());
  }

  addMessage(msg: StoreState['messages'][0]): void {
    this.state = { ...this.state, messages: [...this.state.messages, msg] };
    this.notify();
  }

  setAgents(agents: StoreState['agents']): void {
    this.state = { ...this.state, agents };
    this.notify();
  }

  updateAgent(role: string, update: Partial<StoreState['agents'][0]>): void {
    const agents = this.state.agents.map((a) =>
      a.role === role ? { ...a, ...update } : a
    );
    this.state = { ...this.state, agents };
    this.notify();
  }

  setTasks(tasks: StoreState['tasks']): void {
    this.state = { ...this.state, tasks };
    this.notify();
  }

  setSetting(key: string, value: unknown): void {
    this.state = {
      ...this.state,
      settings: { ...this.state.settings, [key]: value },
    };
    this.notify();
  }

  reset(): void {
    this.state = { ...initialState };
    this.notify();
  }
}

export const swarmStore = new SwarmStore();
