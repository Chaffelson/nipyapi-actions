# How NiPyAPI Actions Works

This document explains the conceptual architecture of NiFi flow CI/CD using GitHub Actions.

## The Big Picture

NiPyAPI Actions enables automated testing and deployment of Apache NiFi flows using GitHub as the source of truth for flow definitions.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   NiFi UI       │     │    GitHub       │     │  GitHub Actions │
│                 │     │                 │     │                 │
│  Design flows   │────▶│  Store flows    │────▶│  Test & Deploy  │
│  Export to Git  │     │  Version control│     │  to NiFi        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Key Components

### 1. NiFi's GitHub Flow Registry Client

Apache NiFi 2.x includes a native **GitHub Flow Registry Client** that can:
- Read flow definitions directly from GitHub repositories
- Track versions using Git commits
- Deploy specific versions or branches to the NiFi canvas

This is a built-in NiFi feature - no separate NiFi Registry instance is required.

### 2. Flow Storage in GitHub

Flows are stored as JSON files in a specific structure:

```
your-repo/
├── flows/                    # "Bucket" (folder name)
│   ├── my-flow.json          # "Flow" (filename without .json)
│   └── another-flow.json
└── production/               # Another bucket
    └── prod-flow.json
```

**How NiFi identifies flows:**

| Concept | Source |
|---------|--------|
| Bucket | Folder name (e.g., `flows`) |
| Flow ID | Filename without `.json` (e.g., `my-flow`) |
| Version | Git commit SHA |
| Version comment | Git commit message |

### 3. nipyapi Client Library

[nipyapi](https://github.com/Chaffelson/nipyapi) is a Python client for NiFi that provides:
- Connection management and authentication
- Helper functions for Git-based registries
- Process group operations (start, stop, delete)
- Parameter context management

NiPyAPI Actions uses nipyapi under the hood for all NiFi interactions.

### 4. GitHub Actions Integration

This action wraps nipyapi functionality into GitHub Actions commands:

```yaml
- uses: Chaffelson/nipyapi-actions@main
  with:
    command: deploy-flow
    bucket: flows
    flow: my-flow
```

## The CI/CD Workflow

### Development Flow

```
1. Developer designs flow in NiFi UI
         │
         ▼
2. Developer exports flow to GitHub (via NiFi's version control)
         │
         ▼
3. Developer creates PR with flow changes
         │
         ▼
4. GitHub Actions workflow triggers
         │
         ▼
5. Action deploys flow to test NiFi instance
         │
         ▼
6. Tests run against deployed flow
         │
         ▼
7. Cleanup removes test deployment
         │
         ▼
8. PR approved and merged
         │
         ▼
9. Production NiFi can pull new version
```

### What Happens During Deploy

When `deploy-flow` runs:

1. **Registry Client Setup**: Action ensures a GitHub Flow Registry Client exists in NiFi, configured with your repository and PAT

2. **Version Resolution**: NiFi's registry client queries GitHub API to find available versions (commits) of the specified flow

3. **Flow Import**: NiFi downloads the flow JSON from GitHub and creates a Process Group on the canvas

4. **Parameter Context**: If the flow references parameters, NiFi creates the parameter context

5. **Ready for Testing**: The flow is deployed but stopped, ready to be started and tested

## Authentication

### GitHub PAT Requirement

The NiFi GitHub Flow Registry Client authenticates to GitHub using a Personal Access Token (PAT). This is required because:

- NiFi needs to call GitHub's API to list and download flows
- The automatic `GITHUB_TOKEN` provided by Actions doesn't work (it's an app token, not a user token)
- A fine-grained PAT with read-only access is recommended

### NiFi Authentication

The action authenticates to NiFi using:
- Basic authentication (username/password)
- SSL verification (configurable)

## Relationship to Traditional NiFi Registry

**Traditional NiFi Registry:**
- Separate service that must be deployed and maintained
- Stores flows in its own database
- Requires network connectivity between NiFi and Registry

**GitHub Flow Registry Client:**
- Built into NiFi 2.x
- Uses GitHub as storage (no separate service)
- Leverages Git's versioning and branching
- Better suited for GitOps workflows

NiPyAPI Actions is designed for the GitHub Flow Registry Client approach. If you're using traditional NiFi Registry, see nipyapi's standard versioning functions.

## Next Steps

- [Setup Guide](setup.md) - Get started with NiPyAPI Actions
- [GitOps Guide](gitops.md) - Feature branches, parameters, and promotion patterns
- [Commands Reference](commands.md) - Detailed command documentation
- [Security Guide](security.md) - PAT setup and best practices
