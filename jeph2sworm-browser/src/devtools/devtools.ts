/**
 * DevTools — creates the jeph2sworm DevTools panel.
 */

chrome.devtools.panels.create(
  'jeph2sworm',
  '',
  'devtools/panel.html',
  (panel) => {
    panel.onShown.addListener((window) => {
      // Panel is visible — start monitoring
      chrome.runtime.sendMessage({ type: 'devtools_panel_shown', tabId: chrome.devtools.inspectedWindow.tabId });
    });

    panel.onHidden.addListener(() => {
      chrome.runtime.sendMessage({ type: 'devtools_panel_hidden', tabId: chrome.devtools.inspectedWindow.tabId });
    });
  }
);
