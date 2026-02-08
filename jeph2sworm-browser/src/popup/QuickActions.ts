/**
 * QuickActions — popup widget with common swarm actions.
 */

interface QuickAction {
  id: string;
  label: string;
  icon: string;
  description: string;
}

const ACTIONS: QuickAction[] = [
  { id: 'screenshot', label: 'Take Screenshot', icon: '📸', description: 'Capture current page' },
  { id: 'extract_dom', label: 'Extract DOM', icon: '🌐', description: 'Extract page structure' },
  { id: 'start_recording', label: 'Start Recording', icon: '🔴', description: 'Record screen activity' },
  { id: 'stop_recording', label: 'Stop Recording', icon: '⏹', description: 'Stop screen recording' },
  { id: 'inspect_element', label: 'Inspect Element', icon: '🔍', description: 'Highlight & inspect' },
  { id: 'run_a11y_check', label: 'Accessibility Check', icon: '♿', description: 'Run accessibility audit' },
];

export class QuickActions {
  private container!: HTMLElement;
  private recording = false;

  mount(container: HTMLElement): void {
    this.container = container;
    this.render();
  }

  private render(): void {
    if (!this.container) { return; }

    const buttons = ACTIONS.filter((a) => {
      if (a.id === 'stop_recording' && !this.recording) { return false; }
      if (a.id === 'start_recording' && this.recording) { return false; }
      return true;
    })
      .map(
        (a) => `
        <button class="quick-action" data-action="${a.id}" title="${a.description}">
          <span class="qa-icon">${a.icon}</span>
          <span class="qa-label">${a.label}</span>
        </button>
      `
      )
      .join('');

    this.container.innerHTML = `<div class="quick-actions">${buttons}</div>`;

    this.container.querySelectorAll('.quick-action').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const action = (e.currentTarget as HTMLElement).dataset.action;
        if (action) { this.execute(action); }
      });
    });
  }

  private async execute(actionId: string): Promise<void> {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab?.id) { return; }

      switch (actionId) {
        case 'screenshot':
          chrome.runtime.sendMessage({ type: 'take_screenshot', tabId: tab.id });
          break;
        case 'extract_dom':
          chrome.tabs.sendMessage(tab.id, { type: 'extract_dom' });
          break;
        case 'start_recording':
          chrome.runtime.sendMessage({ type: 'start_recording', tabId: tab.id });
          this.recording = true;
          this.render();
          break;
        case 'stop_recording':
          chrome.runtime.sendMessage({ type: 'stop_recording', tabId: tab.id });
          this.recording = false;
          this.render();
          break;
        case 'inspect_element':
          chrome.tabs.sendMessage(tab.id, { type: 'highlight_mode' });
          window.close();
          break;
        case 'run_a11y_check':
          chrome.tabs.sendMessage(tab.id, { type: 'a11y_check' });
          break;
      }
    } catch (err) {
      console.error('Quick action failed:', err);
    }
  }
}
