import React, { useState, useRef, useEffect } from 'react';
import { MessageBubble } from './MessageBubble';
import { CodeBlock } from './CodeBlock';

interface Message {
  id: string;
  role: 'user' | 'agent' | 'system';
  agent?: string;
  content: string;
  timestamp: number;
}

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

  /** Split content into text and code blocks for rich rendering */
  const renderContent = (content: string) => {
    const parts = content.split(/(```[\s\S]*?```)/g);
    return parts.map((part, i) => {
      const codeMatch = part.match(/^```(\w*)\n?([\s\S]*?)```$/);
      if (codeMatch) {
        return <CodeBlock key={i} code={codeMatch[2].trim()} language={codeMatch[1] || 'text'} />;
      }
      return part ? <span key={i} style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{part}</span> : null;
    });
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
          <MessageBubble
            key={m.id}
            sender={m.role === 'user' ? 'You' : (m.agent?.toUpperCase() || 'SYSTEM')}
            senderRole={m.role === 'user' ? undefined : m.agent}
            content=""
            timestamp={m.timestamp}
            isUser={m.role === 'user'}
          >
            {renderContent(m.content)}
          </MessageBubble>
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
