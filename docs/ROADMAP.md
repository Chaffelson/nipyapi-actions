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

### Parameter Context Inheritance

**Status:** Not started

When `configure-params` is called, the directly attached parameter context may not contain the parameter being updated - it could be in an inherited parent context.

**Options:**
- Walk the inheritance chain to find where parameter is defined
- Add optional `parameter-context-id` input for explicit targeting
- Fail with helpful error suggesting which context to target

### Smart Flow Placement

**Status:** Not started

Add intelligent X/Y location calculation when deploying flows to avoid overlapping with existing process groups on the canvas.

## Medium-Term Features

### Anthropic Skills Integration

**Status:** Not started

Create Anthropic-format skill definitions for Claude:

```
skills/
├── deploy-flow/
│   └── SKILL.md
├── start-flow/
│   └── SKILL.md
└── ...
```

This would allow Claude to understand NiFi flow operations and help users build CI/CD pipelines.

### MCP Server Adapter

**Status:** Not started

Implement an MCP (Model Context Protocol) server that exposes nipyapi operations as tools for AI assistants like Cursor:

```python
# adapters/mcp/server.py
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "deploy_flow":
        result = nipyapi.ci.deploy_flow(**arguments)
        return result
```

### OIDC Authentication Testing

**Status:** Not started

Test and document OIDC authentication against external NiFi clusters for enterprise deployments.

## Long-Term Vision

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

### v1.0 - Multi-Platform CI/CD (December 2024)

- GitHub Actions support (stable)
- GitLab CI/CD support (stable)
- CLI in nipyapi client (`nipyapi.ci` module)
- GitHub and GitLab Flow Registry support
- Comprehensive test coverage for all operations
