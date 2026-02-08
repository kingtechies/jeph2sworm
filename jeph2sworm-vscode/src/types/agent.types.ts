/**
 * Agent types for the VS Code extension.
 */

export type AgentRole = 'pm' | 'brain' | 'backend' | 'frontend' | 'ux' | 'tester' | 'devops';

export type AgentStatus = 'idle' | 'working' | 'blocked' | 'paused' | 'stopped';

export interface AgentInfo {
  role: AgentRole;
  status: AgentStatus;
  currentTask?: string;
  tasksCompleted: number;
  errorsCount: number;
}

export interface AgentMessage {
  agent: AgentRole;
  content: string;
  timestamp: number;
  type: 'thought' | 'action' | 'result' | 'error';
}
