import React, { useState, useEffect } from 'react';

interface Agent {
  role: string;
  status: string;
  currentTask?: string;
  tasksCompleted: number;
}

const STATUS_COLORS: Record<string, string> = {
  working: 'var(--vscode-charts-blue)',
  idle: 'var(--vscode-charts-green)',
  error: 'var(--vscode-charts-red)',
  starting: 'var(--vscode-charts-yellow)',
  stopped: 'var(--vscode-charts-purple)',
};

const ROLE_ICONS: Record<string, string> = {
  pm: '📋', brain: '🧠', backend: '⚙️', frontend: '🎨',
  ux: '🖌️', tester: '🧪', devops: '🚀',
};

export default function AgentDashboard({ vscode }: { vscode: any }) {
  const [agents, setAgents] = useState<Agent[]>([
    { role: 'pm', status: 'idle', tasksCompleted: 0 },
    { role: 'brain', status: 'idle', tasksCompleted: 0 },
    { role: 'backend', status: 'idle', tasksCompleted: 0 },
    { role: 'frontend', status: 'idle', tasksCompleted: 0 },
    { role: 'ux', status: 'idle', tasksCompleted: 0 },
    { role: 'tester', status: 'idle', tasksCompleted: 0 },
    { role: 'devops', status: 'idle', tasksCompleted: 0 },
  ]);

  useEffect(() => {
    const handler = (e: MessageEvent) => {
      const msg = e.data;
      if (msg.type === 'agent_status') {
        setAgents(prev => prev.map(a =>
          a.role === msg.agent ? { ...a, status: msg.status, currentTask: msg.task } : a
        ));
      }
      if (msg.type === 'agents_update') {
        setAgents(msg.agents);
      }
    };
    window.addEventListener('message', handler);
    return () => window.removeEventListener('message', handler);
  }, []);

  return (
    <div className="panel">
      <div className="panel-header">Agent Dashboard</div>
      <div style={{ display: 'grid', gap: 6 }}>
        {agents.map(a => (
          <div key={a.role} style={{
            background: 'var(--vscode-editor-inactiveSelectionBackground)',
            borderRadius: 6, padding: '8px 10px',
            borderLeft: `3px solid ${STATUS_COLORS[a.status] || '#888'}`,
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontWeight: 600 }}>
                {ROLE_ICONS[a.role] || '🤖'} {a.role.toUpperCase()}
              </span>
              <span className={`badge ${a.status}`}>{a.status}</span>
            </div>
            {a.currentTask && (
              <div style={{ fontSize: 11, color: 'var(--vscode-descriptionForeground)', marginTop: 4 }}>
                {a.currentTask}
              </div>
            )}
            <div style={{ fontSize: 10, color: 'var(--vscode-descriptionForeground)', marginTop: 2 }}>
              Tasks done: {a.tasksCompleted}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
