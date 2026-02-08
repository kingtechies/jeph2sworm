/**
 * StatusBadge — a small coloured badge indicating status.
 */

import React from 'react';

type Status = 'idle' | 'working' | 'success' | 'error' | 'warning' | 'pending';

interface StatusBadgeProps {
  status: Status;
  label?: string;
}

const STATUS_CONFIG: Record<Status, { bg: string; fg: string; icon: string }> = {
  idle: { bg: '#3c3c3c', fg: '#ccc', icon: '⏸' },
  working: { bg: '#264f78', fg: '#569cd6', icon: '⚡' },
  success: { bg: '#1e4620', fg: '#4ec9b0', icon: '✓' },
  error: { bg: '#5a1d1d', fg: '#f44747', icon: '✗' },
  warning: { bg: '#4e3a18', fg: '#dcdcaa', icon: '⚠' },
  pending: { bg: '#3b3b1f', fg: '#d7ba7d', icon: '◌' },
};

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label }) => {
  const cfg = STATUS_CONFIG[status];
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        padding: '2px 8px',
        borderRadius: 10,
        fontSize: 11,
        fontWeight: 600,
        background: cfg.bg,
        color: cfg.fg,
      }}
    >
      <span>{cfg.icon}</span>
      {label ?? status}
    </span>
  );
};
