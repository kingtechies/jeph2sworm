/**
 * Side panel script - UI for the browser extension side panel.
 */

interface PanelMessage {
  type: string;
  data?: Record<string, unknown>;
  event_type?: string;
  source?: string;
  [key: string]: unknown;
}

const messagesDiv = document.getElementById("messages")!;
const statusDot = document.getElementById("status-dot")!;
const statusText = document.getElementById("status-text")!;
const connectBtn = document.getElementById("connect-btn")!;

function addLog(text: string, type: string = "info"): void {
  const div = document.createElement("div");
  div.className = `log ${type}`;
  div.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
  messagesDiv.appendChild(div);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Listen for messages from background
chrome.runtime.onMessage.addListener((msg: PanelMessage) => {
  if (msg.type === "connection_status") {
    const connected = msg.data?.connected as boolean;
    statusDot.className = `dot ${connected ? "connected" : "disconnected"}`;
    statusText.textContent = connected ? "Connected" : "Disconnected";
    addLog(connected ? "Connected to Jeph2Sworm backend" : "Disconnected", connected ? "success" : "error");
  } else if (msg.type === "event") {
    const eventType = msg.event_type || "";
    const source = msg.source || "";
    addLog(`[${eventType}] ${source}: ${JSON.stringify(msg.data || {}).substring(0, 120)}`, "event");
  } else if (msg.type === "browser_command") {
    addLog(`Command: ${JSON.stringify(msg.data || {})}`, "command");
  }
});

// Connect button
connectBtn.addEventListener("click", () => {
  chrome.runtime.sendMessage({ type: "connect" });
  addLog("Connecting...");
});

// Check initial status
chrome.runtime.sendMessage({ type: "get_status" }, (res) => {
  if (res?.connected) {
    statusDot.className = "dot connected";
    statusText.textContent = "Connected";
  }
});

addLog("Jeph2Sworm Browser Extension loaded");
