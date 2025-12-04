# NiFi CI/CD with GitHub Actions - Development Notes

**Purpose**: Internal development notes and context for maintainers and AI-assisted development sessions.
**Created**: 2025-11-10
**Last Updated**: 2025-12-04

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
| 2025-12-04 | Separate `change-version` command (not auto-replace) | Explicit user intent required; can downgrade or upgrade |

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
- `update_git_flow_ver()` - Change version of deployed Git-registry flow (NEW)

**Enhanced functions in `nipyapi.versioning`:**
- `revert_flow_ver(process_group, wait=False)` - Added `wait` parameter for synchronous operation

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

Key insights from development sessions that should guide future work.

### Tool Priority Sequence

When implementing or testing functionality, use this priority order:

1. **Actions first** - If an action command does what you need, use it (e.g., `python tests/local.py ensure-registry`)
2. **Helper functions** - If no action exists, use nipyapi helper functions (e.g., `nipyapi.versioning.deploy_git_registry_flow()`)
3. **Main client** - If no helper exists, use base nipyapi/NiFi API calls
4. **Create helpers** - If functionality is needed but missing, implement it in nipyapi first
5. **Create actions** - If helper functions are used frequently and other users would benefit, create an action command

This establishes a clear abstraction ladder and prevents reinventing wheels or working at the wrong level.

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
- [x] Test secret injection via configure-params (CI injects `github.run_id` as version parameter, verifies HTTP response returns exact value)
- [x] **change-version command** - See Section 8 for detailed working plan
- [x] **revert-flow command** - Revert local modifications to deployed flows
- [ ] Smart X/Y location calculation for flow deployment
- [ ] Flow validation command
- [ ] Wait-for-completion with queue monitoring
- [ ] **Parameter context inheritance support** - Handle cases where parameters are inherited from parent contexts (see Section 9)

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

### Session 7 (2025-12-04)
Added secret injection testing to CI. Uses `github.run_id` as a predictable dynamic value to verify parameters are correctly injected through the full pipeline (GitHub context -> action input -> NiFi parameter -> HTTP response). Updated local.py to use timestamp-based values for the same verification pattern. All three test modes pass (local Python, act, CI ready).

Began planning for `change-version` command - a significant feature to change the version of already-deployed flows. Created detailed working plan in Section 8 covering: test fixtures, nipyapi client work (4 phases), action implementation, and CI test plan. This is a multi-session effort requiring work in both nipyapi and nipyapi-actions repos.

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

## 8. Working Plan: change-version Command

**Status**: Planning
**Started**: 2025-12-04
**Scope**: Multi-session feature spanning nipyapi client and nipyapi-actions

### 8.1 Overview

Implement a `change-version` command that changes the version of an already-deployed, version-controlled process group to a different available version. This is distinct from `deploy-flow` which creates new deployments.

**Key Design Decisions:**
- Explicit command - never auto-replace existing flows
- Named `change-version` not `upgrade-flow` - can move to older or newer versions
- Requires process group to be under version control
- Should handle various process group states (clean, dirty, stale)

### 8.2 Test Fixtures Required

Before implementation, we need test data with various version types:

**In nipyapi-actions repo:**
- [ ] Create git tag `v1.0.0-test` on an older commit of cicd-demo-flow
- [ ] Create git tag `v1.1.0-test` on a different commit
- [ ] Document the commit SHAs for these tags

**Version types to test:**
| Type | Example | How NiFi sees it |
|------|---------|------------------|
| Commit SHA | `97549b88f2e1...` | Direct version reference |
| Git tag | `v1.0.0` | Resolves to commit SHA |
| Branch HEAD | `main` | Latest commit on branch |

### 8.3 nipyapi Client Work (in nipyapi repo)

**Phase 1: Query Functions**

- [ ] `get_git_registry_flow_version_info(process_group)` - Get version control info from deployed PG
- [ ] Verify `list_git_registry_flow_versions()` returns all available versions including tagged commits
- [ ] Test that tags are visible/resolvable through the GitHub registry client

**Phase 2: Change Version Function**

- [ ] `change_git_registry_flow_version(process_group, target_version, branch=None)`
  - Takes a deployed ProcessGroupEntity
  - Takes target version (commit SHA or tag)
  - Optional branch parameter
  - Returns updated ProcessGroupEntity or status

**Implementation approach:**
```python
def change_git_registry_flow_version(process_group, target_version, branch=None):
    """
    Change the version of a deployed Git-registry flow.

    Args:
        process_group: Already-deployed ProcessGroupEntity under version control
        target_version: Commit SHA or tag to change to
        branch: Optional branch (uses current if not specified)

    Returns:
        Updated ProcessGroupEntity
    """
    # 1. Get current version control info
    # 2. Verify target_version exists in available versions
    # 3. Initiate version control update via NiFi API
    # 4. Wait for completion
    # 5. Return updated process group
```

**Phase 3: State Handling Tests**

Test `change_git_registry_flow_version()` with process groups in various states:

| Initial State | Action | Expected Result |
|---------------|--------|-----------------|
| UP_TO_DATE at v1 | Change to v2 | Success, now at v2 |
| UP_TO_DATE at v2 | Change to v1 | Success, now at v1 (downgrade) |
| LOCALLY_MODIFIED | Change to v2 | ? (test behavior - may need force flag) |
| STALE (newer available) | Change to latest | Success |
| STALE | Change to specific older | Success |

**Phase 4: Error Handling**

- [ ] Target version doesn't exist
- [ ] Process group not under version control
- [ ] Process group is running (may need to stop first?)
- [ ] Network/API errors during update

### 8.4 nipyapi-actions Work (in this repo)

**After nipyapi client work is complete:**

**New Command: `change-version`**

```yaml
# action.yml additions
inputs:
  # For change-version command
  target-version:
    description: 'Version (commit SHA or tag) to change to'
    required: false
    default: ''
```

**New file: `src/change_version.py`**

```python
def run_change_version(set_output):
    process_group_id = getenv('NIFI_PROCESS_GROUP_ID')
    target_version = getenv('NIFI_TARGET_VERSION')
    branch = getenv('NIFI_FLOW_BRANCH') or None

    # Get process group
    # Verify it's under version control
    # Call nipyapi.versioning.change_git_registry_flow_version()
    # Set outputs: previous_version, new_version, success
```

**Outputs:**
- `previous-version` - Version before change
- `new-version` - Version after change
- `success` - Boolean

### 8.5 CI Test Plan

**Test workflow additions:**

```yaml
# After deploy-flow, before cleanup:

# Test 1: Change to specific older version (tag)
- name: Test change-version (to tag)
  uses: ./
  with:
    command: change-version
    process-group-id: ${{ steps.deploy.outputs.process-group-id }}
    target-version: 'v1.0.0-test'

- name: Verify version changed
  run: |
    # Check get-status shows correct version

# Test 2: Change back to latest
- name: Test change-version (to latest)
  uses: ./
  with:
    command: change-version
    process-group-id: ${{ steps.deploy.outputs.process-group-id }}
    target-version: ''  # Empty = latest
```

### 8.6 Implementation Order

1. **Create test fixtures** - Tags in nipyapi-actions repo
2. **nipyapi client Phase 1** - Query functions, verify tag visibility
3. **nipyapi client Phase 2** - Implement `change_git_registry_flow_version()`
4. **nipyapi client Phase 3** - State handling tests
5. **nipyapi client Phase 4** - Error handling
6. **Push nipyapi changes** - Update requirements.txt to reference branch
7. **nipyapi-actions command** - Implement `change-version` command
8. **CI tests** - Add change-version tests to workflow
9. **Documentation** - Update commands.md

### 8.7 Design Decisions

- **Always use UUID, never name**: The `change-version` command must only accept `process-group-id` (UUID), not process group name. This prevents ambiguity when multiple flows with the same name exist on the canvas. If we ever add name-based lookup as a convenience, it must fail with a clear error if multiple matches are found.

### 8.8 Resolved Questions

- [x] Does NiFi require flow to be stopped before version change? **No, version change works while running**
- [x] How does LOCALLY_MODIFIED state affect version changes? **NiFi requires revert first - cannot change version with local modifications**
- [x] Can we change version while flow is running? **Yes, tested and working**
- [ ] How are parameter context changes handled during version change?
- [ ] What happens to parameter values when changing versions?

### 8.9 Session Log

**2025-12-04**: Initial planning. Identified need for nipyapi client functions before action implementation. Documented test fixture requirements and implementation phases.

**2025-12-04 (continued)**: Implemented `resolve_version_ref()` function in `main.py` to resolve tags/branches to commit SHAs via GitHub API. Created test fixtures: two flow versions in repo, tagged original as `v1.0.0`. Verified tag-based deployment works. Added `--no-cleanup` flag to local.py for debugging. Added design decision: always use UUID, never name for process group identification.

**2025-12-04 (session 3)**: Implemented version change functionality end-to-end:

**nipyapi changes:**
- Added `update_git_flow_ver(process_group, target_version=None, branch=None)` to `nipyapi/versioning.py`
- Enhanced `revert_flow_ver()` with `wait=False` parameter - when `wait=True`, waits for revert to complete
- Added comprehensive tests for `update_git_flow_ver` covering: specific version, latest, no-op, invalid version, unversioned PG, locally modified (requires revert first)
- Added fixtures to conftest.py: `fix_git_reg_client`, `fix_deployed_git_flow`

**nipyapi-actions changes:**
- New command: `change-version` (`src/change_version.py`) - changes deployed flow to specified version or latest
- New command: `revert-flow` (`src/revert_flow.py`) - reverts local modifications
- Updated `action.yml` with new inputs (`target-version`) and outputs
- Updated CI workflow with tests for both commands
- Updated documentation: README.md, commands.md

**Key findings:**
- NiFi does NOT allow version changes when the process group has local modifications (LOCALLY_MODIFIED state). Must revert first, then change version.
- Parameter context value changes do NOT trigger LOCALLY_MODIFIED - only structural changes (add/remove/rename processors, connections, etc.) trigger this state.

**2025-12-04 (session 3 continued)**: Refined CI tests and utilities:

- Added `modify_processor(process_group_id)` utility to `src/utils.py` - renames first processor to trigger LOCALLY_MODIFIED state
- Updated CI workflow to use `get-status` action to verify LOCALLY_MODIFIED state before testing `revert-flow` (tests get-status in meaningful context)
- Fixed CI verifications to actually check values (not just declare success)
- Removed hacky embedded Python in favor of clean utility function

**CI test flow for version operations:**
1. `change-version` to v1.0.0 (verify SHA matches)
2. `change-version` to latest (verify previous was v1.0.0, new is different)
3. `modify_processor()` utility to create structural change
4. `get-status` to verify LOCALLY_MODIFIED
5. `revert-flow` to restore
6. Verify state is UP_TO_DATE

---

## 9. Parameter Context Inheritance

### 9.1 Problem Statement

NiFi parameter contexts support inheritance - a context can inherit parameters from one or more parent contexts. When `configure-params` is called on a process group, the directly attached context may not contain the parameter being updated; it could be defined in an inherited parent context.

**Current behavior:** `configure-params` only updates parameters in the directly attached context. If the parameter is inherited, the update will fail or create a new parameter that shadows the inherited one.

### 9.2 Test Scenario Needed

Create a test fixture with:
```
TopLevelContext (defines: api_url, timeout)
    └── ChildContext (inherits from TopLevelContext, defines: version)
        └── ProcessGroup (uses ChildContext)
```

Test cases:
1. Update `version` (defined in direct context) - should work
2. Update `api_url` (defined in parent context) - current behavior: fails or shadows
3. Update non-existent parameter - should fail with clear error

### 9.3 Potential Solutions

**Option A: Walk the inheritance chain**
- When updating a parameter, check if it exists in the direct context
- If not, walk up the inheritance chain to find where it's defined
- Update the parameter in the correct context
- Consideration: May require additional permissions to modify parent contexts

**Option B: Explicit context targeting**
- Add optional `parameter-context-id` input to `configure-params`
- If provided, update that specific context (user knows which context has the param)
- If not provided, use current behavior (direct context only)

**Option C: Fail with helpful error**
- Detect when parameter exists only in inherited context
- Fail with clear error message indicating which context contains the parameter
- User can then use Option B or update via NiFi UI

### 9.4 Implementation Notes

- `nipyapi.parameters.get_parameter_context()` returns inheritance info
- Need to check `inherited_parameter_contexts` field
- May need new nipyapi helper: `find_parameter_context_for_param(pg_id, param_name)`

### 9.5 Status

- [ ] Create test fixture with inherited parameter contexts
- [ ] Document current behavior with inherited parameters
- [ ] Decide on solution approach
- [ ] Implement chosen solution
- [ ] Add CI tests

---

*This document is maintained as part of the nipyapi-actions repository.*
