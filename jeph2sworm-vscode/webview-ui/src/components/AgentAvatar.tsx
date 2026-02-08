/**
 * AgentAvatar — renders an agent's avatar with role-based color & icon.
 */

import React from 'react';

interface AgentAvatarProps {
  role: string;
  name?: string;
  size?: number;
  status?: 'idle' | 'working' | 'error';
}

const ROLE_COLORS: Record<string, string> = {
  pm: '#569cd6',
  brain: '#c586c0',
  backend: '#4ec9b0',
  frontend: '#dcdcaa',
  ux: '#ce9178',
  tester: '#d7ba7d',
  devops: '#608b4e',
};

const ROLE_ICONS: Record<string, string> = {
  pm: '📋',
  brain: '🧠',
  backend: '⚙️',
  frontend: '🎨',
  ux: '✏️',
  tester: '🧪',
  devops: '🚀',
};

export const AgentAvatar: React.FC<AgentAvatarProps> = ({
  role,
  name,
  size = 36,
  status = 'idle',
}) => {
  const color = ROLE_COLORS[role] ?? '#888';
  const icon = ROLE_ICONS[role] ?? '🤖';
  const statusDot =
    status === 'working' ? '🟢' : status === 'error' ? '🔴' : '';

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 8,
      }}
      title={name ?? role}
    >
      <div
        style={{
          width: size,
          height: size,
          borderRadius: '50%',
          backgroundColor: color,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: size * 0.5,
          position: 'relative',
        }}
      >
        {icon}
        {statusDot && (
          <span
            style={{
              position: 'absolute',
              bottom: -2,
              right: -2,
              fontSize: 10,
            }}
          >
            {statusDot}
          </span>
        )}
      </div>
      {name && <span style={{ fontSize: 13 }}>{name}</span>}
    </div>
  );
};
