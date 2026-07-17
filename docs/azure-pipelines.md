# Azure Pipelines Guide

Setup and usage for NiPyAPI Actions with Azure DevOps Pipelines.

Azure DevOps differs from GitHub/GitLab in one important way: NiFi's
**Azure DevOps Flow Registry Client** authenticates with a **service principal**
(OAuth2 client credentials), not a Personal Access Token. It reads flows only
from **Azure Repos Git** repositories. So the flow definitions must live in an
Azure Repos repo, and NiFi needs two controller services (an OAuth2 token
provider and a web client) which the `nipyapi` CLI provisions for you.

## Prerequisites

- Apache NiFi 2.x (the Azure DevOps registry client ships in the `nifi-azure`
  NAR; confirmed present in `apache/nifi:2.10.0`).
- An **Entra-backed** Azure DevOps organization. A personal (MSA-backed) org
  cannot add a service principal.
- A Microsoft Entra **app registration / service principal** with a client
  secret, added to the org and granted **Contribute** on the Azure Repos repo
  that holds your flows.
- The flow definitions committed to an **Azure Repos Git** repo (see
  [How It Works](how-it-works.md): bucket = folder, flow = filename).
- An agent: **self-hosted** (available immediately) or **Microsoft-hosted**
  (needs the free-parallelism grant on new orgs; see Agents below). The agent
  needs Docker, Python 3.11, `make`, and `git`.

## Service Principal Setup

Using the Azure CLI:

```bash
# 1. Create the app registration + service principal
az ad app create --display-name "openflow-ado-registry" --sign-in-audience AzureADMyOrg
az ad sp create --id <appId>

# 2. Create a client secret (store the value securely - shown once)
az ad app credential reset --id <appId> --display-name nifi --years 1 --query password -o tsv

# 3. Add the SP to the Azure DevOps org and grant repo Contribute
#    (org must be Entra-backed). Via the Azure DevOps UI:
#    Organization settings > Users > Add > add the app by name, then add it to
#    the project's Contributors group.
```

You will need these five identifiers plus the secret:

| Value | Source |
|-------|--------|
| Tenant ID | `az account show --query tenantId -o tsv` |
| Client (app) ID | the app registration's Application (client) ID |
| Client secret | from `az ad app credential reset` |
| Organization | your Azure DevOps org name |
| Project | the project holding the repo |
| Repository | the Azure Repos repo holding the flows |

## Configure the Variable Group

Create a variable group named **`nipyapi-ado`** (Pipelines > Library) and link
it to your pipeline:

| Variable | Secret? | Description |
|----------|---------|-------------|
| `NIFI_ADO_TENANT_ID` | no | Entra tenant ID |
| `NIFI_ADO_CLIENT_ID` | no | Service principal application (client) ID |
| `NIFI_ADO_CLIENT_SECRET` | **yes** (lock icon) | Service principal client secret |
| `NIFI_ADO_ORG` | no | Azure DevOps organization |
| `NIFI_ADO_PROJECT` | no | Azure DevOps project |
| `NIFI_ADO_REPO` | no | Azure Repos repository name |

Secret variables are **not** exposed to scripts automatically and cannot be used
in `${{ }}` template expressions. Map the secret to an env var on the step that
needs it (only `ensure_registry` does):

```yaml
- script: nipyapi ci ensure_registry
  name: registry
  env:
    NIFI_ADO_CLIENT_SECRET: $(NIFI_ADO_CLIENT_SECRET)   # explicit mapping required
```

## Quick Start

```yaml
pool:
  name: 'Default'            # self-hosted agent pool

variables:
  - group: nipyapi-ado
  - name: NIFI_API_ENDPOINT
    value: 'https://localhost:9447/nifi-api'
  - name: NIFI_USERNAME
    value: 'einstein'
  - name: NIFI_PASSWORD
    value: 'password1234'
  - name: NIFI_VERIFY_SSL
    value: 'false'
  - name: NIFI_REGISTRY_PROVIDER
    value: 'azuredevops'
  - name: NIFI_REPOSITORY_PATH
    value: 'tests'
  - name: NIFI_BUCKET
    value: 'flows'
  - name: NIFI_FLOW
    value: 'my-flow'

steps:
  - script: pip install "nipyapi[cli]>=1.2.0"
    displayName: 'Install nipyapi CLI'

  - script: nipyapi ci ensure_registry
    name: registry
    env:
      NIFI_ADO_CLIENT_SECRET: $(NIFI_ADO_CLIENT_SECRET)

  - script: nipyapi ci deploy_flow
    name: deploy
    env:
      NIFI_REGISTRY_CLIENT_ID: $(registry.registry_client_id)

  - script: nipyapi ci start_flow
    env:
      NIFI_PROCESS_GROUP_ID: $(deploy.process_group_id)
```

> Azure DevOps support requires a version of `nipyapi` that includes the
> Azure DevOps registry helpers. Until that ships to PyPI, install from a git
> ref instead: `pip install "nipyapi[cli] @ git+https://github.com/Chaffelson/nipyapi.git@<branch>"`.

See [azure-pipelines.yml](../azure-pipelines.yml) for the full end-to-end example
(brings up dockerised NiFi, runs the complete lifecycle, tears down).

## Using the Step Template

Reference the reusable step template so you do not repeat the CLI wiring:

```yaml
resources:
  repositories:
    - repository: nipyapi-actions
      type: git
      name: <project>/nipyapi-actions

steps:
  - template: templates/azure-pipelines-steps.yml@nipyapi-actions
    parameters:
      command: ensure_registry
      name: registry
      env:
        NIFI_ADO_CLIENT_SECRET: $(NIFI_ADO_CLIENT_SECRET)

  - template: templates/azure-pipelines-steps.yml@nipyapi-actions
    parameters:
      command: deploy_flow
      name: deploy
      env:
        NIFI_REGISTRY_CLIENT_ID: $(registry.registry_client_id)
```

## Output Variables

Running under Azure Pipelines, the CLI auto-detects the environment (via the
`TF_BUILD` variable) and emits each output as a logging command:

```
##vso[task.setvariable variable=<key>;isOutput=true]<value>
```

Give the step a `name:` and reference its outputs in later steps as
`$(<name>.<key>)`:

| Command | Key outputs |
|---------|-------------|
| `ensure_registry` | `registry_client_id`, `registry_client_name` |
| `deploy_flow` | `process_group_id`, `process_group_name`, `deployed_version` |
| `list_registry_flows` | `flow_count`, `flows` |
| `get_status` | `state`, `version_state`, `running_processors` |
| `get_flow_versions` | `current_version`, `version_count`, `versions` |
| `get_flow_diff` | `state`, `modification_count`, `modifications` |

Complex values (lists/dicts) are emitted as single-line JSON; newlines and
percent signs are percent-encoded so values round-trip intact. To force the
format explicitly, set `NIFI_OUTPUT_FORMAT: azurepipelines`.

## Environment Variables

### Connection

| Variable | Required | Description |
|----------|----------|-------------|
| `NIFI_API_ENDPOINT` | Yes | NiFi API URL |
| `NIFI_USERNAME` / `NIFI_PASSWORD` | No | Basic auth |
| `NIFI_BEARER_TOKEN` | No | JWT bearer token (alternative to basic auth) |
| `NIFI_VERIFY_SSL` | No | Verify SSL (default: true) |

### Registry (Azure DevOps)

| Variable | Required | Description |
|----------|----------|-------------|
| `NIFI_REGISTRY_PROVIDER` | Yes | Set to `azuredevops` |
| `NIFI_ADO_TENANT_ID` | Yes | Entra tenant ID |
| `NIFI_ADO_CLIENT_ID` | Yes | Service principal client ID |
| `NIFI_ADO_CLIENT_SECRET` | Yes | Service principal secret (map from a secret var) |
| `NIFI_ADO_ORG` / `NIFI_ADO_PROJECT` / `NIFI_ADO_REPO` | Yes | Azure DevOps coordinates |
| `NIFI_REGISTRY_BRANCH` | No | Default branch (default `main`) |
| `NIFI_REPOSITORY_PATH` | No | Subfolder in the repo (e.g. `tests`) |
| `NIFI_BUCKET` / `NIFI_FLOW` | Yes | Bucket (folder) and flow (filename) |

## Agents

New Azure DevOps organizations receive **0 Microsoft-hosted parallel jobs** by
default; the free grant must be requested
(<https://aka.ms/azpipelines-parallelism-request>) and takes 2-3 business days.

- **Self-hosted** (recommended to start): register an agent on a machine you
  control (Pipelines > Agent pools). No grant needed, available immediately. The
  agent runs `make` + `docker` + the CLI, exactly like the GitHub/GitLab runners.
- **Microsoft-hosted** (`vmImage: ubuntu-latest`): available once your org has
  the parallelism grant. The pipeline YAML is portable between the two.

## Local Validation

Azure DevOps has no full local runner (unlike `act` for GitHub or
`gitlab-ci-local` for GitLab), but you can validate the YAML offline and against
the service preview API:

```bash
# Lint + offline schema check (no credentials needed)
uvx azure-pipeline-validator --lint --schema .

# Preview against the service (needs AZDO_* + a PAT; queues no build)
uvx azure-pipeline-validator --preview --schema azure-pipelines.yml
```

## Troubleshooting

### "This action is only supported for Microsoft Entra backed organizations"

The org is MSA-backed. A service principal is an Entra identity and cannot be
added to an MSA-backed org. Connect the org to your Entra tenant
(Organization settings > Microsoft Entra > Connect Directory) or create a new
Entra-backed org.

### Registry client is valid but listing the bucket fails

- Confirm the service principal has **Contribute** on the repo.
- Confirm the repo actually contains the flow files at
  `<repository-path>/<bucket>/<flow>.json` on the default branch.
- Confirm NiFi has network egress to `login.microsoftonline.com` and
  `dev.azure.com` (only relevant for locked-down/SPCS deployments).

### The secret is empty at runtime

Secret variables are not auto-exposed. Map `NIFI_ADO_CLIENT_SECRET` explicitly
via the step's `env:` block (see Configure the Variable Group).

## See Also

- [azure-pipelines.yml](../azure-pipelines.yml) - Full end-to-end example
- [Commands Reference](commands.md) - All commands and options
- [How It Works](how-it-works.md) - Architecture overview
- [Security Guide](security.md) - Credentials and best practices
