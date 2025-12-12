# Security Guide

Best practices for securing your NiFi CI/CD workflow with NiPyAPI Actions.

## Git Provider Token Requirements

NiFi's Git Flow Registry Clients (GitHub and GitLab) require Personal Access Tokens (PATs) for repository access.

### GitHub Token Requirements

The automatic `GITHUB_TOKEN` provided by GitHub Actions does **not** work because:

- `GITHUB_TOKEN` is an app installation token, not a user token
- NiFi's client calls GitHub's `/user` API endpoint for authentication
- This endpoint requires user authentication, which `GITHUB_TOKEN` cannot provide

**Error you'll see if using GITHUB_TOKEN:**
```
"Resource not accessible by integration"
```

### GitLab Token Requirements

GitLab requires more permissive token scopes than GitHub:

| Setting | Requirement |
|---------|-------------|
| Role | Developer or higher (not Guest) |
| Scopes | `api`, `read_repository`, `write_repository` |

The `api` scope is required because NiFi uses GitLab's REST API to browse repository contents.

**Error you may see with insufficient permissions:**
```
"Client does not have read access to the repository"
```

This error can also indicate token rate limiting on trial/free GitLab accounts. Try creating a new token if this occurs unexpectedly.

### Creating a Fine-Grained PAT (Recommended)

For the best security posture, use a fine-grained PAT with minimal permissions:

1. Go to **GitHub Settings** then **Developer settings** then **Personal access tokens** then **Fine-grained tokens**

2. Click **Generate new token**

3. Configure:

| Setting | Value |
|---------|-------|
| Token name | `nifi-flow-registry` |
| Expiration | Per your security policy |
| Repository access | Only select repositories |
| Selected repositories | Your flow repository only |

4. Set permissions:

| Permission | Access Level | Notes |
|------------|--------------|-------|
| Contents | Read-only | Sufficient for CI/CD testing |
| Metadata | Read-only | Required |

**Note on read-write access**: Read-only is sufficient for these GitHub Actions (deploying and testing flows). If you also want to use the same token for versioning flows directly from NiFi's UI (committing flow changes back to GitHub), you'll need **Contents: Read and write** instead.

5. Generate and securely store the token

### Fine-Grained PAT Benefits

- **Minimal permissions**: Read-only access means token cannot modify code (for CI use)
- **Scoped access**: Limited to specific repositories
- **Audit trail**: GitHub logs token usage
- **Expiration**: Tokens can have mandatory expiration dates
- **Revocable**: Easy to revoke if compromised

### Classic PAT Alternative

If you cannot use fine-grained tokens (e.g., GitHub Enterprise Server older than 3.10):

1. Go to **Settings** then **Developer settings** then **Personal access tokens** then **Tokens (classic)**
2. Generate with `repo` scope (or `public_repo` for public repositories)

**Note**: Classic PATs are less secure as they grant broader access.

## Storing Secrets

### GitHub Actions - Repository Secrets

Repository secrets are available to all workflows in your repository:

1. Go to **Repository** then **Settings** then **Secrets and variables** then **Actions**
2. Click **New repository secret**
3. Add your secrets:

| Secret Name | Description |
|-------------|-------------|
| `NIFI_URL` | NiFi API endpoint |
| `NIFI_BEARER_TOKEN` | NiFi JWT bearer token |
| `GH_REGISTRY_TOKEN` | GitHub PAT (if flows in GitHub) |
| `GL_REGISTRY_TOKEN` | GitLab PAT (if flows in GitLab) |

Or use basic auth instead of bearer token:

| Secret Name | Description |
|-------------|-------------|
| `NIFI_USERNAME` | NiFi username |
| `NIFI_PASSWORD` | NiFi password |

### GitLab CI - CI/CD Variables

In GitLab, configure variables at **Settings** > **CI/CD** > **Variables**:

| Variable | Description |
|----------|-------------|
| `NIFI_API_ENDPOINT` | NiFi API endpoint |
| `NIFI_BEARER_TOKEN` | NiFi JWT bearer token |
| `GH_REGISTRY_TOKEN` | GitHub PAT (if flows in GitHub) |
| `GL_REGISTRY_TOKEN` | GitLab PAT (if flows in GitLab) |

Mark sensitive variables as **Masked** to prevent them appearing in job logs.

### Environment Secrets (For Approval Gates)

Use environment secrets when you need approval workflows for deployments:

1. Create an environment (e.g., `production`)
2. Configure protection rules (required reviewers, wait timer)
3. Add secrets to the environment
4. Reference in workflow:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production  # Requires approval
    steps:
      - uses: Chaffelson/nipyapi-actions@main
        with:
          command: deploy-flow
          nifi-api-endpoint: ${{ secrets.NIFI_URL }}
          # Uses environment-scoped secrets
```

### Organization Secrets

For secrets shared across multiple repositories:

1. Go to **Organization** then **Settings** then **Secrets and variables** then **Actions**
2. Add secrets and configure repository access
3. Reference the same way as repository secrets

## Fork and PR Security

### GitHub's Built-in Protections

GitHub automatically protects against secret leakage:

- **Fork PRs**: Secrets are NOT available to workflows triggered by fork PRs
- **Branch PRs**: Only PRs from branches within the same repo can access secrets
- **Pull request approval**: Require approval before running workflows on fork PRs

### Best Practices for Public Repositories

1. **Enable branch protection** on `main`:
   - Require pull request reviews
   - Require status checks to pass
   - Restrict who can push

2. **Configure workflow permissions**:
   ```yaml
   permissions:
     contents: read
   ```

3. **Use pull_request_target carefully**: This event has access to secrets even for fork PRs. Avoid it unless you fully understand the security implications.

4. **Limit workflow triggers**:
   ```yaml
   on:
     pull_request:
       branches: [main]  # Only run on PRs to main
   ```

## NiFi Authentication

### Bearer Token

For NiFi instances using OIDC or JWT authentication:

```yaml
nifi-bearer-token: ${{ secrets.NIFI_BEARER_TOKEN }}
```

### Basic Authentication

For NiFi instances using username/password authentication:

```yaml
nifi-username: ${{ secrets.NIFI_USERNAME }}
nifi-password: ${{ secrets.NIFI_PASSWORD }}
```

### SSL Certificates

**Development** (self-signed):
```yaml
nifi-verify-ssl: 'false'
nipyapi-suppress-ssl-warnings: 'true'
```

**Production**:
- Use proper CA-signed certificates
- Keep `nifi-verify-ssl: 'true'` (default)
- Mount CA bundle if using internal CA

## Credential Rotation

### PAT Rotation

1. Generate new PAT before old one expires
2. Update repository secret
3. Verify workflows succeed
4. Revoke old PAT

### NiFi Password Rotation

1. Update password in NiFi
2. Update repository secret
3. Verify workflows succeed

## Audit and Monitoring

### GitHub Actions Logs

- Review workflow runs for unexpected behavior
- Secrets are automatically masked in logs
- Failed authentication attempts are logged

### NiFi Audit Logs

- NiFi logs all API access
- Review for unexpected:
  - Registry client modifications
  - Process group deployments
  - Controller service changes

## Security Checklist

- [ ] Using PAT with minimal permissions (fine-grained for GitHub, scoped for GitLab)
- [ ] PAT scoped to specific repository
- [ ] Secrets stored in repository/environment secrets (masked in GitLab)
- [ ] Branch protection enabled on main
- [ ] Workflow permissions restricted
- [ ] SSL verification enabled in production
- [ ] NiFi service account with minimal permissions
- [ ] Regular credential rotation scheduled
- [ ] Audit logging reviewed periodically

## See Also

- [GitHub Actions Guide](github-actions.md) - GitHub Actions setup
- [GitLab CI Guide](gitlab-ci.md) - GitLab CI setup
- [How It Works](how-it-works.md) - Architecture overview
- [GitHub Actions Security Hardening](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [GitLab CI/CD Security](https://docs.gitlab.com/ee/ci/variables/#cicd-variable-security)
