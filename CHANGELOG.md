# Changelog

All notable changes to NiPyAPI Actions will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-01

### Added

- **GitLab CI/CD Support**: Full support for GitLab CI/CD pipelines alongside GitHub Actions
- **GitLab Flow Registry**: Support for GitLab as a flow repository (`GL_REGISTRY_TOKEN`)
- **Platform Auto-Detection**: CLI automatically detects GitHub Actions vs GitLab CI environment
- **New Commands**:
  - `purge-flowfiles` - Purge queued FlowFiles from connections
  - `export-flow-definition` - Export flow to JSON/YAML file (no registry required)
  - `import-flow-definition` - Import flow from JSON/YAML file (no registry required)
  - `list-registry-flows` - List flows available in a registry bucket
  - `get-versions` - List available versions for a deployed flow
  - `get-diff` - Check for local modifications before promotion
- **GitLab Fragments**: Reusable CLI commands via `templates/fragments.yml`
- **Comprehensive Documentation**: Platform-specific guides for GitHub Actions and GitLab CI

### Changed

- **CLI-First Architecture**: All operations now use the `nipyapi` CLI from the main client library
- **Unified Source**: CI operations moved from this repository into the main nipyapi client
- **Dependency Update**: Requires `nipyapi[cli]>=1.2.0` (was `nipyapi>=1.1.0`)
- **NiFi Version**: Tested against NiFi 2.7.2

### Breaking Changes

- Requires `nipyapi>=1.2.0` with CLI extras: `pip install "nipyapi[cli]>=1.2.0"`
- Environment variable patterns unified between platforms
- Some output variable names changed for consistency

## [1.0.0] - 2024-12-15

### Added

- Initial release with GitHub Actions support
- GitHub Flow Registry Client integration
- Core commands: ensure-registry, deploy-flow, start-flow, stop-flow, cleanup
- Parameter context management
- Version control operations (change-version, revert-flow)
- Semantic versioning test release

[2.0.0]: https://github.com/Chaffelson/nipyapi-actions/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/Chaffelson/nipyapi-actions/releases/tag/v1.0.0
