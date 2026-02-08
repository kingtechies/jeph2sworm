/**
 * ScreenshotPreview — widget showing captured screenshots in the sidepanel.
 */

interface Screenshot {
  url: string;
  timestamp: number;
}

export class ScreenshotPreviewWidget {
  private container!: HTMLElement;
  private screenshots: Screenshot[] = [];
  private maxScreenshots = 20;

  mount(container: HTMLElement): void {
    this.container = container;
    this.render();
  }

  addScreenshot(screenshot: Screenshot): void {
    this.screenshots.unshift(screenshot);
    if (this.screenshots.length > this.maxScreenshots) {
      this.screenshots = this.screenshots.slice(0, this.maxScreenshots);
    }
    this.render();
  }

  private render(): void {
    if (!this.container) { return; }

    if (this.screenshots.length === 0) {
      this.container.innerHTML = '<p class="empty">No screenshots captured</p>';
      return;
    }

    const items = this.screenshots
      .map(
        (s, i) => `
        <div class="screenshot-item" data-index="${i}">
          <img src="${s.url}" alt="Screenshot ${i + 1}" loading="lazy" />
          <span class="screenshot-time">${new Date(s.timestamp).toLocaleTimeString()}</span>
        </div>
      `
      )
      .join('');

    this.container.innerHTML = `<div class="screenshot-grid">${items}</div>`;

    // Add click-to-expand listeners
    this.container.querySelectorAll('.screenshot-item').forEach((el) => {
      el.addEventListener('click', (e) => {
        const target = e.currentTarget as HTMLElement;
        const idx = parseInt(target.dataset.index ?? '0', 10);
        this.showFullScreen(idx);
      });
    });
  }

  private showFullScreen(index: number): void {
    const screenshot = this.screenshots[index];
    if (!screenshot) { return; }

    const overlay = document.createElement('div');
    overlay.className = 'screenshot-overlay';
    overlay.innerHTML = `
      <div class="screenshot-full">
        <img src="${screenshot.url}" alt="Full screenshot" />
        <button class="screenshot-close">&times;</button>
        <span class="screenshot-time">${new Date(screenshot.timestamp).toLocaleString()}</span>
      </div>
    `;
    overlay.addEventListener('click', () => overlay.remove());
    document.body.appendChild(overlay);
  }

  clear(): void {
    this.screenshots = [];
    this.render();
  }
}

export type { Screenshot };
