/**
 * CodeBlock — syntax-highlighted code block with copy button.
 */

import React, { useCallback, useState } from 'react';

interface CodeBlockProps {
  code: string;
  language?: string;
  maxHeight?: number;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({
  code,
  language = 'text',
  maxHeight = 400,
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [code]);

  return (
    <div
      style={{
        position: 'relative',
        borderRadius: 4,
        overflow: 'hidden',
        marginBottom: 12,
        border: '1px solid var(--vscode-panel-border)',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '4px 10px',
          background: 'var(--vscode-editorGroupHeader-tabsBackground)',
          fontSize: 11,
          color: 'var(--vscode-descriptionForeground)',
        }}
      >
        <span>{language}</span>
        <button
          onClick={handleCopy}
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--vscode-textLink-foreground)',
            cursor: 'pointer',
            fontSize: 11,
          }}
        >
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <pre
        style={{
          margin: 0,
          padding: 12,
          background: 'var(--vscode-editor-background)',
          overflow: 'auto',
          maxHeight,
          fontSize: 13,
          fontFamily: 'var(--vscode-editor-font-family)',
          lineHeight: 1.5,
        }}
      >
        <code>{code}</code>
      </pre>
    </div>
  );
};
