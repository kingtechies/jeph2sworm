import React, { useState } from 'react';
import ChatPanel from './components/ChatPanel';
import AgentDashboard from './components/AgentDashboard';
import ProgressView from './components/ProgressView';

type Tab = 'chat' | 'agents' | 'progress';

const vscode = (window as any).acquireVsCodeApi?.() ?? {
  postMessage: (msg: any) => console.log('vscode.postMessage', msg),
  getState: () => ({}),
  setState: (s: any) => s,
};

export default function App() {
  const [tab, setTab] = useState<Tab>('chat');

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <nav style={{ display: 'flex', gap: 0, borderBottom: '1px solid var(--vscode-panel-border)' }}>
        {(['chat', 'agents', 'progress'] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              flex: 1,
              borderRadius: 0,
              background: tab === t ? 'var(--vscode-tab-activeBackground)' : 'transparent',
              borderBottom: tab === t ? '2px solid var(--vscode-focusBorder)' : '2px solid transparent',
            }}
          >
            {t.charAt(0).toUpperCase() + t.slice(1)}
          </button>
        ))}
      </nav>
      <div className="scrollable" style={{ flex: 1 }}>
        {tab === 'chat' && <ChatPanel vscode={vscode} />}
        {tab === 'agents' && <AgentDashboard vscode={vscode} />}
        {tab === 'progress' && <ProgressView vscode={vscode} />}
      </div>
    </div>
  );
}
