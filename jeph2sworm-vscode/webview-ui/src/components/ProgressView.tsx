import React, { useState, useEffect } from 'react';

interface Task {
  id: string;
  title: string;
  status: string;
  assignee?: string;
  priority: string;
}

interface ProjectProgress {
  phase: string;
  tasksTotal: number;
  tasksCompleted: number;
  tasksPending: number;
  tasksInProgress: number;
}

const STATUS_ICON: Record<string, string> = {
  completed: '✅', in_progress: '🔄', pending: '⏳', blocked: '🚫', failed: '❌',
};

export default function ProgressView({ vscode }: { vscode: any }) {
  const [progress, setProgress] = useState<ProjectProgress>({
    phase: 'waiting', tasksTotal: 0, tasksCompleted: 0, tasksPending: 0, tasksInProgress: 0,
  });
  const [tasks, setTasks] = useState<Task[]>([]);

  useEffect(() => {
    const handler = (e: MessageEvent) => {
      const msg = e.data;
      if (msg.type === 'progress_update') { setProgress(msg.progress); }
      if (msg.type === 'tasks_update') { setTasks(msg.tasks); }
    };
    window.addEventListener('message', handler);
    return () => window.removeEventListener('message', handler);
  }, []);

  const pct = progress.tasksTotal > 0
    ? Math.round((progress.tasksCompleted / progress.tasksTotal) * 100)
    : 0;

  return (
    <div className="panel">
      <div className="panel-header">Project Progress</div>

      <div style={{ marginBottom: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
          <span>Phase: <strong>{progress.phase}</strong></span>
          <span>{pct}%</span>
        </div>
        <div style={{
          height: 6, borderRadius: 3, background: 'var(--vscode-progressBar-background, #333)',
          overflow: 'hidden',
        }}>
          <div style={{
            height: '100%', width: `${pct}%`, borderRadius: 3,
            background: 'var(--vscode-progressBar-background, var(--vscode-charts-blue))',
            transition: 'width 0.3s',
          }} />
        </div>
        <div style={{ display: 'flex', gap: 12, fontSize: 11, marginTop: 4, color: 'var(--vscode-descriptionForeground)' }}>
          <span>Done: {progress.tasksCompleted}</span>
          <span>Active: {progress.tasksInProgress}</span>
          <span>Pending: {progress.tasksPending}</span>
          <span>Total: {progress.tasksTotal}</span>
        </div>
      </div>

      <div className="panel-header" style={{ marginTop: 8 }}>Tasks</div>
      {tasks.length === 0 && (
        <div style={{ color: 'var(--vscode-descriptionForeground)', fontSize: 12 }}>No tasks yet</div>
      )}
      {tasks.map(t => (
        <div key={t.id} style={{
          padding: '4px 0', borderBottom: '1px solid var(--vscode-panel-border)',
          display: 'flex', gap: 6, alignItems: 'center', fontSize: 12,
        }}>
          <span>{STATUS_ICON[t.status] || '❓'}</span>
          <span style={{ flex: 1 }}>{t.title}</span>
          {t.assignee && <span className="badge working">{t.assignee}</span>}
          <span style={{ fontSize: 10, color: 'var(--vscode-descriptionForeground)' }}>{t.priority}</span>
        </div>
      ))}
    </div>
  );
}
