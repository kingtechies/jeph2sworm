/**
 * ConnectionStatus — popup widget showing backend connection state.
 */

export class ConnectionStatus {
  private container!: HTMLElement;
  private connected = false;
  private serverUrl = 'ws://localhost:8000/ws';

  mount(container: HTMLElement): void {
    this.container = container;
    this.checkStatus();
    this.render();
  }

  private async checkStatus(): Promise<void> {
    try {
      const response = await chrome.runtime.sendMessage({ type: 'get_connection_status' });
      this.connected = response?.connected ?? false;
      this.serverUrl = response?.url ?? this.serverUrl;
    } catch {
      this.connected = false;
    }
    this.render();
  }

  private render(): void {
    if (!this.container) { return; }

    const dotColor = this.connected ? '#4ec9b0' : '#f44747';
    const statusLabel = this.connected ? 'Connected' : 'Disconnected';

    this.container.innerHTML = `
      <div class="conn-status">
        <div class="conn-header">
          <span class="conn-dot" style="background:${dotColor}"></span>
          <span class="conn-label">${statusLabel}</span>
        </div>
        <div class="conn-url">${this.serverUrl}</div>
        <div class="conn-actions">
          <button id="conn-toggle" class="btn ${this.connected ? 'btn-danger' : 'btn-primary'}">
            ${this.connected ? 'Disconnect' : 'Connect'}
          </button>
          <button id="conn-settings" class="btn btn-secondary">Settings</button>
        </div>
      </div>
    `;

    this.container.querySelector('#conn-toggle')?.addEventListener('click', () => {
      const action = this.connected ? 'disconnect' : 'connect';
      chrome.runtime.sendMessage({ type: action });
      setTimeout(() => this.checkStatus(), 500);
    });

    this.container.querySelector('#conn-settings')?.addEventListener('click', () => {
      chrome.runtime.openOptionsPage?.();
    });
  }
}
