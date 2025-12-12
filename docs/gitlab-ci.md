# GitLab CI Guide

Setup and usage for NiPyAPI Actions with GitLab CI/CD.

## Prerequisites

- Apache NiFi 2.x running and accessible from GitLab runners
- Personal Access Token for your flow repository (GitHub or GitLab)
- GitLab CI/CD enabled on your project

## Quick Start

The simplest approach is to use the `nipyapi` CLI directly in your pipeline:

```yaml
deploy-to-nifi:
  image: python:3.11
  before_script:
    - pip install -q "nipyapi[cli] @ git+https://github.com/Chaffelson/nipyapi.git@feature/cli"
  script:
    - nipyapi ci ensure_registry | tee outputs.env
    - export $(grep -v '^#' outputs.env | xargs)
    - nipyapi ci deploy_flow
    - nipyapi ci start_flow
  variables:
    NIFI_API_ENDPOINT: $NIFI_API_ENDPOINT
    NIFI_USERNAME: $NIFI_USERNAME
    NIFI_PASSWORD: $NIFI_PASSWORD
    GH_REGISTRY_TOKEN: $GH_REGISTRY_TOKEN
    NIFI_REGISTRY_REPO: "your-org/your-flows-repo"
    NIFI_BUCKET: "flows"
    NIFI_FLOW: "my-flow"
```

## Using Fragments (Reusable Commands)

Include the fragments file to get pre-defined CLI commands:

```yaml
include:
  - remote: 'https://raw.githubusercontent.com/nipyapi/nipyapi-actions/main/templates/fragments.yml'

deploy-to-nifi:
  image: python:3.11
  before_script:
    - !reference [.nipyapi, setup]
  script:
    - !reference [.nipyapi, ensure-registry]
    - !reference [.nipyapi, deploy-flow]
    - !reference [.nipyapi, start-flow]
```

## Configure CI/CD Variables

In GitLab: **Settings** > **CI/CD** > **Variables**, add:

| Variable | Description |
|----------|-------------|
| `NIFI_API_ENDPOINT` | NiFi API URL (e.g., `https://nifi:8443/nifi-api`) |
| `NIFI_USERNAME` | NiFi username |
| `NIFI_PASSWORD` | NiFi password |
| `NIFI_BEARER_TOKEN` | JWT bearer token (alternative to username/password) |
| `GH_REGISTRY_TOKEN` | GitHub PAT (if flows are in GitHub) |
| `GL_REGISTRY_TOKEN` | GitLab PAT (if flows are in GitLab) |

Set one of `GH_REGISTRY_TOKEN` or `GL_REGISTRY_TOKEN` depending on where your flows are stored. The provider is auto-detected from which token is available.

## Environment Variables

### Connection

| Variable | Required | Description |
|----------|----------|-------------|
| `NIFI_API_ENDPOINT` | Yes | NiFi API URL |
| `NIFI_USERNAME` | No | Basic auth username |
| `NIFI_PASSWORD` | No | Basic auth password |
| `NIFI_BEARER_TOKEN` | No | JWT bearer token (alternative to username/password) |
| `NIFI_VERIFY_SSL` | No | Verify SSL (default: true) |

### Operations

| Variable | Description |
|----------|-------------|
| `NIFI_PROCESS_GROUP_ID` | Target process group ID |
| `NIFI_REGISTRY_CLIENT_ID` | Registry client ID |
| `NIFI_BUCKET` | Bucket/folder name |
| `NIFI_FLOW` | Flow name |
| `NIFI_TARGET_VERSION` | Version (commit SHA, tag, or branch) |
| `NIFI_PARAMETERS` | JSON object of parameters to set |

## Output Variables

The CLI outputs in dotenv format when running in GitLab CI:

| Output | Description |
|--------|-------------|
| `REGISTRY_CLIENT_ID` | Registry client ID |
| `PROCESS_GROUP_ID` | Deployed process group ID |
| `PROCESS_GROUP_NAME` | Process group name |
| `DEPLOYED_VERSION` | Version that was deployed |

Capture outputs with: `nipyapi ci <command> | tee -a outputs.env`

Load into shell with: `export $(grep -v '^#' outputs.env | xargs)`

## Pipeline Patterns

### Multi-Job Pattern (External NiFi)

Use separate jobs when connecting to an external NiFi instance:

```yaml
stages:
  - deploy
  - test
  - cleanup

deploy-flow:
  stage: deploy
  image: python:3.11
  before_script:
    - pip install -q "nipyapi[cli] @ git+https://github.com/Chaffelson/nipyapi.git@feature/cli"
  script:
    - nipyapi ci deploy_flow | tee outputs.env
  artifacts:
    reports:
      dotenv: outputs.env  # GitLab auto-injects into downstream jobs

start-flow:
  stage: test
  needs:
    - job: deploy-flow
      artifacts: true  # PROCESS_GROUP_ID automatically available
  image: python:3.11
  before_script:
    - pip install -q "nipyapi[cli] @ git+https://github.com/Chaffelson/nipyapi.git@feature/cli"
  script:
    - nipyapi ci start_flow
```

### Single-Job Pattern (Docker-in-Docker)

Use a single job when running NiFi as a Docker container within the pipeline:

```yaml
test-all:
  stage: test
  image: docker:24
  services:
    - docker:24-dind
  variables:
    DOCKER_HOST: tcp://docker:2376
  before_script:
    - apk add --no-cache python3 py3-pip
    - pip install --break-system-packages "nipyapi[cli] @ git+https://github.com/Chaffelson/nipyapi.git@feature/cli"
  script:
    # Start NiFi infrastructure
    - docker-compose up -d nifi
    # ... wait for NiFi to be ready ...

    # Run operations sequentially
    - nipyapi ci deploy_flow | tee outputs.env
    - export $(grep -v '^#' outputs.env | xargs)
    - nipyapi ci start_flow

  after_script:
    - docker-compose down
```

### Choosing a Pattern

| Scenario | Pattern | Reason |
|----------|---------|--------|
| Production deployment | Multi-job | Granular visibility, external NiFi |
| CI testing with DinD | Single-job | Container persistence required |
| Self-hosted runner | Either | Depends on your infrastructure |

## Local Testing

Test your pipeline locally with `gitlab-ci-local`:

```bash
# Install
brew install gitlab-ci-local

# Run single job
gitlab-ci-local --job deploy-flow

# Run full pipeline
gitlab-ci-local
```

Note: Use `host.docker.internal` instead of `localhost` for `NIFI_API_ENDPOINT` when testing locally with Docker.

## Troubleshooting

### "Client does not have read access to the repository"

This error when using GitLab Flow Registry can be misleading. While it suggests a permissions issue, it may actually indicate:

1. **Token rate limiting** - GitLab trial/free accounts may have undocumented API rate limits
2. **Token invalidation** - The token may have been invalidated for security reasons
3. **Account restrictions** - Trial accounts may have restrictions that aren't documented

**Resolution**: Try creating a new Personal Access Token with the same scopes.

### GitLab Token Requirements

GitLab Flow Registry requires more permissive token scopes than GitHub:

| Setting | Requirement |
|---------|-------------|
| Role | Developer or higher (not Guest) |
| Scopes | `api`, `read_repository`, `write_repository` |

The `api` scope is required because NiFi uses GitLab's REST API to browse repository contents.

## See Also

- [Commands Reference](commands.md) - All commands and options
- [How It Works](how-it-works.md) - Architecture overview
- [Security Guide](security.md) - PAT setup and best practices
