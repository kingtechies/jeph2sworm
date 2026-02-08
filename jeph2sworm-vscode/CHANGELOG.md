# Changelog

All notable changes to the Jeph2Sworm VS Code Extension will be documented in this file.

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
