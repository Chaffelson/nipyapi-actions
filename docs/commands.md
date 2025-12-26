# Commands Reference

Complete reference for all NiPyAPI Actions commands.

## CLI Usage

All commands are available via the `nipyapi` CLI:

```bash
# Install CLI
pip install "nipyapi[cli]"

# Run commands
nipyapi ci ensure_registry
nipyapi ci deploy_flow
nipyapi ci start_flow
```

The CLI auto-detects CI environments and formats output appropriately:
- **GitHub Actions**: Outputs `key=value` pairs for `$GITHUB_OUTPUT`
- **GitLab CI**: Outputs `KEY=VALUE` pairs for dotenv artifacts
- **Terminal**: Outputs JSON by default

## Environment Variables

Both platforms use the same environment variables. The CLI reads these automatically.

| Environment Variable | GitHub Input | Description |
|---------------------|--------------|-------------|
| `NIFI_API_ENDPOINT` | `nifi-api-endpoint` | NiFi API URL |
| `NIFI_BEARER_TOKEN` | `nifi-bearer-token` | JWT bearer token |
| `NIFI_USERNAME` | `nifi-username` | Basic auth username |
| `NIFI_PASSWORD` | `nifi-password` | Basic auth password |
| `NIFI_VERIFY_SSL` | `nifi-verify-ssl` | Verify SSL (default: true) |
| `NIFI_PROCESS_GROUP_ID` | `process-group-id` | Target process group |
| `NIFI_REGISTRY_CLIENT_ID` | `registry-client-id` | Registry client ID |
| `NIFI_BUCKET` | `bucket` | Bucket/folder name |
| `NIFI_FLOW` | `flow` | Flow name |

**GitHub Actions:**
```yaml
- uses: Chaffelson/nipyapi-actions@main
  with:
    command: deploy-flow
    nifi-api-endpoint: ${{ secrets.NIFI_URL }}
    nifi-bearer-token: ${{ secrets.NIFI_TOKEN }}
    bucket: flows
    flow: my-flow
```

**GitLab CI:**
```yaml
deploy-flow:
  script:
    - pip install "nipyapi[cli]"
    - nipyapi ci deploy_flow | tee -a outputs.env
  variables:
    NIFI_API_ENDPOINT: $NIFI_URL
    NIFI_BEARER_TOKEN: $NIFI_TOKEN
    NIFI_BUCKET: flows
    NIFI_FLOW: my-flow
```

## Common Inputs

These connection settings are used by all commands:

| Environment Variable | Required | Description |
|---------------------|----------|-------------|
| `NIFI_API_ENDPOINT` | Yes | NiFi API endpoint URL |
| `NIFI_BEARER_TOKEN` | No | JWT bearer token (alternative to username/password) |
| `NIFI_USERNAME` | No | Basic auth username (alternative to bearer token) |
| `NIFI_PASSWORD` | No | Basic auth password |
| `NIFI_VERIFY_SSL` | No | Verify SSL certificates (default: true) |

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

**GitHub Actions:**
```yaml
- uses: Chaffelson/nipyapi-actions@main
  id: registry
  with:
    command: ensure-registry
    nifi-api-endpoint: ${{ secrets.NIFI_URL }}
    nifi-bearer-token: ${{ secrets.NIFI_BEARER_TOKEN }}
    github-registry-token: ${{ secrets.GH_REGISTRY_TOKEN }}
    registry-client-name: my-github-registry
    github-registry-repo: myorg/my-flows
```

**GitLab CI:**
```yaml
ensure-registry:
  script:
    - pip install "nipyapi[cli]"
    - nipyapi ci ensure_registry | tee outputs.env
  variables:
    NIFI_API_ENDPOINT: $NIFI_URL
    NIFI_BEARER_TOKEN: $NIFI_TOKEN
    GH_REGISTRY_TOKEN: $GH_REGISTRY_TOKEN
    NIFI_REGISTRY_CLIENT_NAME: my-github-registry
    NIFI_REGISTRY_REPO: myorg/my-flows
  artifacts:
    reports:
      dotenv: outputs.env
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

**GitHub Actions:**
```yaml
- uses: Chaffelson/nipyapi-actions@main
  id: deploy
  with:
    command: deploy-flow
    nifi-api-endpoint: ${{ secrets.NIFI_URL }}
    nifi-bearer-token: ${{ secrets.NIFI_BEARER_TOKEN }}
    registry-client-id: ${{ steps.registry.outputs.registry-client-id }}
    bucket: flows
    flow: my-flow
```

**GitLab CI:**
```yaml
deploy-flow:
  script:
    - nipyapi ci deploy_flow | tee -a outputs.env
  variables:
    NIFI_REGISTRY_CLIENT_ID: $REGISTRY_CLIENT_ID
    NIFI_BUCKET: flows
    NIFI_FLOW: my-flow
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

**GitHub Actions:**
```yaml
- uses: Chaffelson/nipyapi-actions@main
  with:
    command: start-flow
    nifi-api-endpoint: ${{ secrets.NIFI_URL }}
    nifi-bearer-token: ${{ secrets.NIFI_BEARER_TOKEN }}
    process-group-id: ${{ steps.deploy.outputs.process-group-id }}
```

**GitLab CI:**
```yaml
start-flow:
  script:
    - nipyapi ci start_flow | tee -a outputs.env
  variables:
    NIFI_PROCESS_GROUP_ID: $PROCESS_GROUP_ID
```

---

## stop-flow

Stop a running Process Group.

### Description

Stops all processors in a Process Group. By default, controller services remain
enabled so the flow can be quickly restarted.

Use `--disable_controllers` if you need to delete the process group afterward
(deletion requires disabled controllers and purged queues).

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `process-group-id` | Yes | | Process Group ID to stop |
| `disable-controllers` | No | `false` | Also disable controller services (needed before deletion) |

### Outputs

| Output | Description |
|--------|-------------|
| `stopped` | `true` if the process group was stopped |
| `process-group-name` | Name of the stopped process group |
| `controllers-disabled` | `true` if controllers were disabled |
| `success` | `true` if successful |

### Example

**GitHub Actions (simple stop):**
```yaml
- uses: Chaffelson/nipyapi-actions@main
  with:
    command: stop-flow
    nifi-api-endpoint: ${{ secrets.NIFI_URL }}
    nifi-bearer-token: ${{ secrets.NIFI_BEARER_TOKEN }}
    process-group-id: ${{ steps.deploy.outputs.process-group-id }}
```

**GitLab CI (simple stop):**
```yaml
stop-flow:
  script:
    - nipyapi ci stop_flow | tee -a outputs.env
  variables:
    NIFI_PROCESS_GROUP_ID: $PROCESS_GROUP_ID
```

**GitLab CI (stop with disabled controllers - before deletion):**
```yaml
stop-for-deletion:
  script:
    - nipyapi ci stop_flow --disable_controllers | tee -a outputs.env
  variables:
    NIFI_PROCESS_GROUP_ID: $PROCESS_GROUP_ID
```

---

## change-version

Change a deployed flow to a different version.

### Description

Changes the version of an already-deployed Process Group to a specified version (tag or commit SHA). This is useful for:
- Rolling back to a previous version
- Deploying a specific tagged release
- Upgrading to a newer version

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `process-group-id` | Yes | | Process Group ID to change |
| `target-version` | No | _latest_ | Version to change to (tag like `v1.0.0` or commit SHA) |
| `branch` | No | _current_ | Branch to use when resolving versions |

### Outputs

| Output | Description |
|--------|-------------|
| `previous-version` | Version before the change |
| `new-version` | Version after the change |
| `version-state` | New version state (`UP_TO_DATE` or `STALE`) |
| `success` | `true` if successful |

### Example

**GitHub Actions:**
```yaml
- uses: Chaffelson/nipyapi-actions@main
  with:
    command: change-version
    nifi-api-endpoint: ${{ secrets.NIFI_URL }}
    nifi-bearer-token: ${{ secrets.NIFI_BEARER_TOKEN }}
    process-group-id: ${{ steps.deploy.outputs.process-group-id }}
    target-version: v1.0.0  # omit for latest
```

**GitLab CI:**
```yaml
change-version:
  script:
    - nipyapi ci change_flow_version | tee -a outputs.env
  variables:
    NIFI_PROCESS_GROUP_ID: $PROCESS_GROUP_ID
    NIFI_TARGET_VERSION: v1.0.0  # omit for latest
```

### Notes

- The flow will be stopped temporarily during the version change
- If the flow has local modifications, you must use `revert-flow` first
- When changing to an older version, the state will be `STALE` (indicating newer versions exist)

---

## revert-flow

Revert local modifications to a deployed flow.

### Description

Reverts any local (uncommitted) changes made to a deployed Process Group, restoring it to match the version currently tracked in the registry. This is useful when:
- Test modifications need to be discarded
- The flow needs to be reset to a known state before version change
- Local changes were made accidentally

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `process-group-id` | Yes | | Process Group ID to revert |

### Outputs

| Output | Description |
|--------|-------------|
| `reverted` | `true` if changes were reverted, `false` if already up to date |
| `version` | Current version after revert |
| `state` | Version state after revert (should be `UP_TO_DATE`) |
| `success` | `true` if successful |

### Example

**GitHub Actions:**
```yaml
- uses: Chaffelson/nipyapi-actions@main
  with:
    command: revert-flow
    nifi-api-endpoint: ${{ secrets.NIFI_URL }}
    nifi-bearer-token: ${{ secrets.NIFI_BEARER_TOKEN }}
    process-group-id: ${{ steps.deploy.outputs.process-group-id }}
```

**GitLab CI:**
```yaml
revert-flow:
  script:
    - nipyapi ci revert_flow | tee -a outputs.env
  variables:
    NIFI_PROCESS_GROUP_ID: $PROCESS_GROUP_ID
```

### Notes

- If the flow has no local modifications (`UP_TO_DATE` state), this is a no-op
- Does not change the tracked version, only discards local modifications
- Use `change-version` to switch to a different version

---

## cleanup

Stop and optionally delete a Process Group.

### Description

By default, stops processors, disables controller services, and deletes the Process Group.
Does NOT delete the parameter context by default (safe for shared contexts like Openflow connectors).

Use explicit flags for more aggressive cleanup in CI/CD pipelines.

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `process-group-id` | Yes | | Process Group ID to clean up |
| `stop-only` | No | `false` | Only stop processors, don't delete anything |
| `force` | No | `false` | Force deletion even if flow has queued data |
| `delete-parameter-context` | No | `false` | Also delete the parameter context (use with caution) |
| `disable-controllers` | No | `true` | Disable controller services after stopping |

### Outputs

| Output | Description |
|--------|-------------|
| `stopped` | `true` if processors were stopped |
| `deleted` | `true` if the process group was deleted |
| `process-group-name` | Name of the process group |
| `parameter-context-deleted` | `true` if parameter context was deleted |
| `success` | `true` if successful |

### Example

**GitHub Actions (safe cleanup - keeps parameter context):**
```yaml
- uses: Chaffelson/nipyapi-actions@main
  if: always()
  with:
    command: cleanup
    nifi-api-endpoint: ${{ secrets.NIFI_URL }}
    nifi-bearer-token: ${{ secrets.NIFI_BEARER_TOKEN }}
    process-group-id: ${{ steps.deploy.outputs.process-group-id }}
```

**GitLab CI (full cleanup for CI/CD pipelines):**
```yaml
cleanup:
  script:
    # Full cleanup with parameter context deletion (only for CI-deployed flows)
    - nipyapi ci cleanup --delete_parameter_context --force | tee -a outputs.env
  variables:
    NIFI_PROCESS_GROUP_ID: $PROCESS_GROUP_ID
  when: always
```

**GitLab CI (stop only - no deletion):**
```yaml
stop-flow:
  script:
    - nipyapi ci cleanup --stop_only | tee -a outputs.env
  variables:
    NIFI_PROCESS_GROUP_ID: $PROCESS_GROUP_ID
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

**GitHub Actions:**
```yaml
- uses: Chaffelson/nipyapi-actions@main
  with:
    command: configure-params
    nifi-api-endpoint: ${{ secrets.NIFI_URL }}
    nifi-bearer-token: ${{ secrets.NIFI_BEARER_TOKEN }}
    process-group-id: ${{ steps.deploy.outputs.process-group-id }}
    parameters: '{"version": "2.0.0", "environment": "staging"}'
```

**GitLab CI:**
```yaml
configure-params:
  script:
    - nipyapi ci configure_params | tee -a outputs.env
  variables:
    NIFI_PROCESS_GROUP_ID: $PROCESS_GROUP_ID
    NIFI_PARAMETERS: '{"version": "2.0.0", "environment": "staging"}'
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

**GitHub Actions:**
```yaml
- uses: Chaffelson/nipyapi-actions@main
  id: status
  with:
    command: get-status
    nifi-api-endpoint: ${{ secrets.NIFI_URL }}
    nifi-bearer-token: ${{ secrets.NIFI_BEARER_TOKEN }}
    process-group-id: ${{ steps.deploy.outputs.process-group-id }}
```

**GitLab CI:**
```yaml
get-status:
  script:
    - nipyapi ci get_status | tee -a outputs.env
  variables:
    NIFI_PROCESS_GROUP_ID: $PROCESS_GROUP_ID
  artifacts:
    reports:
      dotenv: outputs.env
```

---

## list-registry-flows

List flows available in a Git registry bucket.

### Description

Queries a Git-based Flow Registry to list available flows within a bucket. Useful for discovering what flows can be deployed before running `deploy-flow`.

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `registry-client-id` | Yes | | Registry client ID (from `ensure-registry`) |
| `bucket` | Yes | | Bucket (folder) to list flows from |
| `branch` | No | _default_ | Branch to query |
| `detailed` | No | `false` | Include descriptions and comments |

### Outputs

| Output | Description |
|--------|-------------|
| `registry-client-id` | Registry client ID used |
| `registry-client-name` | Registry client name |
| `bucket` | Bucket queried |
| `flow-count` | Number of flows found |
| `flows` | JSON array of flow info (name, flow_id) |
| `success` | `true` if successful |

### Example

**GitHub Actions:**
```yaml
- uses: Chaffelson/nipyapi-actions@main
  id: list-flows
  with:
    command: list-registry-flows
    nifi-api-endpoint: ${{ secrets.NIFI_URL }}
    nifi-bearer-token: ${{ secrets.NIFI_BEARER_TOKEN }}
    registry-client-id: ${{ steps.registry.outputs.registry-client-id }}
    bucket: flows
```

**GitLab CI:**
```yaml
list-registry-flows:
  script:
    - nipyapi ci list_registry_flows | tee -a outputs.env
  variables:
    NIFI_REGISTRY_CLIENT_ID: $REGISTRY_CLIENT_ID
    NIFI_BUCKET: flows
```

---

## get-versions

List available versions for a deployed flow.

### Description

Returns the version history of a deployed, version-controlled Process Group. Use this to see what versions are available for promotion, rollback, or to verify the current deployed version.

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `process-group-id` | Yes | | Process Group ID |

### Outputs

| Output | Description |
|--------|-------------|
| `flow-id` | Flow identifier in registry |
| `bucket-id` | Bucket containing the flow |
| `registry-id` | Registry client ID |
| `current-version` | Currently deployed version |
| `state` | Version control state |
| `version-count` | Number of versions available |
| `versions` | JSON array of version metadata |
| `success` | `true` if successful |

### Example

**GitHub Actions:**
```yaml
- uses: Chaffelson/nipyapi-actions@main
  id: versions
  with:
    command: get-versions
    nifi-api-endpoint: ${{ secrets.NIFI_URL }}
    nifi-bearer-token: ${{ secrets.NIFI_BEARER_TOKEN }}
    process-group-id: ${{ steps.deploy.outputs.process-group-id }}
```

**GitLab CI:**
```yaml
get-versions:
  script:
    - nipyapi ci get_flow_versions | tee -a outputs.env
  variables:
    NIFI_PROCESS_GROUP_ID: $PROCESS_GROUP_ID
```

### Notes

- The `versions` output contains commit SHA, author, timestamp, and comments for each version
- Use with `change-version` to switch to a specific version

---

## get-diff

Check for local modifications to a versioned flow.

### Description

Returns details about any local (uncommitted) changes made to a version-controlled Process Group. Use this before promotion to detect modifications that would block a version upgrade.

This is particularly important in environments where someone may have made emergency changes that weren't committed back to the registry.

### Inputs

| Input | Required | Default | Description |
|-------|----------|---------|-------------|
| `process-group-id` | Yes | | Process Group ID |

### Outputs

| Output | Description |
|--------|-------------|
| `process-group-id` | Process Group ID |
| `process-group-name` | Process Group name |
| `flow-id` | Flow ID in registry |
| `current-version` | Current committed version |
| `state` | Version control state (`UP_TO_DATE`, `LOCALLY_MODIFIED`, etc.) |
| `modification-count` | Number of modified components |
| `modifications` | JSON array of modification details |
| `success` | `true` if successful |

### Example

**GitHub Actions:**
```yaml
- uses: Chaffelson/nipyapi-actions@main
  id: diff
  with:
    command: get-diff
    nifi-api-endpoint: ${{ secrets.NIFI_URL }}
    nifi-bearer-token: ${{ secrets.NIFI_BEARER_TOKEN }}
    process-group-id: ${{ steps.deploy.outputs.process-group-id }}

- name: Check for modifications
  if: steps.diff.outputs.modification-count != '0'
  run: |
    echo "WARNING: Flow has ${{ steps.diff.outputs.modification-count }} local modifications"
    echo "Consider reverting before upgrade: use revert-flow command"
```

**GitLab CI:**
```yaml
get-diff:
  script:
    - nipyapi ci get_flow_diff | tee -a outputs.env
  variables:
    NIFI_PROCESS_GROUP_ID: $PROCESS_GROUP_ID

check-modifications:
  script:
    - |
      if [ "$MODIFICATION_COUNT" != "0" ]; then
        echo "WARNING: Flow has local modifications - review before promotion"
        exit 1
      fi
```

### Notes

- If `modification-count` is 0 and `state` is `UP_TO_DATE`, the flow matches the registry version
- Use `revert-flow` to discard local modifications before upgrading
- The `modifications` array shows exactly what changed (component, type, description)

---

## Additional CLI Functions

The `nipyapi` CLI provides additional functions that may be useful for advanced CI/CD workflows. These are not included in the example action implementations above, but are available via direct CLI usage.

### Discovery and Audit

| Function | CLI Command | Description |
|----------|-------------|-------------|
| `list_flows` | `nipyapi ci list_flows` | List Process Groups deployed on the NiFi canvas |

**Example:**
```bash
# List all flows on canvas
nipyapi ci list_flows

# Use in GitLab CI
nipyapi ci list_flows | tee -a outputs.env
```

### GitOps / Development Workflows

| Function | CLI Command | Description |
|----------|-------------|-------------|
| `commit_flow` | `nipyapi ci commit_flow` | Commit local changes back to Git registry |
| `detach_flow` | `nipyapi ci detach_flow` | Remove version control from a Process Group |

**Example:**
```bash
# Commit local modifications to registry
nipyapi ci commit_flow --process_group_id <pg-id> --comment "Updated processor config"

# Detach from version control (fork a flow)
nipyapi ci detach_flow --process_group_id <pg-id>
```

> **Note**: These are typically used in development workflows rather than production CI/CD pipelines. See the [nipyapi documentation](https://nipyapi.readthedocs.io/) for full details.

### Parameter Management

| Function | CLI Command | Description |
|----------|-------------|-------------|
| `configure_inherited_params` | `nipyapi ci configure_inherited_params` | Set values in inherited parameter contexts |
| `upload_asset` | `nipyapi ci upload_asset` | Upload a file as a parameter asset |

**Example:**
```bash
# Set inherited parameter values (useful for OpenFlow connectors)
nipyapi ci configure_inherited_params --process_group_id <pg-id> \
  --parameters '{"parent_param": "value"}'

# Upload a certificate as a parameter asset
nipyapi ci upload_asset --context_id <ctx-id> --parameter_name "ssl_cert" \
  --file_path /path/to/cert.pem
```

### Version Resolution

| Function | CLI Command | Description |
|----------|-------------|-------------|
| `resolve_git_ref` | `nipyapi ci resolve_git_ref` | Resolve a Git tag or ref to a commit SHA |

**Example:**
```bash
# Resolve a tag to its commit SHA
nipyapi ci resolve_git_ref --process_group_id <pg-id> --ref "v1.0.0"
```

> **Note**: Useful for tag-based release workflows where you need to convert a semantic version tag to the actual commit identifier.

---

## See Also

- [GitHub Actions Guide](github-actions.md) - GitHub Actions setup
- [GitLab CI Guide](gitlab-ci.md) - GitLab CI setup
- [Security Guide](security.md) - Authentication and secrets
- [How It Works](how-it-works.md) - Architecture overview
- [nipyapi Documentation](https://nipyapi.readthedocs.io/) - Full client documentation
