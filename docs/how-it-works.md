# How NiPyAPI Actions Works

This document explains the conceptual architecture of NiFi flow CI/CD.

## The Big Picture

NiPyAPI Actions enables automated testing and deployment of Apache NiFi flows using Git as the source of truth for flow definitions.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   NiFi UI       │     │  Git Repository │     │    CI/CD        │
│                 │     │                 │     │                 │
│  Design flows   │────▶│  Store flows    │────▶│  Test & Deploy  │
│  Export to Git  │     │  Version control│     │  to NiFi        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              │
                    GitHub or GitLab
```

## Supported CI/CD Platforms

| Platform | Status | Guide |
|----------|--------|-------|
| GitHub Actions | Stable | [GitHub Actions Guide](github-actions.md) |
| GitLab CI/CD | Stable | [GitLab CI Guide](gitlab-ci.md) |

Both platforms use the same core operations and environment variables.

## Key Components

### 1. NiFi's Git Flow Registry Client

Apache NiFi 2.x includes native **Git Flow Registry Clients** that can:
- Read flow definitions directly from Git repositories
- Track versions using Git commits
- Deploy specific versions or branches to the NiFi canvas

Supported providers:
- **GitHub Flow Registry Client** - for GitHub repositories
- **GitLab Flow Registry Client** - for GitLab repositories (planned)

This is a built-in NiFi feature - no separate NiFi Registry instance is required.

### 2. Flow Storage in Git

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

### 4. CLI and CI/CD Integration

The `nipyapi` CLI provides high-level CI operations that both platforms use:

```bash
# Install the CLI
pip install "nipyapi[cli]"

# Run CI operations
nipyapi ci deploy_flow
nipyapi ci start_flow
nipyapi ci get_status
```

**GitHub Actions:**
```yaml
- uses: Chaffelson/nipyapi-actions@main
  with:
    command: deploy-flow
    bucket: flows
    flow: my-flow
```

**GitLab CI:**
```yaml
deploy-flow:
  script:
    - pip install "nipyapi[cli]"
    - nipyapi ci deploy_flow | tee outputs.env
  variables:
    NIFI_BUCKET: flows
    NIFI_FLOW: my-flow
```

The CLI auto-detects the CI environment and formats output appropriately.

## The CI/CD Workflow

### Development Flow

```
1. Developer designs flow in NiFi UI
         │
         ▼
2. Developer exports flow to Git (via NiFi's version control)
         │
         ▼
3. Developer creates PR/MR with flow changes
         │
         ▼
4. CI/CD pipeline triggers
         │
         ▼
5. Pipeline deploys flow to test NiFi instance
         │
         ▼
6. Tests run against deployed flow
         │
         ▼
7. Cleanup removes test deployment
         │
         ▼
8. PR/MR approved and merged
         │
         ▼
9. Production NiFi can pull new version
```

### What Happens During Deploy

When `deploy-flow` runs:

1. **Registry Client Setup**: Ensures a Git Flow Registry Client exists in NiFi, configured with your repository and access token

2. **Version Resolution**: NiFi's registry client queries the Git provider's API to find available versions (commits) of the specified flow

3. **Flow Import**: NiFi downloads the flow JSON and creates a Process Group on the canvas

4. **Parameter Context**: If the flow references parameters, NiFi creates the parameter context

5. **Ready for Testing**: The flow is deployed but stopped, ready to be started and tested

## Authentication

### Git Provider Token

The NiFi Git Flow Registry Client authenticates to your Git provider using a Personal Access Token (PAT):

- **GitHub**: Fine-grained PAT with read access to Contents and Metadata
- **GitLab**: Project access token with read_repository scope

### NiFi Authentication

NiPyAPI Actions authenticates to NiFi using:
- JWT bearer token
- Basic authentication (username/password)
- SSL verification (configurable)

## Relationship to Traditional NiFi Registry

**Traditional NiFi Registry:**
- Separate service that must be deployed and maintained
- Stores flows in its own database
- Requires network connectivity between NiFi and Registry

**Git Flow Registry Client:**
- Built into NiFi 2.x
- Uses Git as storage (no separate service)
- Leverages Git's versioning and branching
- Better suited for GitOps workflows

NiPyAPI Actions is designed for the Git Flow Registry Client approach. If you're using traditional NiFi Registry, see nipyapi's standard versioning functions.

## See Also

- [GitHub Actions Guide](github-actions.md) - GitHub Actions setup
- [GitLab CI Guide](gitlab-ci.md) - GitLab CI setup
- [Commands Reference](commands.md) - All commands and options
- [GitOps Guide](gitops.md) - Feature branches and promotion patterns
- [Security Guide](security.md) - Authentication and secrets
