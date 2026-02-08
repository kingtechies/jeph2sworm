<p align="center">
  <img src="https://raw.githubusercontent.com/kingtechies/jeph2sworm/main/assets/logo.png" alt="Jeph2Sworm Logo" width="200" />
</p>

<h1 align="center">Jeph2Sworm</h1>

<p align="center">
  <strong>From idea to production. Automatically.</strong>
</p>

<p align="center">
  <a href="https://github.com/kingtechies/jeph2sworm/stargazers">
    <img src="https://img.shields.io/github/stars/kingtechies/jeph2sworm?style=for-the-badge" alt="Stars" />
  </a>
  <a href="https://github.com/kingtechies/jeph2sworm/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/kingtechies/jeph2sworm?style=for-the-badge" alt="License" />
  </a>
  <a href="https://github.com/kingtechies/jeph2sworm/issues">
    <img src="https://img.shields.io/github/issues/kingtechies/jeph2sworm?style=for-the-badge" alt="Issues" />
  </a>
</p>

---

## What is Jeph2Sworm?

Jeph2Sworm is an autonomous AI development swarm that transforms a single product idea into a fully built, tested, and deployed software application.

You describe your idea. The swarm does everything else.

No prompting fatigue. No context loss. No half-built projects. No wasted tokens.

The system is composed of three tightly integrated components:

| Component | Description |
|-----------|-------------|
| **VS Code Extension** | AI chat sidebar with a multi-agent swarm that writes, builds, tests, and deploys your entire project |
| **Chrome Extension** | AI-controlled browser for live testing, screenshots, screen recording, DevTools access, and GUI interaction |
| **Python Backend** | Multi-agent orchestration engine with shared memory, LLM routing, and a rules-based safety layer |

<p align="center">
  <img src="https://raw.githubusercontent.com/kingtechies/jeph2sworm/main/assets/logo.png" alt="Jeph2Sworm" width="120" />
</p>

---

## How It Works

1. **You describe your idea** -- "Build me a social media app like Facebook"
2. **The Project Manager asks clarifying questions** -- name, features, audience, tech preferences
3. **The Brain designs the architecture** -- tech stack, folder structure, database schema, API contracts
4. **You approve the plan** -- or modify it
5. **The swarm activates** -- all agents work simultaneously in real time
6. **You watch the magic** -- agents write code, install packages, deploy, and test -- all visible in a live feed
7. **120 test cycles run** -- unit, integration, E2E, edge cases, and regression, with screenshot evidence
8. **Done means done** -- deployed, tested, documented, credentials secured

---

## The Agent Swarm

Seven specialized AI agents work in parallel, communicating through a shared Brain and real-time event bus. No agent waits for another. They all execute simultaneously and coordinate through shared memory.

| Role | Responsibility |
|------|----------------|
| **Project Manager** | Gathers requirements, breaks project into milestones, assigns tasks, communicates with the user |
| **Brain / Architect** | Designs system architecture, chooses tech stack, defines API contracts, resolves technical conflicts |
| **Backend Developer** | Implements APIs, database, authentication, business logic. Sends endpoint contracts to Frontend and DevOps |
| **Frontend Developer** | Implements UI components, state management, routing. Consumes API contracts and design specs |
| **UI/UX Designer** | Creates design system, page layouts, component specs. Can use browser-based design tools via Chrome extension |
| **Tester / QA** | Writes and runs 120+ test cycles. Tests live in the browser. Produces screenshot and recording evidence |
| **DevOps Engineer** | Sets up Docker, CI/CD, hosting, environment variables, DNS, SSL, monitoring. Deploys the application |



---

## Key Features

### Autonomous Multi-Agent Execution
All agents work at the same time. The backend developer sends API endpoints to the frontend developer while the DevOps engineer configures the server and the tester writes tests -- all happening in parallel.

### Shared Brain (Zero Context Loss)
A central memory system stores the project spec, architecture decisions, task board, API contracts, agent states, error logs, and conversation history. Every agent reads from and writes to this shared Brain. Nothing is forgotten.

### Full File System and Terminal Access
Agents create files, install packages, run servers, execute database migrations, and commit to Git -- without asking for permission on every action. The user grants access once and the swarm operates freely within safety rules.

### 120-Cycle Testing with Proof
The Tester agent runs 120 test cycles across five categories: unit tests (runs 1-30), integration tests (31-60), end-to-end browser tests (61-90), edge case tests (91-110), and final regression (111-120). Every run produces evidence: screenshots, recordings, logs, and coverage reports. "Done" means all 120 runs pass with zero failures.

### AI-Controlled Browser (Powered by browser-use)
The Chrome extension gives agents real browser access. They navigate pages, click elements, fill forms, take screenshots, record screen, read DevTools console and network tabs, download assets, and interact with GUI design tools. Testing happens on the live deployed site, not just with curl commands.

Built on top of [browser-use](https://github.com/kingtechies/browser-use) for browser automation.

### Mobile Development (Powered by Maestro)
Mobile app testing and automation powered by [Maestro](https://github.com/kingtechies/Maestro), enabling the swarm to build, test, and validate mobile applications with the same rigor as web projects.

### Secure Credential Management (ai.env)
Every password, secret, and API key generated during development is stored in a single `ai.env` file. Generated passwords are 32+ characters with 128-bit entropy -- comparable to a bitcoin address. The file is auto-added to `.gitignore`, viewable in the VS Code extension (masked by default), and never hardcoded in source files.

### Multi-Provider LLM Support
Connect your preferred AI provider. The LLM Router selects the best model for each task type and falls back to alternatives if a provider fails.

| Provider | Models |
|----------|--------|
| OpenAI | GPT-4o, GPT-4.1, o3 |
| Anthropic | Claude Opus 4, Claude Sonnet 4 |
| xAI | Grok-3 |
| Google | Gemini 2.0 Pro, Gemini 2.5 |
| DeepSeek | DeepSeek-V3, DeepSeek-R1 |
| Mistral | Mistral Large, Codestral |
| Meta | Llama 4 (via Together/Groq) |
| Cohere | Command R+ |

### Safety Rules Engine
Eight hard-coded rules that cannot be overridden:

1. Never delete user data or system files
2. Never corrupt the project (auto-backup before every write)
3. No hallucination in critical paths (all imports, URLs, and APIs are verified)
4. Stay in scope (no file access outside workspace)
5. Transparent operations (every action logged and auditable)
6. Credential security (128-bit entropy, never hardcoded)
7. No data exfiltration (code never sent to unauthorized services)
8. Graceful failure (retry, escalate, never crash silently)

---

## Architecture Overview

```
                         USER
                          |
          +---------------+---------------+
          |                               |
  +-------v--------+          +----------v----------+
  | VS CODE EXT    |<-------->| CHROME EXTENSION    |
  | Chat Sidebar   | WebSocket| Browser Control     |
  | Agent Dashboard|          | Screenshots         |
  | Progress View  |          | Screen Recording    |
  | File Changes   |          | DevTools Access     |
  +-------+--------+          +----------+----------+
          |                               |
          +---------------+---------------+
                          |
              +-----------v-----------+
              |   JEPH2SWORM-CORE     |
              |   (Python Backend)    |
              |                       |
              |  Orchestrator         |
              |  Brain (Shared Memory)|
              |  Agent Swarm (7)      |
              |  LLM Router           |
              |  Rules Engine         |
              |  Event Bus            |
              +-----------+-----------+
                          |
          +---------------+---------------+
          |               |               |
  +-------v------+ +-----v-------+ +-----v--------+
  | File System  | | Terminal    | | browser-use  |
  | Read/Write   | | Exec Cmds  | | Web Control  |
  +--------------+ +-------------+ +--------------+
```

---

## Project Structure

```
jeph2sworm/
|
|-- jeph2sworm-vscode/        # VS Code Extension (TypeScript + React)
|   |-- src/
|   |   |-- extension.ts      # Entry point
|   |   |-- core/             # Orchestrator, event bus, brain client
|   |   |-- agents/           # Agent implementations
|   |   |-- providers/        # LLM provider integrations
|   |   |-- views/            # Sidebar, panels, components
|   |   |-- services/         # WebSocket, Git, browser bridge
|   |   +-- types/            # TypeScript type definitions
|   +-- webview-ui/           # React webview app
|
|-- jeph2sworm-browser/       # Chrome Extension (TypeScript + React)
|   |-- src/
|   |   |-- manifest.json     # Manifest V3
|   |   |-- background/       # Service worker, WebSocket client
|   |   |-- content/          # Content scripts, DOM extraction
|   |   |-- devtools/         # DevTools panel, network monitor
|   |   |-- sidepanel/        # Side panel UI
|   |   |-- recorder/         # Screen recording
|   |   +-- types/            # Type definitions
|   +-- public/               # Icons, styles
|
|-- jeph2sworm-core/          # Python Backend (FastAPI)
|   |-- jeph2sworm/
|   |   |-- main.py           # FastAPI entry point
|   |   |-- orchestrator/     # Swarm manager, task scheduler
|   |   |-- agents/           # Agent implementations
|   |   |-- brain/            # Memory, RAG, vector store
|   |   |-- llm/              # Multi-provider LLM router
|   |   |-- tools/            # File system, terminal, credentials
|   |   |-- browser/          # browser-use bridge, screenshots
|   |   |-- events/           # Event bus
|   |   +-- security/         # Rules engine, action validator
|   +-- tests/                # Test suite
|
+-- assets/                   # Images, branding
```

---

## Getting Started

### Prerequisites

- VS Code 1.85 or later
- Python 3.11 or later
- Node.js 18 or later
- Google Chrome (for browser extension)
- An API key from at least one supported LLM provider

### Installation

1. Install the VS Code extension from the Marketplace:

   Search for "Jeph2Sworm" in the VS Code Extensions panel.

2. Open the extension sidebar and complete the setup wizard:

   - Connect your LLM provider and API key
   - Optionally provide your machine password for package installation
   - Optionally install the Chrome extension companion

3. Start a new project:

   - Click "Start New Project" in the sidebar
   - Describe your idea
   - Answer the clarifying questions
   - Approve the plan
   - Watch it build

### Chrome Extension (Optional)

Install "Jeph2Sworm Browser" from the Chrome Web Store to enable:

- Live website testing
- Screenshot and screen recording
- DevTools data capture
- GUI tool interaction
- Asset downloading

---

## Real-Time Agent Communication

All agents communicate through a central event bus. Every action is visible in the VS Code sidebar as a live feed:

```
[10:30] Backend Dev:  Auth API complete -- POST /api/auth/login ready
[10:30] Frontend Dev: Connecting login form to /api/auth/login
[10:31] Tester:       Writing auth endpoint tests
[10:31] DevOps:       Added JWT_SECRET to environment config
[10:32] UX Designer:  Login page design ready -- sending to Frontend
[10:33] Tester:       Auth tests passing (12/12)
[10:34] DevOps:       Deployed to staging -- https://app.example.com
[10:35] Tester:       Running E2E login flow on live site
```

---

## The ai.env File

Every credential generated during development is stored in a single secure file:

```
# ================================================
# ai.env -- Auto-generated by Jeph2Sworm
# ================================================
# WARNING: This file contains sensitive credentials
# DO NOT commit to version control
# ================================================

DB_PASSWORD=kX9#mQ$vL2@nR7!pW4&jY6*cF8^hT3xZ1
JWT_SECRET=aB3$dE5&gH7*jK9!mN1@pQ3#sU5^wY7zR2
ADMIN_PASSWORD=qW8#eR0$tY2&uI4*oP6!aS8@dF0#gH2bN4
```

All passwords are 32+ characters with 128-bit entropy. No dictionary words. No sequential characters. No reuse.

---

## Supported Integrations

| Category | Tools |
|----------|-------|
| **Browser Automation** | [browser-use](https://github.com/kingtechies/browser-use) |
| **Mobile Testing** | [Maestro](https://github.com/kingtechies/Maestro) |
| **Deployment** | Vercel, Railway, AWS, Netlify, DigitalOcean |
| **Databases** | PostgreSQL, MySQL, MongoDB, SQLite, Redis |
| **Frontend** | React, Next.js, Vue, Svelte, Angular |
| **Backend** | Node.js, Python/FastAPI, Go, Ruby on Rails |
| **Mobile** | React Native, Flutter |
| **CI/CD** | GitHub Actions, Docker |
| **Version Control** | Git (auto-commit at milestones) |

---

## Contributing

Contributions are welcome. Please read the contributing guidelines before submitting a pull request.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Links

- [GitHub Repository](https://github.com/kingtechies/jeph2sworm)
- [browser-use](https://github.com/kingtechies/browser-use)
- [Maestro](https://github.com/kingtechies/Maestro)
- [Report Issues](https://github.com/kingtechies/jeph2sworm/issues)

---

<p align="center">
  <img src="https://raw.githubusercontent.com/kingtechies/jeph2sworm/main/assets/logo.png" alt="Jeph2Sworm Logo" width="100" />
</p>

<p align="center">
  <strong>Jeph2Sworm</strong><br/>
  From idea to production. Automatically.<br/>
  Built by <a href="https://github.com/kingtechies">kingtechies</a>
</p>
