# GitHub Actions Guide

Setup and usage for NiPyAPI Actions with GitHub Actions.

## Prerequisites

Before you begin, ensure you have:

- [ ] **Apache NiFi 2.x** running and accessible from GitHub Actions runners
- [ ] **GitHub repository** for storing your flow definitions
- [ ] **Repository admin access** to add secrets

## Step 1: Create a GitHub Personal Access Token

NiFi's GitHub Flow Registry Client requires a Personal Access Token (PAT) to access your repository.

### For Public Repositories (Recommended: Fine-grained PAT)

1. Go to **GitHub Settings** → **Developer settings** → **Personal access tokens** → **Fine-grained tokens**

2. Click **Generate new token**

3. Configure the token:
   - **Token name**: `nifi-flow-registry` (or similar)
   - **Expiration**: Choose based on your security policy
   - **Repository access**: Select **Only select repositories** → choose your flow repository
   - **Permissions**:
     - **Contents**: Read-only
     - **Metadata**: Read-only

   **Note**: Read-only access is sufficient for CI/CD testing with these actions. If you also want to use the same token for versioning flows directly from NiFi's UI (committing flow changes back to GitHub), select **Contents: Read and write** instead.

4. Click **Generate token** and copy the value

### For Private Repositories

You can use either a fine-grained PAT (as above) or a classic PAT with `repo` scope.

## Step 2: Add Secrets to Your Repository

1. Go to your repository → **Settings** → **Secrets and variables** → **Actions**

2. Add these repository secrets:

| Secret Name | Description |
|-------------|-------------|
| `NIFI_URL` | Your NiFi API endpoint (e.g., `https://nifi.example.com:8443/nifi-api`) |
| `NIFI_BEARER_TOKEN` | NiFi JWT bearer token |
| `GH_REGISTRY_TOKEN` | The PAT you created in Step 1 |

**Or** use basic authentication instead of bearer token:

| Secret Name | Description |
|-------------|-------------|
| `NIFI_USERNAME` | NiFi username |
| `NIFI_PASSWORD` | NiFi password |

## Step 3: Version Control Your Flows

NiFi's GitHub Flow Registry Client commits flows directly to GitHub - no manual file handling required.

### Repository Structure

Flows are stored as JSON files in folders (buckets):

```
your-repo/
├── flows/                    # Bucket name (folder)
│   └── my-flow.json          # Flow (committed by NiFi)
├── .github/
│   └── workflows/
│       └── test-flow.yml     # Your CI workflow
└── README.md
```

### Versioning from NiFi

1. In NiFi, configure a GitHub Flow Registry Client pointing to your repository (or use the `ensure-registry` action)
2. Right-click on a Process Group and select **Version** → **Start version control**
3. Select your GitHub registry client, choose a bucket (folder), and provide a flow name
4. NiFi commits the flow definition directly to GitHub

When you make changes to a versioned flow, use **Version** → **Commit local changes** to create a new version (commit) in GitHub.

For feature branch workflows and best practices, see the [GitOps Guide](gitops.md).

## Step 4: Create Your Workflow

Create `.github/workflows/test-flow.yml`:

```yaml
name: Test NiFi Flow

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Registry Client
        uses: Chaffelson/nipyapi-actions@main
        id: registry
        with:
          command: ensure-registry
          nifi-api-endpoint: ${{ secrets.NIFI_URL }}
          nifi-bearer-token: ${{ secrets.NIFI_BEARER_TOKEN }}  # or nifi-username/nifi-password
          github-registry-token: ${{ secrets.GH_REGISTRY_TOKEN }}
          registry-client-name: my-flow-registry

      - name: Deploy Flow
        uses: Chaffelson/nipyapi-actions@main
        id: deploy
        with:
          command: deploy-flow
          nifi-api-endpoint: ${{ secrets.NIFI_URL }}
          nifi-bearer-token: ${{ secrets.NIFI_BEARER_TOKEN }}
          registry-client-id: ${{ steps.registry.outputs.registry-client-id }}
          bucket: flows
          flow: my-flow

      - name: Start Flow
        uses: Chaffelson/nipyapi-actions@main
        with:
          command: start-flow
          nifi-api-endpoint: ${{ secrets.NIFI_URL }}
          nifi-bearer-token: ${{ secrets.NIFI_BEARER_TOKEN }}
          process-group-id: ${{ steps.deploy.outputs.process-group-id }}

      - name: Run Tests
        run: |
          echo "Add your test logic here"
          echo "Deployed flow: ${{ steps.deploy.outputs.process-group-name }}"

      - name: Cleanup
        if: always()
        uses: Chaffelson/nipyapi-actions@main
        with:
          command: cleanup
          nifi-api-endpoint: ${{ secrets.NIFI_URL }}
          nifi-bearer-token: ${{ secrets.NIFI_BEARER_TOKEN }}
          process-group-id: ${{ steps.deploy.outputs.process-group-id }}
          # For CI/CD full cleanup, enable these options:
          delete-parameter-context: 'true'
          force: 'true'
```

## Step 5: Test Your Setup

1. Push your workflow to GitHub
2. Create a PR or push to trigger the workflow
3. Check the Actions tab for results

## Troubleshooting

### "Resource not accessible by integration"

This error means you're using `GITHUB_TOKEN` instead of a PAT. NiFi's GitHub Flow Registry Client requires a Personal Access Token.

### "Unable to obtain listing of versions"

Check that:
- Your PAT has read access to the repository
- The `bucket` and `flow` names match your folder/file structure
- The `repository-path` is correct (if using one)

### SSL Certificate Errors

For self-signed certificates, add:
```yaml
nifi-verify-ssl: 'false'
```

For production, configure proper certificates.

### Connection Refused

Ensure your NiFi instance is:
- Running and accessible from GitHub's runners
- Not blocked by firewall rules
- Using the correct port in `nifi-api-endpoint`

## See Also

- [GitLab CI Guide](gitlab-ci.md) - Using with GitLab CI/CD
- [Commands Reference](commands.md) - All commands and options
- [GitOps Guide](gitops.md) - Feature branches and parameter handling
- [Security Guide](security.md) - PAT setup and best practices
- [How It Works](how-it-works.md) - Architecture overview
