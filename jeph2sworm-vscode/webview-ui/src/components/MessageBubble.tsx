/**
 * MessageBubble — renders a single chat-like message bubble.
 */

import React from 'react';
import { AgentAvatar } from './AgentAvatar';

interface MessageBubbleProps {
  sender: string;
  senderRole?: string;
  content: string;
  timestamp?: number;
  isUser?: boolean;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  sender,
  senderRole,
  content,
  timestamp,
  isUser = false,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: isUser ? 'row-reverse' : 'row',
        gap: 8,
        marginBottom: 12,
        alignItems: 'flex-start',
      }}
    >
      {senderRole && !isUser && <AgentAvatar role={senderRole} size={28} />}
      <div
        style={{
          maxWidth: '75%',
          background: isUser
            ? 'var(--vscode-button-background)'
            : 'var(--vscode-editor-inactiveSelectionBackground)',
          color: isUser
            ? 'var(--vscode-button-foreground)'
            : 'var(--vscode-editor-foreground)',
          borderRadius: 8,
          padding: '8px 12px',
        }}
      >
        <div
          style={{
            fontSize: 11,
            opacity: 0.7,
            marginBottom: 4,
            fontWeight: 600,
          }}
        >
          {sender}
          {timestamp && (
            <span style={{ marginLeft: 8, fontWeight: 400 }}>
              {new Date(timestamp).toLocaleTimeString()}
            </span>
          )}
        </div>
        <div style={{ whiteSpace: 'pre-wrap', fontSize: 13 }}>{content}</div>
      </div>
    </div>
  );
};
