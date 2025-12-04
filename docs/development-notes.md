# NiFi CI/CD with GitHub Actions - Development Notes

**Purpose**: Internal development notes and context for maintainers and AI-assisted development sessions.
**Created**: 2025-11-10
**Last Updated**: 2025-12-03

This document contains architectural decisions, roadmap, and session history for the nipyapi-actions project. For user-facing documentation, see the other files in this directory.

---

## 1. Key Decisions Log
| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-11-10 | GitHub Registry Client is primary approach | Native NiFi integration, no separate Registry needed |
| 2025-11-10 | Cluster pulls from GitHub (not Action pushes) | Validates same pathway as production |
| 2025-11-10 | Feature branch workflow | Feature → PR (test) → main (prod) |
| 2025-11-27 | Single action with commands (not multiple actions) | Marketplace-compatible, centralizes setup |
| 2025-11-27 | Add "env" profile to nipyapi | Pure env var configuration without profiles file |
| 2025-11-27 | GitHub registry config NOT in nipyapi profiles | Clean separation of concerns |
| 2025-12-03 | Consolidate nipyapi-workflow into nipyapi-actions | Single repo, CI as canonical example |
| 2025-12-03 | NIFI_ prefix for action env vars | Avoid namespace clashes with system vars |
| 2025-12-03 | PAT required for NiFi GitHub Registry Client | GITHUB_TOKEN doesn't work (app token vs user token) |
| 2025-12-03 | Read-only fine-grained PAT for public repos | Minimal permissions, scoped to single repo |

---

## 2. Implementation Summary

### nipyapi Client Library Changes

Branch: `feature/github-cicd-versioning`

**New functions in `nipyapi.versioning`:**
- `list_git_registry_buckets()` - List buckets from GitHub registry client
- `get_git_registry_bucket()` - Get specific bucket by name
- `list_git_registry_flows()` - List flows in a bucket
- `get_git_registry_flow()` - Get specific flow by name
- `list_git_registry_flow_versions()` - List versions (commits) of a flow
- `deploy_git_registry_flow()` - Deploy flow from GitHub to canvas

**New function in `nipyapi.canvas`:**
- `schedule_all_controllers()` - Bulk enable/disable controller services in a process group

**New profile support in `nipyapi.profiles`:**
- "env" profile - Pure environment variable configuration without profiles file

**Bug fix:**
- Version sorting in `deploy_git_registry_flow()` - Sort by timestamp to get latest

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

## 3. Lessons Learned

Key insights from development sessions that should guide future work:

### Code Architecture

- **Prefer nipyapi helper functions over base API calls.** If a helper function doesn't exist for what you need, implement it in the main nipyapi client first, then use it in the action command. This maintains separation of concerns - the action orchestrates, nipyapi handles NiFi API complexity.

- **Don't re-implement nipyapi functionality.** Use existing patterns like `profiles.switch()` for authentication, `nipyapi.utils.getenv()` for environment variables, etc. The client already handles edge cases.

- **Version sorting is not deterministic.** The NiFi API may return flow versions in any order. Always sort by timestamp when finding "latest" version.

### Environment and Testing

- **Use the main nipyapi client's virtual environment.** Don't create a separate venv for the actions repo - nipyapi is the only dependency and it's already installed.

- **Make targets over direct commands.** Use `make test`, `make infra-up` etc. rather than direct pytest/docker commands. Make targets handle environment setup correctly.

- **Local Python tests use local nipyapi; act/CI use requirements.txt.** This means you can iterate on both repos locally, but must push nipyapi changes before they'll work in act or GitHub CI.

### NiFi Specifics

- **GITHUB_TOKEN doesn't work for NiFi Registry Client.** NiFi calls GitHub's `/user` endpoint which requires a user PAT, not an app installation token. This was a significant discovery.

- **IGNORE_CHANGES is the safer parameter default.** This imports new parameters but preserves existing values, preventing accidental overwrites of environment-specific settings.

- **Sensitive parameter values are never versioned.** Only the parameter name and sensitive flag are stored. Values must be set after deployment.

- **Contain all dependencies in the versioned process group.** Controller services at root canvas level won't exist in target environments. Everything the flow needs must be inside the top-level process group.

### Documentation

- **Keep user docs and maintainer docs separate.** User-facing docs (README, setup, commands, etc.) should be clean and focused. Development notes are for maintainers and AI context.

---

## 4. Known Limitations

- NiFi GitHub Registry Client requires PAT (GITHUB_TOKEN doesn't work)
- Repository path + bucket + flow structure must match exactly
- Version = Git commit SHA (not semantic versions)
- Action re-authenticates on each step (stateless)
- Parameter contexts must exist before configure-params
- Cleanup requires process-group-id (must track from deploy)

---

## 5. Future Enhancements

### 5.1 Short-term
- [ ] Test secret injection via configure-params (documented but not verified in CI)
- [ ] Test tag-based releases (deploy specific git tags as versions)
- [ ] Smart X/Y location calculation for flow deployment
- [ ] Flow validation command
- [ ] Wait-for-completion with queue monitoring

### 5.2 Medium-term
- [ ] Test with OIDC authentication against external NiFi cluster
- [ ] Consider adding GitHub registry function tests to main nipyapi CI (requires GH_REGISTRY_TOKEN secret)
- [ ] GitLab, Azure DevOps, Bitbucket provider testing
- [ ] Environment-based workflow patterns
- [ ] Approval gates for production deployments

### 5.3 Long-term
- [ ] External parameter providers (AWS Secrets Manager, HashiCorp Vault)
- [ ] Ensure-parameter-provider action (similar to ensure-registry for external secrets managers)
- [ ] Refresh-secrets command for secret rotation
- [ ] GitHub Marketplace publishing

---

## 6. Session History

### Session 6 (2025-12-03)
Complete documentation restructure: Created setup.md, gitops.md, commands.md, how-it-works.md, security.md, development.md. Restructured README. Added GitOps best practices, parameter handling, flow design guidance.

### Session 5 (2025-12-03)
Consolidated repos, simplified env vars (NIFI_ prefix), fixed PAT requirement, implemented fine-grained PAT for public repos, CI passing.

### Sessions 1-4 (2025-11-10 to 2025-11-27)
Initial implementation: nipyapi helper functions, "env" profile, single action with 7 commands, three testing modes.

---

## 7. Reference Links

- [NiFi Documentation](https://nifi.apache.org/docs.html)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [nipyapi Documentation](https://nipyapi.readthedocs.io/)
- [Fine-grained PATs](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#fine-grained-personal-access-tokens)
- [act - Local GitHub Actions Runner](https://github.com/nektos/act)

---

*This document is maintained as part of the nipyapi-actions repository.*
