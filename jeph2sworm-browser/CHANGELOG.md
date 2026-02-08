# Changelog

All notable changes to the Jeph2Sworm Browser Extension will be documented in this file.

## [1.0.0] — 2025-01-15

### Added

- **WebSocket Bridge**: Real-time connection to Jeph2Sworm backend server
- **Side Panel**: Live task status, activity log, and screenshot previews
- **DevTools Integration**: Network monitoring, console capture, performance metrics
- **Content Script**: DOM extraction, element highlighting, form filling, screenshot capture
- **Screen Recording**: Capture development sessions as visual evidence (MV3 compliant)
- **Accessibility Auditing**: Run a11y checks on inspected pages
- **Tab Manager**: Chrome tab lifecycle management
- **Command Queue**: Reliable command delivery with retry logic

### Fixed

- Screen recorder updated for Manifest V3 compatibility
- Message handlers properly route commands to content scripts

### Changed

- Production-ready build configuration
- Comprehensive error handling throughout

## [0.1.0] — 2025-01-01

### Added

- Initial extension scaffold
- Background service worker with WebSocket client
- Content script for DOM access
- DevTools panel with network/console monitoring
- Popup with connection status and quick actions
- Side panel with task status widget
