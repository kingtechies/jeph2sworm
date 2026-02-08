/**
 * SidePanel — main side panel component (DOM-based, no React dependency in Chrome extension).
 */

import { TaskStatus, TaskStatusWidget } from './TaskStatus';
import { ScreenshotPreview, ScreenshotPreviewWidget } from './ScreenshotPreview';

export class SidePanelApp {
  private container: HTMLElement;
  private taskWidget: TaskStatusWidget;
  private screenshotWidget: ScreenshotPreviewWidget;
  private logContainer!: HTMLElement;

  constructor(container: HTMLElement) {
    this.container = container;
    this.taskWidget = new TaskStatusWidget();
    this.screenshotWidget = new ScreenshotPreviewWidget();
    this.render();
    this.listen();
  }

  private render(): void {
    this.container.innerHTML = `
      <div class="j2s-sidepanel">
        <header class="j2s-header">
          <img src="../public/icons/icon-48.png" alt="Jeph2Sworm" width="24" height="24">
          <h2>Jeph2Sworm</h2>
          <span id="sp-status" class="status-dot disconnected"></span>
        </header>
        <section id="sp-tasks" class="j2s-section">
          <h3>Active Tasks</h3>
          <div id="sp-tasks-list"></div>
        </section>
        <section id="sp-screenshots" class="j2s-section">
          <h3>Screenshots</h3>
          <div id="sp-screenshots-list"></div>
        </section>
        <section id="sp-log" class="j2s-section">
          <h3>Activity Log</h3>
          <div id="sp-log-list" class="log-list"></div>
        </section>
      </div>
    `;

    this.logContainer = this.container.querySelector('#sp-log-list')!;
    const tasksContainer = this.container.querySelector('#sp-tasks-list')!;
    const screenshotsContainer = this.container.querySelector('#sp-screenshots-list')!;

    this.taskWidget.mount(tasksContainer as HTMLElement);
    this.screenshotWidget.mount(screenshotsContainer as HTMLElement);
  }

  private listen(): void {
    chrome.runtime.onMessage.addListener((msg) => {
      switch (msg.type) {
        case 'connection_status':
          this.updateStatus(msg.data?.connected as boolean);
          break;
        case 'task_update':
          this.taskWidget.update(msg.data as TaskStatus);
          break;
        case 'screenshot_taken':
          this.screenshotWidget.addScreenshot(msg.data as { url: string; timestamp: number });
          break;
        case 'event':
          this.addLog(msg.event_type ?? 'event', JSON.stringify(msg.data ?? {}).slice(0, 120));
          break;
      }
    });
  }

  private updateStatus(connected: boolean): void {
    const dot = this.container.querySelector('#sp-status');
    if (dot) {
      dot.className = `status-dot ${connected ? 'connected' : 'disconnected'}`;
    }
  }

  private addLog(type: string, message: string): void {
    const div = document.createElement('div');
    div.className = 'log-entry';
    div.innerHTML = `<span class="log-time">${new Date().toLocaleTimeString()}</span> <strong>${type}</strong>: ${message}`;
    this.logContainer.appendChild(div);
    this.logContainer.scrollTop = this.logContainer.scrollHeight;
  }
}
