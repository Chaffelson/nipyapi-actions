# Agent Instructions for nipyapi-actions

## Architecture: CLI-First

This repository provides examples for consuming the `nipyapi` CLI in CI/CD pipelines.
All NiFi operations are handled by the `nipyapi` Python client, exposed via CLI.

## Quick Reference

```bash
# Development
make gitlab-test           # Run GitLab CI setup test
make gitlab-test-all       # Run full GitLab CI pipeline (requires NiFi)
make test-act              # Run GitHub Actions locally

# Infrastructure
make infra-up              # Start NiFi
make infra-down            # Stop NiFi
make infra-ready           # Wait for NiFi
```

## Repository Structure

```
nipyapi-actions/
├── templates/
│   └── fragments.yml      # Reusable CLI commands for GitLab CI
├── action.yml             # GitHub Actions definition (uses nipyapi CLI)
├── .gitlab-ci.yml         # GitLab CI example (uses nipyapi CLI)
└── docs/                  # Platform-specific guides
```

## CLI Usage

Both platforms use the `nipyapi` CLI directly:

```bash
# Install CLI
pip install "nipyapi[cli] @ git+https://github.com/Chaffelson/nipyapi.git@feature/cli"

# Run operations (auto-detects CI environment)
nipyapi ci ensure_registry
nipyapi ci deploy_flow
nipyapi ci start_flow
```

The CLI:
- Auto-detects GitHub Actions or GitLab CI environment
- Outputs in appropriate format (GitHub: key=value, GitLab: dotenv)
- Reads configuration from environment variables

## Available CI Operations

All operations are in `nipyapi.ci`:

- `ensure_registry` - Create/update Git Flow Registry Client
- `deploy_flow` - Deploy flow from registry to canvas
- `start_flow` - Enable controllers and start processors
- `stop_flow` - Stop processors and disable controllers
- `get_status` - Get comprehensive status information
- `configure_params` - Set parameter values
- `change_version` - Change to specific version or latest
- `revert_flow` - Revert uncommitted local changes
- `cleanup` - Stop and delete process group

## GitLab Fragments

Users can include `templates/fragments.yml` to get reusable CLI commands:

```yaml
include:
  - remote: 'https://raw.githubusercontent.com/nipyapi/nipyapi-actions/main/templates/fragments.yml'

my-job:
  image: python:3.11
  before_script:
    - !reference [.nipyapi, setup]
  script:
    - !reference [.nipyapi, ensure-registry]
    - !reference [.nipyapi, deploy-flow]
```

**Important:** The fragments in `templates/fragments.yml` must be kept in sync with
the `.gitlab-ci.yml` test pipeline, which validates that all operations work correctly.

## Local CI Testing

```bash
# GitLab CI (requires Docker)
gitlab-ci-local --job test-setup

# GitHub Actions (requires Docker + act)
make test-act
```
