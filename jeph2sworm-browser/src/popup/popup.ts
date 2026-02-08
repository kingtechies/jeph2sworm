/**
 * Popup script — quick actions and connection status.
 */

const statusDot = document.getElementById('statusDot')!;
const statusText = document.getElementById('statusText')!;

// Check connection status
chrome.runtime.sendMessage({ type: 'get_status' }, (response) => {
  if (response?.connected) {
    statusDot.className = 'dot connected';
    statusText.textContent = `Connected to ${response.url || 'server'}`;
  }
});

document.getElementById('btnConnect')!.addEventListener('click', () => {
  chrome.runtime.sendMessage({ type: 'connect' }, (response) => {
    if (response?.ok) {
      statusDot.className = 'dot connected';
      statusText.textContent = 'Connected';
    }
  });
});

document.getElementById('btnCapture')!.addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.id) {
    chrome.runtime.sendMessage({ type: 'capture_screenshot', tabId: tab.id });
    window.close();
  }
});

document.getElementById('btnExtract')!.addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.id) {
    chrome.tabs.sendMessage(tab.id, { type: 'extract_dom' });
    window.close();
  }
});

document.getElementById('btnPanel')!.addEventListener('click', async () => {
  const [win] = await chrome.windows.getAll({ populate: false });
  if (win?.id) {
    chrome.sidePanel.open({ windowId: win.id });
  }
  window.close();
});
