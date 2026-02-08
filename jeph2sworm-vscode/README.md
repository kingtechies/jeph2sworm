# Jeph2Sworm — VS Code Extension

**Autonomous AI Development Swarm** — from idea to production, automatically.

## Features

- **Multi-Agent Swarm**: 7 specialized AI agents (PM, Brain/Architect, Backend, Frontend, UX, Tester, DevOps) working in parallel.
- **8 LLM Providers**: OpenAI, Anthropic, Grok, Gemini, DeepSeek, Mistral, LLaMA, Cohere — with automatic routing and fallback.
- **Chat Sidebar**: Conversational interface for project ideation, progress tracking, and swarm control.
- **Agent Dashboard**: Real-time visibility into what every agent is doing.
- **Brain Memory**: Shared context store with RAG for relevant retrieval.
- **120-Cycle Testing**: Comprehensive unit, integration, E2E, edge-case, and regression testing.
- **ai.env Management**: Auto-generated secure credentials (128-bit entropy) with masked viewer.
- **Browser Integration**: Companion Chrome extension for live testing, screenshots, screen recording, and DevTools access.
- **File & Terminal Access**: Agents create files, run commands, install packages, and commit to git autonomously.
- **Rules Engine**: Safety-first design — no file deletion, no hallucinated imports, no external data exfiltration.

## Requirements

- VS Code `1.85.0` or later
- Node.js `18+` (for building)
- Python `3.11+` (for the backend)
- An API key from at least one supported LLM provider

## Quick Start

1. Install the extension from the VS Code Marketplace (or load unpacked from `dist/`).
2. Open the **Jeph2Sworm** sidebar (activity bar icon).
3. Click **Setup Wizard** → provide your LLM API key.
4. Describe your project idea in the chat.
5. Approve the plan → agents start building.

## Extension Commands

| Command | Description |
|---|---|
| `Jeph2Sworm: Start New Project` | Begin a new project from idea |
| `Jeph2Sworm: Connect API Key` | Add/update LLM provider key |
| `Jeph2Sworm: View Agent Activity` | Open the agent dashboard |
| `Jeph2Sworm: View Brain Memory` | Browse Brain context store |
| `Jeph2Sworm: Pause All Agents` | Pause swarm execution |
| `Jeph2Sworm: Resume All Agents` | Resume paused agents |
| `Jeph2Sworm: View ai.env` | Open credential viewer |
| `Jeph2Sworm: Run Full Test Suite` | Trigger 120-cycle testing |
| `Jeph2Sworm: Deploy Project` | Deploy via DevOps agent |
| `Jeph2Sworm: Export Project Report` | Generate project summary |
| `Jeph2Sworm: Connect Browser Extension` | Link Chrome companion |

## Extension Settings

| Setting | Default | Description |
|---|---|---|
| `jeph2sworm.apiProvider` | `openai` | Primary LLM provider |
| `jeph2sworm.autoInstallPackages` | `true` | Auto-install npm/pip packages |
| `jeph2sworm.maxConcurrentAgents` | `6` | Max parallel agents |
| `jeph2sworm.testCycles` | `120` | Number of test cycles |
| `jeph2sworm.browserExtensionPort` | `9222` | Chrome extension port |
| `jeph2sworm.autoStart` | `false` | Auto-start backend on activation |

## Architecture

```
src/
├── extension.ts          # Entry point
├── client.ts             # WebSocket client to Python backend
├── core/                 # Orchestrator, EventBus, Brain, LLM Router, Rules Engine
├── agents/               # 7 specialized agents + base class
├── providers/            # 8 LLM provider proxies + base interface
├── views/                # Sidebar views + webview panels
├── services/             # WebSocket, Git, Browser Bridge, Token Tracker
├── utils/                # Password generator, context compressor, logger
└── types/                # TypeScript type definitions

webview-ui/               # React-based webview UI
├── src/
│   ├── components/       # Reusable UI components
│   ├── hooks/            # Custom React hooks
│   ├── stores/           # State management
│   └── styles/           # Global styles
```

## Development

```bash
npm install
npm run build            # Build extension
npm run watch            # Watch mode
npm run lint             # ESLint
npm run package          # Create .vsix
```

## License

MIT — see [LICENSE](LICENSE).
