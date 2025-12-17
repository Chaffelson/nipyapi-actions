# Roadmap

Future development plans for NiPyAPI Actions and the nipyapi CLI.

## Current State

The project has achieved stable CI/CD support for:
- **GitHub Actions** - Via the `nipyapi-actions` action
- **GitLab CI/CD** - Via the `nipyapi` CLI directly

All CI operations are implemented in the `nipyapi` client library (`nipyapi.ci` module) and exposed via CLI.

## Short-Term Enhancements

### CLI Object Passing

**Status:** Not started

Currently, the CLI cannot easily pass complex NiFi objects between chained commands. For example:

```bash
# This doesn't work - PROC is a JSON string, not a ProcessorEntity object
PROC=$(nipyapi canvas get_processor abc-123 id)
nipyapi canvas update_processor "$PROC" --name "new-name"
```

**Solution:** Add type hints to nipyapi functions and enhance CLI to auto-deserialize JSON input when the expected type is a NiFi DTO. The `nipyapi.utils.load()` function already supports this.

### Parameter Context Inheritance in Actions

**Status:** Partially complete

The `nipyapi` CLI already has full support for inheritance-aware parameter configuration via
`nipyapi ci configure_inherited_params`. This function:

- Walks the inheritance chain to find where each parameter is defined
- Routes updates to the correct owning context
- Supports dry-run mode to preview changes
- Warns about asset replacement conflicts
- Handles sensitive parameters correctly

**Remaining work:**

- Expose `configure-inherited-params` command in `action.yml` (GitHub Actions)
- Add `configure-inherited-params` and `configure-inherited-params-dry-run` fragments to `fragments.yml` (GitLab)
- Add `dry-run` and `allow-override` inputs to the action
- Add outputs for `plan`, `warnings`, `errors`

**Workaround:** Users can call `nipyapi ci configure_inherited_params` directly in their workflows.

## Medium-Term Features

### External Parameter Providers

Support for external secrets managers:
- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault

Commands like `ensure-parameter-provider` and `refresh-secrets` for secret rotation workflows.

### GitHub Marketplace Publishing

Publish the GitHub Action to the GitHub Marketplace for easier discovery and installation.

### Additional Git Providers

- Bitbucket Flow Registry support
- Azure DevOps pipelines (if cross-compatible mechanism emerges)

## Contributing

Contributions toward any roadmap items are welcome. Please open an issue to discuss before starting work on larger features.

## Completed Milestones

### v1.0 - Multi-Platform CI/CD (December 2025)

- GitHub Actions support (stable)
- GitLab CI/CD support (stable)
- CLI in nipyapi client (`nipyapi.ci` module)
- GitHub and GitLab Flow Registry support
- Comprehensive test coverage for all operations
- Smart flow placement with intelligent X/Y location calculation to avoid overlapping process groups
