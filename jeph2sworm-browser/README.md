# Jeph2Sworm Browser Extension

Chrome extension companion for the Jeph2Sworm autonomous AI development swarm.

## Features

- **WebSocket Bridge**: Real-time connection to the Jeph2Sworm backend server.
- **Side Panel**: Live task status, activity log, and screenshot previews.
- **DevTools Integration**: Network monitoring, console capture, and performance metrics.
- **Content Script**: DOM extraction, element highlighting, form filling, screenshot capture.
- **Screen Recording**: Capture development sessions as visual evidence.
- **Accessibility Auditing**: Run a11y checks on the inspected page.

## Architecture

```
src/
├── background.ts          # Service worker — WebSocket client, command routing
├── background/
│   ├── websocket-client.ts  # Persistent WS connection to backend
│   ├── command-queue.ts     # Queue & retry for commands
│   └── tab-manager.ts       # Chrome tab lifecycle management
├── content.ts              # Content script — DOM access entry point
├── content/
│   ├── dom-extractor.ts     # Extract DOM tree & metadata
│   ├── element-highlighter.ts # Visual element selection
│   ├── form-filler.ts       # AI-driven form filling
│   └── screenshot.ts        # Page screenshot capture
├── devtools/
│   ├── devtools.ts          # DevTools page entry
│   ├── panel.ts             # Custom DevTools panel
│   ├── network-monitor.ts   # Network request capture
│   ├── console-capture.ts   # Console message interception
│   └── performance.ts       # Performance metric collection
├── sidepanel.ts             # Side panel entry script
├── sidepanel/
│   ├── SidePanel.ts         # Main side panel application
│   ├── TaskStatus.ts        # Task status widget
│   └── ScreenshotPreview.ts # Screenshot gallery widget
├── popup/
│   ├── popup.ts             # Popup entry
│   ├── ConnectionStatus.ts  # Connection state widget
│   └── QuickActions.ts      # Quick action buttons
├── recorder/
│   ├── screen-recorder.ts   # MediaRecorder-based capture
│   └── recording-manager.ts # Recording session management
├── utils/
│   ├── messaging.ts         # Chrome messaging helpers
│   ├── storage.ts           # chrome.storage wrapper
│   └── logger.ts            # Extension logger
└── types/
    ├── commands.types.ts    # Command type definitions
    ├── messages.types.ts    # Message type definitions
    └── devtools.types.ts    # DevTools type definitions
```

## Development

```bash
npm install
npm run build        # One-time build
npm run watch        # Watch mode
```

### Load in Chrome

1. Navigate to `chrome://extensions`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `jeph2sworm-browser` directory

## Configuration

The extension connects to the backend at `ws://localhost:8000/ws` by default.
Change this in the popup settings or via `chrome.storage.sync`.

## Permissions

- `tabs` — Tab management and navigation
- `activeTab` — Current tab access
- `scripting` — Content script injection
- `storage` — Settings persistence
- `sidePanel` — Side panel UI
- `devtools` — DevTools panel and network monitoring
- `tabCapture` — Screen recording
