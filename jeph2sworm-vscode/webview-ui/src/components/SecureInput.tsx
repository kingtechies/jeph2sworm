/**
 * SecureInput — password/secret input with toggle visibility and strength indicator.
 */

import React, { useCallback, useState } from 'react';

interface SecureInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  label?: string;
  showStrength?: boolean;
}

function getStrength(val: string): { label: string; color: string; pct: number } {
  if (val.length === 0) { return { label: '', color: '#3c3c3c', pct: 0 }; }
  let score = 0;
  if (val.length >= 8) { score++; }
  if (val.length >= 16) { score++; }
  if (/[A-Z]/.test(val) && /[a-z]/.test(val)) { score++; }
  if (/[0-9]/.test(val)) { score++; }
  if (/[^A-Za-z0-9]/.test(val)) { score++; }
  const levels = [
    { label: 'Weak', color: '#f44747', pct: 20 },
    { label: 'Fair', color: '#dcdcaa', pct: 40 },
    { label: 'Good', color: '#d7ba7d', pct: 60 },
    { label: 'Strong', color: '#4ec9b0', pct: 80 },
    { label: 'Excellent', color: '#608b4e', pct: 100 },
  ];
  return levels[Math.min(score, levels.length) - 1] || levels[0];
}

export const SecureInput: React.FC<SecureInputProps> = ({
  value,
  onChange,
  placeholder = 'Enter secret...',
  label,
  showStrength = false,
}) => {
  const [visible, setVisible] = useState(false);
  const strength = getStrength(value);

  const toggle = useCallback(() => setVisible((v) => !v), []);

  return (
    <div style={{ marginBottom: 12 }}>
      {label && (
        <label
          style={{
            display: 'block',
            marginBottom: 4,
            fontSize: 12,
            fontWeight: 600,
          }}
        >
          {label}
        </label>
      )}
      <div style={{ display: 'flex', gap: 4 }}>
        <input
          type={visible ? 'text' : 'password'}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          style={{
            flex: 1,
            padding: '6px 8px',
            background: 'var(--vscode-input-background)',
            color: 'var(--vscode-input-foreground)',
            border: '1px solid var(--vscode-input-border)',
            borderRadius: 3,
            fontFamily: 'var(--vscode-editor-font-family)',
          }}
        />
        <button
          onClick={toggle}
          style={{
            background: 'var(--vscode-button-secondaryBackground)',
            color: 'var(--vscode-button-secondaryForeground)',
            border: 'none',
            padding: '4px 10px',
            cursor: 'pointer',
            borderRadius: 3,
            fontSize: 12,
          }}
        >
          {visible ? 'Hide' : 'Show'}
        </button>
      </div>
      {showStrength && value.length > 0 && (
        <div style={{ marginTop: 4 }}>
          <div
            style={{
              height: 3,
              width: `${strength.pct}%`,
              background: strength.color,
              borderRadius: 2,
              transition: 'width 0.2s',
            }}
          />
          <span style={{ fontSize: 10, color: strength.color }}>{strength.label}</span>
        </div>
      )}
    </div>
  );
};
