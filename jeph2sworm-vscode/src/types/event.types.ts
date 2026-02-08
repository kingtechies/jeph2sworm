/**
 * Event types for the VS Code extension.
 */

export type EventType =
  | 'agent_message'
  | 'agent_thinking'
  | 'agent_error'
  | 'task_created'
  | 'task_assigned'
  | 'task_started'
  | 'task_completed'
  | 'file_created'
  | 'file_modified'
  | 'code_generated'
  | 'test_passed'
  | 'test_failed'
  | 'build_started'
  | 'build_completed'
  | 'deploy_started'
  | 'deploy_completed'
  | 'browser_action'
  | 'credential_generated'
  | 'system_message'
  | 'user_message'
  | 'project_created';

export interface SwarmEvent {
  type: EventType;
  agent: string;
  data: Record<string, unknown>;
  timestamp: number;
}

export interface EventFilter {
  types?: EventType[];
  agents?: string[];
  since?: number;
}
