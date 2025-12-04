# NiFi CI/CD with GitHub Actions - Development Notes

**Purpose**: Development notes and context for maintainers.
**Last Updated**: 2025-12-04

For user-facing documentation, see the other files in this directory.

---

## 1. Implementation Summary

### nipyapi Client Library Support

This action requires nipyapi with the following features (available in nipyapi 1.1.0+):

**Git Registry Functions (`nipyapi.versioning`):**
- `list_git_registry_buckets()` - List buckets from GitHub registry client
- `get_git_registry_bucket()` - Get specific bucket by name
- `list_git_registry_flows()` - List flows in a bucket
- `get_git_registry_flow()` - Get specific flow by name
- `list_git_registry_flow_versions()` - List versions (commits) of a flow
- `deploy_git_registry_flow()` - Deploy flow from GitHub to canvas
- `update_git_flow_ver()` - Change version of deployed Git-registry flow
- `revert_flow_ver(wait=True)` - Revert local modifications with synchronous option

**Other Functions:**
- `schedule_all_controllers()` - Bulk enable/disable controller services
- `profiles.switch('env')` - Pure environment variable configuration

### Environment Variable Flow

```
action.yml input (nifi-api-endpoint)
    ↓ action.yml env block
NIFI_API_ENDPOINT (env var)
    ↓ nipyapi.profiles.switch('env')
    ↓ nipyapi ENV_VAR_MAPPINGS
nipyapi.config.nifi_config.host
```

---

## 2. Lessons Learned

### Abstraction Ladder

When implementing or testing functionality, use this priority order:

1. **Actions first** - If an action command does what you need, use it
2. **Helper functions** - Use nipyapi helper functions if no action exists
3. **Main client** - Use base nipyapi/NiFi API calls if no helper exists
4. **Create helpers** - Implement in nipyapi first if functionality is missing
5. **Create actions** - Create action command if helper is frequently needed

### Code Architecture

- **Prefer nipyapi helper functions over base API calls.** Implement new helpers in nipyapi first, then use in action commands.
- **Don't re-implement nipyapi functionality.** Use existing patterns like `profiles.switch()` and `nipyapi.utils.getenv()`.
- **Version sorting is not deterministic.** Always sort by timestamp when finding "latest" version.

### Environment and Testing

- **Use the main nipyapi client's virtual environment.** Don't create a separate venv.
- **Make targets over direct commands.** Use `make test`, `make infra-up` etc.
- **Local Python tests use local nipyapi; act/CI use requirements.txt.** Push nipyapi changes before they'll work in CI.

### NiFi Specifics

- **GITHUB_TOKEN doesn't work for NiFi Registry Client.** NiFi requires a user PAT, not an app installation token.
- **IGNORE_CHANGES is the safer parameter default.** Preserves existing values during import.
- **Sensitive parameter values are never versioned.** Only the name and sensitive flag are stored.
- **Contain all dependencies in the versioned process group.** Controller services at root level won't exist in target environments.
- **LOCALLY_MODIFIED state blocks version changes.** Must revert first, then change version.
- **Parameter value changes don't trigger LOCALLY_MODIFIED.** Only structural changes (add/remove/rename processors) trigger this state.
- **Processors must be stopped before renaming.** API returns 409 Conflict if processor is running.

---

## 3. Known Limitations

- NiFi GitHub Registry Client requires PAT (GITHUB_TOKEN doesn't work)
- Repository path + bucket + flow structure must match exactly
- Version = Git commit SHA (not semantic versions)
- Action re-authenticates on each step (stateless)
- Parameter contexts must exist before configure-params
- Cleanup requires process-group-id (must track from deploy)

---

## 4. Future Enhancements

### Short-term
- [ ] Smart X/Y location calculation for flow deployment
- [ ] Flow validation command
- [ ] Wait-for-completion with queue monitoring
- [ ] Parameter context inheritance support (see Section 5)

### Medium-term
- [ ] Test with OIDC authentication against external NiFi cluster
- [ ] GitLab, Azure DevOps, Bitbucket provider testing
- [ ] Environment-based workflow patterns
- [ ] Approval gates for production deployments

### Long-term
- [ ] External parameter providers (AWS Secrets Manager, HashiCorp Vault)
- [ ] Ensure-parameter-provider action
- [ ] Refresh-secrets command for secret rotation
- [ ] GitHub Marketplace publishing

---

## 5. Parameter Context Inheritance

### Problem Statement

NiFi parameter contexts support inheritance. When `configure-params` is called, the directly attached context may not contain the parameter being updated - it could be in an inherited parent context.

**Current behavior:** Only updates parameters in the directly attached context.

### Potential Solutions

**Option A: Walk the inheritance chain** - Find where parameter is defined and update there.

**Option B: Explicit context targeting** - Add optional `parameter-context-id` input.

**Option C: Fail with helpful error** - Detect inherited parameter and suggest which context to target.

### Status
- [ ] Create test fixture with inherited parameter contexts
- [ ] Document current behavior
- [ ] Decide on solution approach
- [ ] Implement chosen solution

---

## 6. Reference Links

- [NiFi Documentation](https://nifi.apache.org/docs.html)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [nipyapi Documentation](https://nipyapi.readthedocs.io/)
- [Fine-grained PATs](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#fine-grained-personal-access-tokens)
- [act - Local GitHub Actions Runner](https://github.com/nektos/act)
