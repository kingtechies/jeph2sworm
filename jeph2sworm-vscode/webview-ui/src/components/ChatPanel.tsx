import React, { useState, useRef, useEffect } from 'react';

interface Message {
  id: string;
  role: 'user' | 'agent' | 'system';
  agent?: string;
  content: string;
  timestamp: number;
}

const AGENT_COLORS: Record<string, string> = {
  pm: '#4fc1ff',
  brain: '#c586c0',
  backend: '#dcdcaa',
  frontend: '#9cdcfe',
  ux: '#ce9178',
  tester: '#4ec9b0',
  devops: '#d7ba7d',
  system: '#888',
};

export default function ChatPanel({ vscode }: { vscode: any }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MessageEvent) => {
      const msg = e.data;
      if (msg.type === 'agent_message' || msg.type === 'chat_response') {
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'agent',
          agent: msg.agent,
          content: msg.content || msg.message,
          timestamp: Date.now(),
        }]);
      }
    };
    window.addEventListener('message', handler);
    return () => window.removeEventListener('message', handler);
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = () => {
    if (!input.trim()) return;
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: input, timestamp: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    vscode.postMessage({ type: 'chat', message: input });
    setInput('');
  };

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div className="scrollable" style={{ flex: 1, padding: 8 }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', padding: 40, color: 'var(--vscode-descriptionForeground)' }}>
            <p style={{ fontSize: 16, marginBottom: 8 }}>🐝 jeph2sworm</p>
            <p>Describe your product idea and the swarm will build it.</p>
          </div>
        )}
        {messages.map(m => (
          <div key={m.id} style={{ marginBottom: 8 }}>
            <div style={{ fontSize: 10, color: AGENT_COLORS[m.agent || 'system'] || '#888', fontWeight: 600, marginBottom: 2 }}>
              {m.role === 'user' ? 'You' : m.agent?.toUpperCase() || 'SYSTEM'}
            </div>
            <div style={{
              background: m.role === 'user' ? 'var(--vscode-input-background)' : 'var(--vscode-editor-inactiveSelectionBackground)',
              padding: '6px 10px', borderRadius: 6, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
            }}>
              {m.content}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <div style={{ display: 'flex', gap: 4, padding: 8, borderTop: '1px solid var(--vscode-panel-border)' }}>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          placeholder="Describe your product idea..."
          style={{ flex: 1 }}
        />
        <button onClick={send}>Send</button>
      </div>
    </div>
  );
}
