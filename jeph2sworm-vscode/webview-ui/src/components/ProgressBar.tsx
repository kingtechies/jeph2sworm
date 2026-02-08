/**
 * ProgressBar — animated progress bar with label and percentage.
 */

import React from 'react';

interface ProgressBarProps {
  value: number; // 0-100
  label?: string;
  color?: string;
  height?: number;
  showPercentage?: boolean;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  label,
  color = 'var(--vscode-progressBar-background)',
  height = 6,
  showPercentage = true,
}) => {
  const clamped = Math.max(0, Math.min(100, value));

  return (
    <div style={{ marginBottom: 8 }}>
      {(label || showPercentage) && (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: 12,
            marginBottom: 4,
            color: 'var(--vscode-descriptionForeground)',
          }}
        >
          <span>{label ?? ''}</span>
          {showPercentage && <span>{clamped.toFixed(0)}%</span>}
        </div>
      )}
      <div
        style={{
          width: '100%',
          height,
          background: 'var(--vscode-editor-inactiveSelectionBackground)',
          borderRadius: height / 2,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${clamped}%`,
            height: '100%',
            background: color,
            borderRadius: height / 2,
            transition: 'width 0.3s ease',
          }}
        />
      </div>
    </div>
  );
};
