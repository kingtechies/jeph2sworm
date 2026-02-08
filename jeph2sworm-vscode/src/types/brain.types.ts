/**
 * Brain types for the VS Code extension.
 */

export interface BrainStats {
  totalDecisions: number;
  totalTasks: number;
  sections: string[];
  lastUpdated: number;
}

export interface BrainDecision {
  id: string;
  title: string;
  description: string;
  rationale: string;
  decidedBy: string;
  category: string;
  status: 'active' | 'superseded' | 'reverted';
  timestamp: number;
}

export interface BrainContext {
  projectSpec: Record<string, unknown>;
  architecture: Record<string, unknown>;
  taskBoardSummary: Record<string, number>;
}
