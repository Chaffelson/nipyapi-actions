# GitHub App Setup for NiFi Flow Registry

This guide describes how to configure a GitHub App for use with NiFi's GitHub Flow Registry Client. GitHub Apps are the enterprise-preferred authentication method, providing better security, audit trails, and fine-grained permissions compared to Personal Access Tokens (PATs).

## Prerequisites

- GitHub account with permission to create Apps (personal account or organization admin)
- A repository to store NiFi flow definitions

## Step 1: Create a GitHub App

1. Navigate to GitHub App creation:
   - Personal account: https://github.com/settings/apps/new
   - Organization: https://github.com/organizations/YOUR_ORG/settings/apps/new

2. Configure basic settings:
   - **GitHub App name**: A unique name (e.g., `NiFi-Flow-Registry-YourOrg`)
   - **Homepage URL**: Your organization URL or repository URL
   - **Webhook**: Uncheck "Active" (not required for flow registry)

3. Set repository permissions:
   - **Contents**: Read and write (required for flow read/write operations)
   - **Metadata**: Read-only (required, auto-selected)

4. Set installation scope:
   - **Only on this account**: App can only be installed on repositories owned by this account/org
   - **Any account**: App can be installed on any GitHub account (like marketplace apps)

   **Important:** If you select "Only on this account", the App can only be installed on repositories within the same account or organization where the App was created. To use the App with repositories in a different account, you must either:
   - Create the App in the account that owns the target repositories, OR
   - Select "Any account" to allow cross-account installation, OR
   - Transfer App ownership to the account that owns the repositories

5. Click **Create GitHub App**

## Step 2: Generate a Private Key

1. On the App settings page, scroll to **Private keys**
2. Click **Generate a private key**
3. Save the downloaded `.pem` file securely
4. This file is required for authentication and cannot be recovered if lost

## Step 3: Record App ID

From the App settings page, note the **App ID** (a number at the top of the General settings page, e.g., `123456`). This is required for NiFi configuration.

## Step 4: Install the App

1. From the App settings page, click **Install App** in the left sidebar
2. Select the account or organization
3. Choose installation scope:
   - **All repositories**: Full access (not recommended)
   - **Only select repositories**: Choose specific repos for flow storage
4. Click **Install**


## Summary of Required Credentials

After completing setup, you should have:

| Credential | Description | Storage |
|------------|-------------|---------|
| **App ID** | Numeric identifier for the App | NiFi registry client configuration |
| **Private Key** | PEM file (converted to PKCS#8) | NiFi registry client configuration (sensitive property) |

## Security Considerations

- Store the private key securely (secrets manager, encrypted storage)
- Private keys cannot be recovered - generate a new one if lost
- Rotate private keys periodically per your security policy
- Use minimal repository permissions (only repos needed for flow storage)
- Installation tokens are short-lived (1 hour) and automatically managed

## NiFi Registry Client Configuration

Configure the NiFi GitHub Flow Registry Client with these properties:

| Property | Value | Notes |
|----------|-------|-------|
| **GitHub API URL** | `https://api.github.com/` | For GitHub.com |
| **Repository Owner** | Your GitHub username or org | e.g., `Chaffelson` |
| **Repository Name** | Repository name | e.g., `nipyapi-actions` |
| **Repository Path** | Path within repo | e.g., `tests` (empty = repo root) |
| **Authentication Type** | `App Installation` | Select from dropdown |
| **App ID** | Your App ID | e.g., `2432460` |
| **App Private Key** | PKCS#8 private key | See key format below |
| **Default Branch** | `main` | Or your default branch |

### Private Key Format

NiFi accepts the private key in the standard RSA format that GitHub provides. The key starts with `-----BEGIN RSA PRIVATE KEY-----` and can be used directly without conversion.

Simply paste the entire contents of the downloaded `.pem` file into the **App Private Key** field in NiFi.

### Understanding Buckets and Flows

In the GitHub registry, directories map to NiFi concepts:

```
repository-root/
└── {Repository Path}/     <-- Configured on registry client
    └── {bucket}/          <-- Directory = Bucket
        └── {flow}.json    <-- JSON file = Flow
```

Example with `Repository Path: tests`:
```
nipyapi-actions/
└── tests/
    └── flows/             <-- Bucket named "flows"
        └── nipyapi_test_cicd_demo.json
```

## Troubleshooting

### "No buckets available" when starting version control

**Symptom:** Import flow works, but "Start version control" shows no buckets.

**Cause:** The GitHub App has read-only permissions. Write operations require read+write.

**Solution:**
1. Go to App settings → Permissions & events
2. Change **Contents** from `Read-only` to `Read and write`
3. Save changes
4. Go to the Installation and accept the updated permissions
5. **Delete and recreate** the NiFi registry client (forces new token with updated permissions)

### Permission changes not taking effect

**Symptom:** Updated App permissions but NiFi still behaves as before.

**Cause:** NiFi caches the installation access token (valid for 1 hour).

**Solution:** Either:
- Delete and recreate the registry client in NiFi (immediate), OR
- Wait up to 1 hour for the cached token to expire and automatically refresh

### Cannot install App on repository

**Symptom:** The App doesn't appear in the installation options for your repository.

**Cause:** The App was created with "Only on this account" in a different account than the repository owner.

**Solution:** Either:
- Transfer App ownership to the account that owns the repository
- Recreate the App in the correct account
- Change App settings to "Any account" (if cross-org installation is acceptable)

### Cannot find repository or authentication fails

**Checklist:**
- [ ] App is installed on the correct repository
- [ ] Repository Owner and Repository Name are correct (case-sensitive)
- [ ] App ID matches the App settings page
- [ ] Private key is the complete PEM file contents (including BEGIN/END lines)
- [ ] Private key belongs to the correct App (not a different one)

### Read operations work but write fails

This indicates a permissions mismatch:
- **Contents: Read-only** = Can import flows, cannot version control
- **Contents: Read and write** = Full functionality

## Comparison: PAT vs GitHub App

| Aspect | Personal Access Token | GitHub App |
|--------|----------------------|------------|
| **Tied to** | User account | Organization/App |
| **Token rotation** | Manual | Automatic (1 hour) |
| **Audit trail** | User-level | App-level |
| **Permission scope** | User's access | Explicitly configured |
| **Enterprise policy** | Often prohibited | Usually preferred |
| **Setup complexity** | Simple | More steps |

## Next Steps

For CI/CD integration with NiPyAPI Actions, see the [Commands Reference](commands.md) for `ensure-registry` and `deploy-flow` commands.
