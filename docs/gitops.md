# GitOps for NiFi Flows

This guide covers best practices for managing NiFi flows using Git as the source of truth.

## The GitOps Model

GitOps applies Git-based workflows to infrastructure and application deployment:

- **Git is the source of truth** - Flow definitions live in GitHub
- **Changes via pull requests** - All modifications go through PR review
- **Automated testing** - CI validates flows before merge
- **Declarative state** - The repository defines what should be deployed

## Feature Branch Workflow

### Overview

```
main (production-ready)
  │
  ├── feature/new-data-pipeline     ← Developer works here
  │     │
  │     └── PR → CI tests → Review → Merge
  │
  └── main (updated)
```

### Step-by-Step Process

**1. Create a Feature Branch**

In your flow repository:
```bash
git checkout main
git pull
git checkout -b feature/my-new-flow
```

**2. Configure NiFi for the Branch**

When setting up version control in NiFi, or when using the `ensure-registry` action, specify your feature branch and the path to your flows if they're not in the repository root:

```yaml
- uses: Chaffelson/nipyapi-actions@main
  with:
    command: ensure-registry
    github-registry-branch: feature/my-new-flow  # Your feature branch
    repository-path: nifi-flows  # If flows are in a subdirectory (omit if at repo root)
    # ... other inputs
```

**3. Develop and Commit**

- Make changes to your flow in NiFi
- Use **Version** → **Commit local changes** to save versions
- Each commit creates a new version in your feature branch

**4. Create Pull Request**

Push your branch and create a PR to `main`. If you have set up a CI workflow (see [Setup Guide](setup.md)), it will:
- Deploy your flow version to a test NiFi instance
- Run automated tests
- Clean up after testing

**5. Review and Merge**

After review and successful CI, merge the PR to `main`. What happens next depends on your setup:

- **Existing deployed flow**: If this flow is already deployed to production from `main`, NiFi will show a notification that a new version is available. An operator can then choose to update.
- **New flow**: The flow can now be deployed to production from `main`, either manually or via automated deployment using these same actions.

### Branch Detection in CI

The `deploy-flow` command automatically detects the correct branch:

- **Pull requests**: Deploys from the PR's source branch (`github.head_ref`)
- **Push to main**: Deploys from `main`

You can also specify explicitly:
```yaml
- uses: Chaffelson/nipyapi-actions@main
  with:
    command: deploy-flow
    branch: ${{ github.head_ref || github.ref_name }}
    # ... other inputs
```

## New Flow vs Existing Flow

### Creating a New Flow

When designing a new flow for version control:

1. **Create a top-level Process Group** - This becomes the versioned unit. All components inside it will be included in version control.

2. **Place all dependencies inside the Process Group** - Controller services, nested process groups, and any other components your flow needs should be contained within this top-level group. Do not configure controller services at the root canvas level if your flow depends on them.

3. **Create and attach a Parameter Context** - If your flow uses parameters, create a Parameter Context and attach it to the Process Group before starting version control. The parameter context reference will be included in the versioned flow, ensuring parameters are available when the flow is deployed elsewhere.

4. **Start version control** - Right-click the Process Group → **Version** → **Start version control**

5. **Select bucket and name** - Choose the folder (bucket) and provide a flow name. NiFi creates the flow file in your repository.

**Why this matters**: When you deploy a versioned flow, NiFi creates the Process Group and everything inside it. If your flow references controller services at the root canvas level, those won't exist in the target environment and the flow will fail to start.

### Modifying an Existing Flow

1. Ensure you're working on the correct branch in NiFi's registry client
2. Make changes to the versioned Process Group
3. Right-click → **Version** → **Commit local changes**
4. Provide a commit message describing the changes

### Updating a Deployed Flow

For flows already deployed in production:

1. The deployed flow tracks its version in the registry
2. After merging changes to `main`, the Process Group displays a notification icon indicating a newer version is available
3. Use **Version** → **Change version** to pull the latest from `main`

NiFi may also display notification icons for other states such as uncommitted local changes or version conflicts.

### Rolling Back Changes

You can undo changes by reverting to a previous version:

- **Discard uncommitted changes**: Right-click → **Version** → **Revert local changes** to discard any modifications since the last commit
- **Roll back to earlier version**: Right-click → **Version** → **Change version** and select a previous version from the list

**Important**: Version changes are all-or-nothing. You cannot partially roll back specific components within a flow. This is why regular, incremental commits are encouraged - smaller commits give you more granular rollback points.

## Parameter Handling

### How Parameters Work with Versioning

When you version a flow with parameters:

- **Parameter names and default values** are saved in the flow definition
- **Parameter contexts** are created/updated during deployment

### Sensitive Parameters

**Sensitive parameter values are never saved to version control.** Only the parameter name and the fact that it is sensitive are stored. This ensures secrets don't end up in Git.

When deploying a flow with sensitive parameters, you must set their values in the target environment using `configure-params` or manually in the NiFi UI.

NiFi also enforces type safety: if a processor or controller service property is marked as sensitive, you must use a sensitive parameter to reference it. You cannot supply a non-sensitive parameter value to a sensitive property.

**Alternative approach**: If your organisation uses an external secrets manager (such as AWS Secrets Manager or HashiCorp Vault), you can configure it as an External Parameter Provider in NiFi. The provider can be inherited into the parameter context attached to your process group, with parameter names matching those used in your versioned flow. Setup of external parameter providers is beyond the scope of this guide, but it's worth noting that these actions provide a straightforward method for injecting secrets - other approaches may better suit your corporate standards.

### The IGNORE_CHANGES Setting

The `ensure-registry` action configures the registry client with `Parameter Context Values: IGNORE_CHANGES`. This means:

| Scenario | Behavior |
|----------|----------|
| New parameter in flow | Created with default value from Git |
| Existing parameter | **Value preserved** - not overwritten |
| Parameter removed from flow | Remains in context (manual cleanup needed) |

### Why This Matters

Consider a flow with a `database_url` parameter:

```
Git (flow definition):     database_url = "jdbc:postgresql://localhost/dev"
Production deployment:     database_url = "jdbc:postgresql://prod-db/prod"
```

With `IGNORE_CHANGES`:
- Deploying a new version **keeps** the production value
- You don't accidentally overwrite production settings with development defaults

### Setting Environment-Specific Parameters

Use the `configure-params` action to set values after deployment:

```yaml
- uses: Chaffelson/nipyapi-actions@main
  with:
    command: configure-params
    process-group-id: ${{ steps.deploy.outputs.process-group-id }}
    parameters: '{"database_url": "${{ secrets.DB_URL }}", "api_key": "${{ secrets.API_KEY }}"}'
```

### Parameter Best Practices

1. **Use meaningful defaults** - Git should contain sensible development defaults
2. **Secrets via CI** - Inject sensitive values using `configure-params` and GitHub secrets
3. **Document parameters** - Note which parameters need environment-specific values
4. **Don't commit secrets** - Never put production credentials in flow definitions

## Repository Organization

### Single Flow Repository

Simple projects with one or few flows:

```
my-nifi-flows/
├── flows/
│   └── my-flow.json
├── .github/workflows/
│   └── test-flow.yml
└── README.md
```

### Multi-Environment Repository

Separate buckets for different teams or security categorisations:

```
nifi-flows/
├── analytics/             # Analytics team flows
│   └── reporting-pipeline.json
├── data-platform/         # Data platform team (stricter review)
│   └── customer-ingestion.json
├── templates/             # Reusable patterns
│   ├── kafka-ingress.json
│   └── object-store-egress.json
└── .github/workflows/
    └── test-flow.yml
```

Note: Don't separate buckets by environment (dev/prod). The same flow definition is promoted through environments - that's the point of GitOps. Use branches to manage promotion.

### Monorepo with Flows

Flows alongside application code:

```
my-application/
├── src/
├── nifi-flows/            # Use repository-path: "nifi-flows"
│   └── data-ingestion/    # bucket: "data-ingestion"
│       └── ingest.json
└── .github/workflows/
    └── ci.yml
```

## CI Workflow Patterns

### Basic: Test on PR

```yaml
on:
  pull_request:
    branches: [main]
```

Tests every PR before merge.

### Comprehensive: Test and Deploy

```yaml
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  test:
    # ... test job (always runs)

  deploy-staging:
    needs: test
    if: github.ref == 'refs/heads/main'
    # ... deploy to staging after merge
```

### With Manual Approval

```yaml
jobs:
  test:
    # ... automated tests

  deploy-production:
    needs: test
    environment: production  # Requires approval
    # ... deploy to production
```

## See Also

- [Setup Guide](setup.md) - Initial setup instructions
- [Commands Reference](commands.md) - All available commands
- [Security Guide](security.md) - Secrets and permissions
