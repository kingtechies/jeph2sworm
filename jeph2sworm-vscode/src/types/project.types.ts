/**
 * Project types for the VS Code extension.
 */

export interface ProjectConfig {
  name: string;
  description: string;
  type: 'web' | 'mobile' | 'api' | 'fullstack' | 'cli';
  framework?: string;
  features: string[];
  database?: string;
}

export interface ProjectStatus {
  phase: 'planning' | 'designing' | 'building' | 'testing' | 'deploying' | 'complete';
  progress: number; // 0-100
  activeTasks: number;
  completedTasks: number;
  totalTasks: number;
  agents: Record<string, string>; // role -> status
}

export interface TaskInfo {
  id: string;
  title: string;
  description: string;
  status: 'backlog' | 'assigned' | 'in_progress' | 'review' | 'done' | 'blocked';
  priority: 'critical' | 'high' | 'medium' | 'low';
  assignedTo?: string;
  filesAffected: string[];
}
