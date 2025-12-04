# NiPyAPI GitHub Actions

Reusable GitHub Action for Apache NiFi CI/CD workflows using [nipyapi](https://github.com/Chaffelson/nipyapi).

## What It Does

NiPyAPI Actions enables automated testing and deployment of Apache NiFi flows using GitHub as the source of truth. It leverages NiFi 2.x's native GitHub Flow Registry Client to:

- **Store flows in Git**: Version control your NiFi flows alongside your code
- **Test on PR**: Automatically deploy and test flows when PRs are opened
- **Promote with confidence**: Same flow definition deploys to dev, staging, production

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   NiFi UI       │     │    GitHub       │     │  GitHub Actions │
│                 │     │                 │     │                 │
│  Design flows   │────▶│  Store flows    │────▶│  Test & Deploy  │
│  Export to Git  │     │  Version control│     │  to NiFi        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Commands

A single action with multiple commands for the full CI/CD lifecycle:

| Command | Description |
|---------|-------------|
| `ensure-registry` | Create or update a GitHub Flow Registry Client |
| `deploy-flow` | Deploy a versioned flow from GitHub to NiFi |
| `start-flow` | Start a deployed Process Group |
| `stop-flow` | Stop a running Process Group |
| `cleanup` | Delete a Process Group and associated resources |
| `configure-params` | Set parameter values on a parameter context |
| `get-status` | Get comprehensive status of a Process Group |

## Quick Example

```yaml
name: Test NiFi Flow

on: [pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: Chaffelson/nipyapi-actions@main
        id: registry
        with:
          command: ensure-registry
          nifi-api-endpoint: ${{ secrets.NIFI_URL }}
          nifi-username: ${{ secrets.NIFI_USERNAME }}
          nifi-password: ${{ secrets.NIFI_PASSWORD }}
          github-registry-token: ${{ secrets.GH_REGISTRY_TOKEN }}

      - uses: Chaffelson/nipyapi-actions@main
        id: deploy
        with:
          command: deploy-flow
          nifi-api-endpoint: ${{ secrets.NIFI_URL }}
          nifi-username: ${{ secrets.NIFI_USERNAME }}
          nifi-password: ${{ secrets.NIFI_PASSWORD }}
          registry-client-id: ${{ steps.registry.outputs.registry-client-id }}
          bucket: flows
          flow: my-flow

      - uses: Chaffelson/nipyapi-actions@main
        with:
          command: start-flow
          nifi-api-endpoint: ${{ secrets.NIFI_URL }}
          nifi-username: ${{ secrets.NIFI_USERNAME }}
          nifi-password: ${{ secrets.NIFI_PASSWORD }}
          process-group-id: ${{ steps.deploy.outputs.process-group-id }}

      # Your tests here

      - uses: Chaffelson/nipyapi-actions@main
        if: always()
        with:
          command: cleanup
          nifi-api-endpoint: ${{ secrets.NIFI_URL }}
          nifi-username: ${{ secrets.NIFI_USERNAME }}
          nifi-password: ${{ secrets.NIFI_PASSWORD }}
          process-group-id: ${{ steps.deploy.outputs.process-group-id }}
```

## Important: GitHub Token

NiFi's GitHub Flow Registry Client requires a **Personal Access Token (PAT)**. The automatic `GITHUB_TOKEN` does not work.

For public repositories, create a fine-grained PAT with read-only access to Contents and Metadata, scoped to your flow repository. Read-only access is sufficient for CI/CD testing with these actions. If you also want to use the same token for versioning flows directly from NiFi's UI (committing changes to GitHub), you'll need read-write access instead.

See [Security Guide](docs/security.md) for details.

## Documentation

| Guide | Description |
|-------|-------------|
| [Setup Guide](docs/setup.md) | Step-by-step setup instructions |
| [GitOps Guide](docs/gitops.md) | Feature branches, parameter handling, promotion patterns |
| [Commands Reference](docs/commands.md) | Complete command and input/output documentation |
| [How It Works](docs/how-it-works.md) | Conceptual overview and architecture |
| [Security Guide](docs/security.md) | PAT setup, secrets, and best practices |
| [Development Guide](docs/development.md) | Testing, contributing, and debugging |

## Complete Example

See [`.github/workflows/ci.yml`](.github/workflows/ci.yml) for a complete, tested workflow that:

1. Sets up NiFi infrastructure
2. Creates a GitHub Registry Client
3. Deploys a test flow
4. Validates HTTP endpoint functionality
5. Tests parameter configuration
6. Cleans up all resources

This CI workflow runs on every push and serves as the canonical usage example.

## Requirements

- Apache NiFi 2.x (GitHub Flow Registry Client support)
- nipyapi 1.1.0+ (env profile, Git registry helpers)
- Python 3.9+
- GitHub PAT with repository read access

## Related Projects

- [nipyapi](https://github.com/Chaffelson/nipyapi) - Python client for Apache NiFi
- [Apache NiFi](https://nifi.apache.org/) - Data flow automation

**Why a separate repository?** GitHub requires actions to be published from their own repository for the [GitHub Marketplace](https://docs.github.com/en/actions/sharing-automations/creating-actions/publishing-actions-in-github-marketplace). This repository contains the GitHub Action; nipyapi contains the underlying Python client library.

## License

Apache License 2.0
