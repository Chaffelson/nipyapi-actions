# NiPyAPI Actions

CI/CD automation for Apache NiFi flows using [nipyapi](https://github.com/Chaffelson/nipyapi).

## Supported Platforms

| Platform | Status | Guide |
|----------|--------|-------|
| GitHub Actions | Stable | [GitHub Actions Guide](docs/github-actions.md) |
| GitLab CI/CD | Stable | [GitLab CI Guide](docs/gitlab-ci.md) |
| Azure Pipelines | Stable | [Azure Pipelines Guide](docs/azure-pipelines.md) |

## What It Does

Automates testing and deployment of Apache NiFi flows using Git as the source of truth:

- **Store flows in Git**: Version control your NiFi flows alongside your code
- **Test on PR/MR**: Automatically deploy and test flows when changes are proposed
- **Promote with confidence**: Same flow definition deploys to dev, staging, production

## Commands

| Command | Description |
|---------|-------------|
| `ensure-registry` | Create or update a Git Flow Registry Client |
| `deploy-flow` | Deploy a versioned flow from Git registry to NiFi |
| `start-flow` | Start a deployed Process Group |
| `stop-flow` | Stop a running Process Group |
| `change-version` | Change to a different version (tag or SHA) |
| `revert-flow` | Revert local modifications |
| `cleanup` | Delete a Process Group |
| `configure-params` | Set parameter values |
| `get-status` | Get comprehensive status |
| `list-registry-flows` | List flows available in a registry bucket |
| `get-versions` | List available versions for a deployed flow |
| `get-diff` | Check for local modifications before promotion |
| `purge-flowfiles` | Purge queued FlowFiles from connections |
| `export-flow-definition` | Export a flow to JSON/YAML file (no registry required) |
| `import-flow-definition` | Import a flow from JSON/YAML file (no registry required) |

## Quick Start

### GitHub Actions

```yaml
- uses: Chaffelson/nipyapi-actions@main
  with:
    command: deploy-flow
    nifi-api-endpoint: ${{ secrets.NIFI_URL }}
    nifi-bearer-token: ${{ secrets.NIFI_BEARER_TOKEN }}  # or use nifi-username/nifi-password
    registry-client-id: ${{ steps.registry.outputs.registry-client-id }}
    bucket: flows
    flow: my-flow
```

See [GitHub Actions Guide](docs/github-actions.md) for complete setup.

### GitLab CI/CD

```yaml
deploy-flow:
  image: python:3.11
  script:
    - pip install "nipyapi[cli]>=1.2.0"
    - nipyapi ci deploy_flow | tee outputs.env
  variables:
    NIFI_API_ENDPOINT: $NIFI_URL
    NIFI_BEARER_TOKEN: $NIFI_TOKEN  # or use NIFI_USERNAME/NIFI_PASSWORD
    NIFI_BUCKET: flows
    NIFI_FLOW: my-flow
  artifacts:
    reports:
      dotenv: outputs.env
```

See [GitLab CI Guide](docs/gitlab-ci.md) for complete setup.

### Azure Pipelines

```yaml
variables:
  - group: nipyapi-ado          # service principal creds (NIFI_ADO_*)
steps:
  - script: nipyapi ci ensure_registry
    name: registry
    env:
      NIFI_ADO_CLIENT_SECRET: $(NIFI_ADO_CLIENT_SECRET)
  - script: nipyapi ci deploy_flow
    env:
      NIFI_REGISTRY_CLIENT_ID: $(registry.registry_client_id)
      NIFI_BUCKET: flows
      NIFI_FLOW: my-flow
```

Azure DevOps uses NiFi's service-principal-based Azure DevOps Flow Registry
Client and reads flows from an Azure Repos Git repo. See
[Azure Pipelines Guide](docs/azure-pipelines.md) for complete setup.

## Requirements

- Apache NiFi 2.x with Git-based Flow Registry Client (tested against NiFi 2.7.2; Azure DevOps registry client requires 2.10.0+)
- nipyapi 1.2.0+ with CLI (`pip install "nipyapi[cli]"`)
- Python 3.9+
- A credential for your Git provider: a Personal Access Token (GitHub or GitLab) or a service principal (Azure DevOps)

## Documentation

| Guide | Description |
|-------|-------------|
| [GitHub Actions Guide](docs/github-actions.md) | Setup and usage for GitHub Actions |
| [GitLab CI Guide](docs/gitlab-ci.md) | Setup and usage for GitLab CI/CD |
| [Azure Pipelines Guide](docs/azure-pipelines.md) | Setup and usage for Azure DevOps Pipelines |
| [Commands Reference](docs/commands.md) | All commands and options |
| [How It Works](docs/how-it-works.md) | Architecture overview |
| [GitOps Guide](docs/gitops.md) | Feature branches and promotion patterns |
| [Security Guide](docs/security.md) | PAT setup and best practices |
| [Changelog](CHANGELOG.md) | Version history and release notes |

## License

Apache License 2.0
