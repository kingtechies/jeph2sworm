/**
 * DevTools Panel — network monitoring, console capture, performance metrics.
 */

// Tab switching
document.querySelectorAll('#tabs button').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('#tabs button').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    const tab = btn.getAttribute('data-tab')!;
    document.getElementById(tab)!.classList.add('active');
  });
});

// Network monitoring
const networkLog = document.getElementById('network-log')!;
const requests: Array<{ url: string; method: string; status: number; time: number }> = [];

chrome.devtools.network.onRequestFinished.addListener((request: any) => {
  const entry = {
    url: request.request.url,
    method: request.request.method,
    status: request.response.status,
    time: Math.round(request.time),
  };
  requests.push(entry);

  const div = document.createElement('div');
  div.className = `entry ${entry.status >= 400 ? 'error' : 'info'}`;
  div.textContent = `${entry.method} ${entry.status} ${entry.time}ms ${entry.url.substring(0, 80)}`;
  networkLog.appendChild(div);

  // Send to background for server relay
  chrome.runtime.sendMessage({ type: 'network_request', data: entry });
});

// Console capture
const consoleLog = document.getElementById('console-log')!;

chrome.devtools.inspectedWindow.eval(
  `(function() {
    const orig = { log: console.log, warn: console.warn, error: console.error };
    ['log','warn','error'].forEach(level => {
      console[level] = function(...args) {
        orig[level].apply(console, args);
        window.postMessage({ __jeph2sworm_console: true, level, args: args.map(String) }, '*');
      };
    });
  })()`,
  { useContentScriptContext: false }
);

// Listen for console messages via background
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'console_entry') {
    const div = document.createElement('div');
    div.className = `entry ${msg.level}`;
    div.textContent = `[${msg.level}] ${msg.args.join(' ')}`;
    consoleLog.appendChild(div);
  }
});

// Performance metrics
const perfMetrics = document.getElementById('perf-metrics')!;

function updatePerformance() {
  chrome.devtools.inspectedWindow.eval(
    `JSON.stringify(performance.getEntriesByType('navigation')[0])`,
    (result: string) => {
      try {
        const nav = JSON.parse(result);
        perfMetrics.innerHTML = [
          metric('DNS', Math.round(nav.domainLookupEnd - nav.domainLookupStart)),
          metric('TCP', Math.round(nav.connectEnd - nav.connectStart)),
          metric('TTFB', Math.round(nav.responseStart - nav.requestStart)),
          metric('DOM Load', Math.round(nav.domContentLoadedEventEnd - nav.navigationStart)),
          metric('Full Load', Math.round(nav.loadEventEnd - nav.navigationStart)),
        ].join('');
      } catch { /* ignore */ }
    }
  );
}

function metric(label: string, value: number): string {
  return `<span class="metric"><span class="label">${label}: </span><span class="value">${value}ms</span></span>`;
}

updatePerformance();
setInterval(updatePerformance, 5000);
