/**
 * Element Highlighter — visually highlights elements on the page for agent interaction.
 */

const HIGHLIGHT_CLASS = 'jeph2sworm-highlight';
const STYLE_ID = 'jeph2sworm-highlight-style';

function ensureStyles(): void {
  if (document.getElementById(STYLE_ID)) return;
  const style = document.createElement('style');
  style.id = STYLE_ID;
  style.textContent = `
    .${HIGHLIGHT_CLASS} {
      outline: 2px solid #4fc1ff !important;
      outline-offset: 2px;
      box-shadow: 0 0 8px rgba(79,193,255,0.5) !important;
      transition: outline 0.2s, box-shadow 0.2s;
    }
    .${HIGHLIGHT_CLASS}::after {
      content: attr(data-jeph-label);
      position: absolute;
      top: -20px;
      left: 0;
      background: #4fc1ff;
      color: #000;
      font-size: 10px;
      padding: 1px 6px;
      border-radius: 3px;
      font-family: monospace;
      z-index: 999999;
      white-space: nowrap;
    }
  `;
  document.head.appendChild(style);
}

export function highlightElement(selector: string, label?: string): HTMLElement | null {
  ensureStyles();
  const el = document.querySelector<HTMLElement>(selector);
  if (!el) return null;
  el.classList.add(HIGHLIGHT_CLASS);
  if (label) { el.setAttribute('data-jeph-label', label); }
  el.style.position = el.style.position || 'relative';
  return el;
}

export function highlightMultiple(selectors: Array<{ selector: string; label?: string }>): void {
  selectors.forEach(({ selector, label }) => highlightElement(selector, label));
}

export function clearHighlights(): void {
  document.querySelectorAll(`.${HIGHLIGHT_CLASS}`).forEach(el => {
    el.classList.remove(HIGHLIGHT_CLASS);
    el.removeAttribute('data-jeph-label');
  });
}

export function highlightByText(text: string, tag = '*'): HTMLElement | null {
  const els = document.querySelectorAll<HTMLElement>(tag);
  for (const el of els) {
    if (el.textContent?.trim().includes(text)) {
      return highlightElement(`${el.tagName.toLowerCase()}`, text);
    }
  }
  return null;
}
