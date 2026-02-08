/**
 * Side panel script - UI for the browser extension side panel.
 *
 * Uses modular SidePanelApp component with TaskStatus and ScreenshotPreview widgets.
 */

import { SidePanelApp } from "./sidepanel/SidePanel";

// Initialize the side panel app
const container = document.getElementById("app") || document.body;
const app = new SidePanelApp(container);

// Connect button (if the SidePanelApp doesn't provide one, add fallback)
const connectBtn = document.getElementById("connect-btn");
if (connectBtn) {
  connectBtn.addEventListener("click", () => {
    chrome.runtime.sendMessage({ type: "connect" });
  });
}

// Check initial status
chrome.runtime.sendMessage({ type: "get_status" }, (res) => {
  if (res?.connected) {
    // SidePanelApp handles status updates via runtime messages
    chrome.runtime.sendMessage({
      type: "connection_status",
      data: { connected: true },
    });
  }
});
