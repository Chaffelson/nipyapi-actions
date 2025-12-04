# Commands Reference

Complete reference for all NiPyAPI Actions commands.

## Common Inputs

These inputs are common to all commands:

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `command` | Yes | | The command to execute |
| `nifi-api-endpoint` | Yes | | NiFi API endpoint URL (e.g., `https://nifi:8443/nifi-api`) |
| `nifi-username` | No | | NiFi username for basic authentication |
| `nifi-password` | No | | NiFi password for basic authentication |
| `nifi-verify-ssl` | No | `true` | Whether to verify SSL certificates |
| `nipyapi-suppress-ssl-warnings` | No | `false` | Suppress SSL warning messages |

---

## ensure-registry

Create or update a GitHub Flow Registry Client in NiFi.

### Description

This command ensures a GitHub Flow Registry Client exists in NiFi with the specified configuration. If a client with the same name exists, it will be updated with the new settings.

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `registry-client-name` | No | `GitHub-FlowRegistry` | Name for the registry client |
| `github-registry-token` | **Yes** | | GitHub PAT for repository access |
| `github-registry-repo` | No | `github.repository` | Repository in `owner/repo` format |
| `github-registry-branch` | No | `main` | Default branch for the client |
| `repository-path` | No | repo root | Path within repo to use as root (omit to use repository root) |
| `github-api-url` | No | `https://api.github.com/` | GitHub API URL (for GitHub Enterprise) |

### Understanding Repository Path, Bucket, and Flow

The registry client uses a layered path structure to locate flows:

```
repository-path / bucket / flow.json
```

| Setting | What it represents | Example |
|---------|-------------------|---------|
| `repository-path` | Base directory within the repo (set on registry client) | `nifi-flows` |
| `bucket` | Folder under the base path (used in `deploy-flow`) | `production` |
| `flow` | Flow filename without `.json` (used in `deploy-flow`) | `my-pipeline` |

**Example 1: Flows at repository root**

```
my-repo/
└── production/          # bucket: "production"
    └── my-flow.json     # flow: "my-flow"
```

```yaml
# repository-path not specified (defaults to repo root)
- uses: Chaffelson/nipyapi-actions@main
  with:
    command: ensure-registry
    # ... other inputs, no repository-path
```

Then deploy with `bucket: production` and `flow: my-flow`.

**Example 2: Flows in a subdirectory**

```
my-repo/
└── nifi-flows/          # repository-path: "nifi-flows"
    └── production/      # bucket: "production"
        └── my-flow.json # flow: "my-flow"
```

```yaml
- uses: Chaffelson/nipyapi-actions@main
  with:
    command: ensure-registry
    repository-path: nifi-flows  # Set base path
    # ... other inputs
```

Then deploy with `bucket: production` and `flow: my-flow`.

**Default behavior**: If you omit `repository-path` entirely, the repository root is used as the base path. You do not need to explicitly set it to an empty string.

### Outputs

| Output | Description |
|--------|-------------|
| `registry-client-id` | UUID of the registry client |
| `registry-client-name` | Name of the registry client |
| `success` | `true` if successful |

### Example

```yaml
- uses: Chaffelson/nipyapi-actions@main
  id: registry
  with:
    command: ensure-registry
    nifi-api-endpoint: ${{ secrets.NIFI_URL }}
    nifi-username: ${{ secrets.NIFI_USERNAME }}
    nifi-password: ${{ secrets.NIFI_PASSWORD }}
    github-registry-token: ${{ secrets.GH_REGISTRY_TOKEN }}
    registry-client-name: my-github-registry
    github-registry-repo: myorg/my-flows
    github-registry-branch: main
```

---

## deploy-flow

Deploy a versioned flow from the GitHub registry to the NiFi canvas.

### Description

Deploys a flow from GitHub to NiFi as a new Process Group. The flow is deployed in a stopped state - use `start-flow` to begin processing.

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `registry-client-id` | Yes | | Registry client ID (from `ensure-registry`) |
| `bucket` | Yes | | Bucket (folder) containing the flow |
| `flow` | Yes | | Flow name (filename without `.json`) |
| `branch` | No | _auto-detect_ | Branch to deploy from |
| `version` | No | _latest_ | Specific version (commit SHA) to deploy |
| `parent-process-group-id` | No | _root_ | Parent Process Group ID |
| `location-x` | No | `0` | X coordinate on canvas |
| `location-y` | No | `0` | Y coordinate on canvas |

**Note**: The `bucket` and `flow` values combine with the registry client's `repository-path` to form the full path: `repository-path/bucket/flow.json`. See the [ensure-registry](#ensure-registry) section for details.

### Branch Auto-Detection

If `branch` is not specified:
- For pull requests: Uses `github.head_ref` (source branch)
- For pushes: Uses `github.ref_name` (current branch)

### Outputs

| Output | Description |
|--------|-------------|
| `process-group-id` | UUID of the deployed Process Group |
| `process-group-name` | Name of the deployed Process Group |
| `deployed-version` | Version (commit SHA) that was deployed |
| `success` | `true` if successful |

### Example

```yaml
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
    version: abc123def  # Optional: specific commit
```

---

## start-flow

Start a deployed Process Group.

### Description

Enables controller services and starts all processors in a Process Group. The flow must be deployed before it can be started.

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `process-group-id` | Yes | | Process Group ID to start |
| `enable-controllers` | No | `true` | Enable controller services before starting processors |

### Outputs

| Output | Description |
|--------|-------------|
| `started` | `true` if the process group was started |
| `process-group-name` | Name of the started process group |
| `message` | Status message |
| `success` | `true` if successful |

### Example

```yaml
- uses: Chaffelson/nipyapi-actions@main
  with:
    command: start-flow
    nifi-api-endpoint: ${{ secrets.NIFI_URL }}
    nifi-username: ${{ secrets.NIFI_USERNAME }}
    nifi-password: ${{ secrets.NIFI_PASSWORD }}
    process-group-id: ${{ steps.deploy.outputs.process-group-id }}
```

---

## stop-flow

Stop a running Process Group.

### Description

Stops all processors and optionally disables controller services in a Process Group.

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `process-group-id` | Yes | | Process Group ID to stop |
| `disable-controllers` | No | `true` | Disable controller services after stopping processors |

### Outputs

| Output | Description |
|--------|-------------|
| `stopped` | `true` if the process group was stopped |
| `process-group-name` | Name of the stopped process group |
| `message` | Status message |
| `success` | `true` if successful |

### Example

```yaml
- uses: Chaffelson/nipyapi-actions@main
  with:
    command: stop-flow
    nifi-api-endpoint: ${{ secrets.NIFI_URL }}
    nifi-username: ${{ secrets.NIFI_USERNAME }}
    nifi-password: ${{ secrets.NIFI_PASSWORD }}
    process-group-id: ${{ steps.deploy.outputs.process-group-id }}
```

---

## cleanup

Delete a Process Group and its associated resources.

### Description

Stops processors, disables controller services, purges connections, and deletes a Process Group. Optionally deletes the associated parameter context.

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `process-group-id` | Yes | | Process Group ID to delete |
| `force-delete` | No | `true` | Force deletion even if flow has data |
| `delete-parameter-context` | No | `true` | Delete the associated parameter context |

### Outputs

| Output | Description |
|--------|-------------|
| `deleted` | `true` if the process group was deleted |
| `deleted-name` | Name of the deleted process group |
| `message` | Status message |
| `success` | `true` if successful |

### Example

```yaml
- uses: Chaffelson/nipyapi-actions@main
  if: always()  # Run even if previous steps failed
  with:
    command: cleanup
    nifi-api-endpoint: ${{ secrets.NIFI_URL }}
    nifi-username: ${{ secrets.NIFI_USERNAME }}
    nifi-password: ${{ secrets.NIFI_PASSWORD }}
    process-group-id: ${{ steps.deploy.outputs.process-group-id }}
```

---

## configure-params

Set parameter values on a Process Group's parameter context.

### Description

Updates parameter values in the parameter context attached to a Process Group. The Process Group must have a parameter context attached before this command can be used.

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `process-group-id` | Yes | | Process Group ID |
| `parameters` | Yes | | JSON object of parameter name/value pairs |

### Outputs

| Output | Description |
|--------|-------------|
| `parameters-updated` | Comma-separated list of updated parameter names |
| `parameters-count` | Number of parameters updated |
| `context-name` | Name of the parameter context |
| `success` | `true` if successful |

### Example

```yaml
- uses: Chaffelson/nipyapi-actions@main
  with:
    command: configure-params
    nifi-api-endpoint: ${{ secrets.NIFI_URL }}
    nifi-username: ${{ secrets.NIFI_USERNAME }}
    nifi-password: ${{ secrets.NIFI_PASSWORD }}
    process-group-id: ${{ steps.deploy.outputs.process-group-id }}
    parameters: '{"version": "2.0.0", "environment": "staging", "api_key": "${{ secrets.API_KEY }}"}'
```

### Notes

- Parameters must already exist in the parameter context
- Use this to inject environment-specific values or secrets
- The flow does not need to be stopped to update parameters

---

## get-status

Get comprehensive status information for a Process Group.

### Description

Returns detailed information about a Process Group including processor states, controller service states, version control status, and parameter context information.

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `process-group-id` | Yes | | Process Group ID |

### Outputs

**Process Group Info:**
| Output | Description |
|--------|-------------|
| `process-group-id` | Process Group ID |
| `process-group-name` | Process Group name |
| `state` | State: `RUNNING`, `STOPPED`, or `EMPTY` |

**Processor Counts:**
| Output | Description |
|--------|-------------|
| `total-processors` | Total number of processors |
| `running-processors` | Number of running processors |
| `stopped-processors` | Number of stopped processors |
| `invalid-processors` | Number of invalid processors |
| `disabled-processors` | Number of disabled processors |

**Queue Info:**
| Output | Description |
|--------|-------------|
| `queued-flowfiles` | Number of flowfiles queued |
| `queued-bytes` | Bytes queued |

**Controller Services:**
| Output | Description |
|--------|-------------|
| `total-controllers` | Total controller services |
| `enabled-controllers` | Enabled controller services |
| `disabled-controllers` | Disabled controller services |
| `enabling-controllers` | Controller services currently enabling |
| `disabling-controllers` | Controller services currently disabling |

**Version Control:**
| Output | Description |
|--------|-------------|
| `versioned` | Whether flow is under version control |
| `version-id` | Current version (commit SHA) |
| `version-state` | `UP_TO_DATE`, `LOCALLY_MODIFIED`, `STALE`, etc. |
| `flow-id` | Flow ID in registry |
| `flow-name` | Flow name in registry |
| `bucket-id` | Bucket ID in registry |
| `bucket-name` | Bucket name in registry |
| `registry-id` | Registry client ID |
| `registry-name` | Registry client name |
| `modified` | Whether flow has local modifications |

**Parameter Context:**
| Output | Description |
|--------|-------------|
| `has-parameter-context` | Whether flow has a parameter context |
| `parameter-context-id` | Parameter context ID |
| `parameter-context-name` | Parameter context name |
| `parameter-count` | Number of parameters |

### Example

```yaml
- uses: Chaffelson/nipyapi-actions@main
  id: status
  with:
    command: get-status
    nifi-api-endpoint: ${{ secrets.NIFI_URL }}
    nifi-username: ${{ secrets.NIFI_USERNAME }}
    nifi-password: ${{ secrets.NIFI_PASSWORD }}
    process-group-id: ${{ steps.deploy.outputs.process-group-id }}

- name: Check for issues
  run: |
    if [ "${{ steps.status.outputs.invalid-processors }}" != "0" ]; then
      echo "ERROR: Flow has invalid processors"
      exit 1
    fi
    if [ "${{ steps.status.outputs.running-processors }}" != "${{ steps.status.outputs.total-processors }}" ]; then
      echo "WARNING: Not all processors are running"
    fi
```

---

## See Also

- [Setup Guide](setup.md) - Getting started
- [Security Guide](security.md) - PAT and secrets best practices
- [How It Works](how-it-works.md) - Architecture overview
