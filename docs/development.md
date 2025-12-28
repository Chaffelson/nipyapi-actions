# Development Guide

Guide for developing, testing, and contributing to NiPyAPI Actions.

## Development Setup

This repository is designed to be developed alongside the main [nipyapi](https://github.com/Chaffelson/nipyapi) client repository, which provides the NiFi infrastructure for testing.

### 1. Clone Both Repositories

```bash
# Clone side by side
git clone https://github.com/Chaffelson/nipyapi.git
git clone https://github.com/Chaffelson/nipyapi-actions.git
```

Your directory structure should look like:
```
projects/
├── nipyapi/           # Main client library + Docker infrastructure
└── nipyapi-actions/   # This repository
```

### 2. Set Up the Main Client

Follow the setup instructions in the [nipyapi repository](https://github.com/Chaffelson/nipyapi) to:
- Create a Python virtual environment
- Install dependencies
- Generate certificates for NiFi
- Verify Docker is running

### 3. Set Up This Repository

```bash
cd nipyapi-actions

# Activate the virtual environment from the main client
source ../nipyapi/.venv/bin/activate  # On Windows: ..\nipyapi\.venv\Scripts\activate
```

No additional dependencies are required - nipyapi is already installed from your main client setup. The `requirements.txt` in this repository is only used by the GitHub Action when running in CI.

The `GH_REGISTRY_TOKEN` should already be configured in `../nipyapi/.env` as part of the main client setup - it's required for the nipyapi CI tests that use GitHub registry functions.

### 4. Start NiFi Infrastructure

```bash
# From nipyapi-actions directory
make infra-up      # Starts NiFi using nipyapi's Docker setup
make infra-ready   # Waits for NiFi to be available
```

You're now ready to run tests with `make test`.

## Repository Structure

```
nipyapi-actions/
├── action.yml              # GitHub Action definition (must be at root)
├── src/                    # Python command implementations
│   ├── main.py             # Entry point and routing
│   ├── ensure_registry.py  # ensure-registry command
│   ├── deploy_flow.py      # deploy-flow command
│   ├── start_flow.py       # start-flow command
│   ├── stop_flow.py        # stop-flow command
│   ├── cleanup.py          # cleanup command
│   ├── configure_params.py # configure-params command
│   └── get_status.py       # get-status command
├── tests/
│   ├── local.py            # Local Python testing script
│   └── flows/              # Test flow definitions
│       └── nipyapi_test_cicd_demo.json
├── scripts/
│   └── generate_secrets.py # Generate .secrets for act
├── .github/workflows/
│   └── ci.yml              # CI workflow (also canonical example)
├── docs/                   # Documentation
├── Makefile                # Development commands
└── requirements.txt        # Python dependencies
```

## Testing Modes

NiPyAPI Actions supports three testing modes, from fastest to most comprehensive.

### Which nipyapi Version is Used?

| Test Mode | nipyapi Version | Use Case |
|-----------|-----------------|----------|
| Local Python (`make test`) | Your local dev-installed version | Fast iteration on both repos simultaneously |
| Local act (`make test-act`) | From `requirements.txt` (GitHub URL) | Test the action as it will run in CI |
| GitHub CI | From `requirements.txt` (GitHub URL) | Final validation |

**Workflow for changes requiring nipyapi modifications:**

1. Make your nipyapi changes on a feature branch or your own fork
2. Push those changes to GitHub
3. Update `requirements.txt` to reference your branch/fork:
   ```
   # Example: feature branch
   git+https://github.com/Chaffelson/nipyapi.git@feature/my-branch#egg=nipyapi

   # Example: your fork
   git+https://github.com/yourusername/nipyapi.git@main#egg=nipyapi
   ```
4. Test with act or push to trigger GitHub CI

By default, `requirements.txt` should reference the main nipyapi release or the main branch once changes are merged.

### 1. Local Python Testing (Fastest)

Tests the Python command logic directly without GitHub Actions overhead.

**Prerequisites:**
- NiFi infrastructure running
- `GH_REGISTRY_TOKEN` environment variable set
- Python environment with dependencies

**When to use:**
- Rapid iteration on command logic
- Debugging Python code
- Testing nipyapi client integration

**Commands:**
```bash
# Start NiFi (uses nipyapi repo)
make infra-up
make infra-ready

# Run full workflow test
make test

# Test individual commands
make test-single CMD=ensure-registry
make test-single CMD=deploy-flow
make test-single CMD=start-flow
make test-single CMD=stop-flow
make test-single CMD=configure-params
make test-single CMD=get-status
make test-single CMD=cleanup

# Stop NiFi
make infra-down
```

**What it tests:**
- Python command implementations
- nipyapi client integration
- NiFi API interactions
- Output formatting

### 2. Local Act Testing (GitHub Actions Simulation)

Tests the full GitHub Action in a Docker container simulating GitHub Actions.

**Prerequisites:**
- Docker running
- `act` installed (`brew install act` on macOS)
- NiFi infrastructure running
- `.secrets` file (generated by make)

**When to use:**
- Testing `action.yml` composite action definition
- Verifying environment variable passing
- Validating action inputs/outputs
- Pre-push validation

**Commands:**
```bash
# Generate secrets file from nipyapi config
make generate-secrets

# Run CI workflow with act
make test-act

# Verbose output for debugging
make test-act-verbose
```

**What it tests:**
- `action.yml` syntax and structure
- Environment variable mapping
- Input/output handling
- Full workflow execution
- Docker container compatibility

**Notes:**
- Uses `host.docker.internal` to reach NiFi on host
- Requires `.secrets` file with credentials
- Run `make clean` after testing to remove secrets file

### 3. GitHub Actions CI (Production)

Runs automatically when code is pushed to GitHub.

**Trigger:** Push to main or PR creation

**When to use:**
- Final validation before merge
- Testing in real GitHub environment
- Verifying infrastructure setup

**What it tests:**
- Complete infrastructure setup (certs, Docker, NiFi)
- All action commands in sequence
- HTTP endpoint testing
- Parameter configuration
- Full cleanup verification

**View results:**
- Go to repository Actions tab
- Select the workflow run
- Review step outputs and logs

## Infrastructure Management

NiPyAPI Actions relies on the nipyapi client repository for NiFi infrastructure.

### Setup

```bash
# Clone nipyapi client (if not already present)
git clone https://github.com/Chaffelson/nipyapi.git ../nipyapi

# Or specify a different path
export NIPYAPI_INFRA=/path/to/nipyapi
```

### Commands

```bash
# Start NiFi with github-cicd profile
make infra-up

# Wait for NiFi to be ready
make infra-ready

# Stop NiFi
make infra-down
```

### Profiles

The nipyapi repository includes a `github-cicd` profile specifically configured for testing these actions, which is what the `make infra-up` command uses.

## Makefile Reference

```bash
make help              # Show all available commands

# Testing
make test              # Run full Python workflow test
make test-single CMD=X # Test single command
make test-act          # Run CI with act (local GitHub simulation)
make test-act-verbose  # Run with debug output

# Infrastructure (uses nipyapi repo)
make infra-up          # Start NiFi
make infra-down        # Stop NiFi
make infra-ready       # Wait for NiFi to be ready

# Utilities
make generate-secrets  # Create .secrets for act testing
make lint              # Check Python syntax
make clean             # Remove cache, secrets, temp files
make check-env         # Verify environment variables
make check-act         # Verify act and Docker installed
make check-infra       # Verify NiFi is running
```

## Test Flow

The CI uses `tests/flows/nipyapi_test_cicd_demo.json` which contains:

- **HandleHttpRequest**: Listens on port 8080
- **HandleHttpResponse**: Returns response with `version` header
- **StandardHttpContextMap**: Controller service for HTTP context
- **Parameter Context**: `nipyapi_test_cicd_params` with `version` parameter

The test flow validates:
1. Deploy flow from GitHub
2. Start flow (enables controllers, starts processors)
3. HTTP endpoint responds correctly
4. Configure parameters (update `version`)
5. HTTP endpoint returns new version
6. Cleanup removes all resources

## Adding New Commands

1. **Create command handler** in `src/`:
   ```python
   # src/my_command.py
   from os import getenv

   def run_my_command(set_output):
       """Execute my-command."""
       # Get inputs from environment
       some_input = getenv('NIFI_SOME_INPUT')

       # Implement logic using nipyapi
       import nipyapi
       result = nipyapi.some_function(some_input)

       # Set outputs
       set_output('result-id', result.id)
       set_output('success', 'true')

       print(f"Success: {result}")
   ```

2. **Register in main.py**:
   ```python
   COMMAND_REQUIREMENTS = {
       # ... existing commands ...
       'my-command': ['NIFI_SOME_INPUT'],
   }

   # In main():
   elif command == 'my-command':
       from my_command import run_my_command
       run_my_command(set_output)
   ```

3. **Add inputs/outputs to action.yml**:
   ```yaml
   inputs:
     some-input:
       description: 'Description of the input'
       required: true

   outputs:
     result-id:
       description: 'Description of the output'
   ```

4. **Add environment variable mapping** in action.yml:
   ```yaml
   env:
     NIFI_SOME_INPUT: ${{ inputs.some-input }}
   ```

5. **Add tests** to `tests/local.py`

6. **Integrate with CI** - Either:
   - Add steps to `.github/workflows/ci.yml` to test the new command as part of the canonical example, or
   - If the command requires a different test flow, add a new flow to `tests/flows/` and document it

7. **Update documentation** in `docs/commands.md`

## Contributing

### Code Style

- Follow PEP 8 guidelines
- Use meaningful variable names
- Add docstrings to functions
- Keep functions focused and small

### Testing Requirements

Before submitting a PR:
1. Run `make lint` - must pass
2. Run `make test` - full workflow must pass
3. Update documentation if adding features
4. Add tests for new functionality

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Push and create PR
5. Wait for CI to pass
6. Address review comments

## Debugging

### Enable Verbose Logging

```bash
# For act testing
make test-act-verbose

# For Python testing (add to local.py)
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Issues

**"Command X requires these inputs"**
- Check environment variables are set correctly
- Verify `action.yml` env mapping

**nipyapi authentication errors**
- Verify `NIFI_USERNAME` and `NIFI_PASSWORD`
- Check NiFi is running: `make check-infra`

**act cannot find action**
- Ensure `action.yml` is at repository root
- Check `--local-repository` path syntax

**SSL certificate errors**
- Regenerate certs: `cd ../nipyapi && make certs`
- Clean Docker: `cd ../nipyapi && make clean-docker`

## See Also

- [Commands Reference](commands.md) - All available commands
- [How It Works](how-it-works.md) - Architecture overview
- [nipyapi Documentation](https://nipyapi.readthedocs.io/) - Python client docs
- [Development Notes](development-notes.md) - Architectural decisions, roadmap, and session history for maintainers
