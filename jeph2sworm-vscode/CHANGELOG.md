# Changelog

All notable changes to the Jeph2Sworm VS Code Extension will be documented in this file.

## [1.0.1] — 2025-01-15

### Changed

- Added author information and portfolio link (jephthahameh.cfd)
- Updated homepage to author portfolio

## [1.0.0] — 2025-01-15

### Added

- **120-Cycle Test Runner**: Run tests 120 times to catch flaky tests and race conditions
- **Browser E2E Integration**: Tester agent can now run browser-based E2E tests via Chrome extension
- **Credential Rotation Service**: Automated credential lifecycle management with scheduled rotation
- **Visual Regression Testing**: Compare pages against design specs with screenshot evidence
- **RAG-Powered Context**: Vector store integration for intelligent context retrieval
- **Complete SwarmManager wiring**: All components (VectorStore, BrowserBridge, ContextManager) connected

### Fixed

- VectorStore now uses ChromaDB's PersistentClient API
- BrowserController/BrowserUseBridge properly use LLM instances
- Agent context manager wiring in SwarmManager

### Changed

- All 132 tests passing
- Production-ready build configuration

## [0.1.0] — 2025-01-01

### Added

- Initial extension scaffold with activation, client, and core modules.
- **Agents**: Base agent + 7 role-specific agents (PM, Brain, Backend, Frontend, UX, Tester, DevOps).
- **Providers**: 8 LLM provider proxies (OpenAI, Anthropic, Grok, Gemini, DeepSeek, Mistral, LLaMA, Cohere) + base provider interface.
- **Core**: Orchestrator, EventBus, BrainClient, LLM Router, Rules Engine, File/Terminal/Credential managers.
- **Services**: WebSocket, BrowserBridge, Git, TokenTracker, Backup.
- **Views**: Chat sidebar, Agent tree, Task tree, Event feed, FileChangeLog, SetupWizard.
- **Panels**: AgentConversation, TestDashboard, DeployStatus, AiEnvViewer, BrainViewer.
- **Webview-UI**: React-based ChatPanel, AgentDashboard, ProgressView, and reusable components.
- **Types**: Agent, Brain, Event, LLM, Project type definitions.
- **Utils**: PasswordGenerator, ContextCompressor, Logger, Validators.
