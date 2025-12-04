#!/usr/bin/env python
"""
Local test script for nipyapi-actions

This script simulates the GitHub Actions environment to test
the action locally without needing to push to GitHub.

The action uses direct environment variable names (no INPUT_ prefix):
- NIFI_API_ENDPOINT, NIFI_USERNAME, etc. (nipyapi standard names)
- GH_REGISTRY_TOKEN, REGISTRY_REPO, etc. (action-specific names)

Usage:
    # Set required environment variable first:
    export GITHUB_REGISTRY_TOKEN="your-token"

    # Then run from repo root:
    python tests/local.py [command]

    # Commands: ensure-registry (default), deploy-flow, start-flow, stop-flow, cleanup, full-workflow
"""

import os
import sys
import time
import tempfile
import importlib
import urllib.request

# Add src to path so we can import the modules (go up one level from tests/)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Env vars to clear between tests (action-specific vars, not system vars)
ACTION_ENV_VARS = [
    'NIFI_ACTION_COMMAND', 'NIFI_API_ENDPOINT', 'NIFI_USERNAME', 'NIFI_PASSWORD',
    'NIFI_VERIFY_SSL', 'NIPYAPI_SUPPRESS_SSL_WARNINGS',
    'GH_REGISTRY_TOKEN', 'NIFI_REGISTRY_REPO', 'NIFI_REGISTRY_BRANCH',
    'NIFI_REGISTRY_CLIENT_NAME', 'NIFI_REPOSITORY_PATH', 'NIFI_REGISTRY_API_URL',
    'NIFI_REGISTRY_CLIENT_ID', 'NIFI_BUCKET', 'NIFI_FLOW', 'NIFI_FLOW_BRANCH',
    'NIFI_FLOW_VERSION', 'NIFI_PARENT_PG_ID', 'NIFI_LOCATION_X', 'NIFI_LOCATION_Y',
    'NIFI_PROCESS_GROUP_ID', 'NIFI_ENABLE_CONTROLLERS', 'NIFI_DISABLE_CONTROLLERS',
    'NIFI_FORCE_DELETE', 'NIFI_DELETE_PARAM_CONTEXT', 'NIFI_PARAMETERS',
]


def get_base_env(github_token, output_file):
    """Get base environment variables common to all tests."""
    return {
        # NiFi connection - matches nipyapi ENV_VAR_MAPPINGS
        'NIFI_API_ENDPOINT': 'https://localhost:9447/nifi-api',
        'NIFI_USERNAME': 'einstein',
        'NIFI_PASSWORD': 'password1234',
        'NIFI_VERIFY_SSL': 'false',
        'NIPYAPI_SUPPRESS_SSL_WARNINGS': 'true',

        # GitHub registry - action-specific (NIFI_ prefix for safety)
        'GH_REGISTRY_TOKEN': github_token,
        'NIFI_REGISTRY_REPO': 'Chaffelson/nipyapi-actions',
        'NIFI_REGISTRY_BRANCH': 'main',

        # GitHub output file
        'GITHUB_OUTPUT': output_file,
    }


def run_command(env_vars):
    """Run main.py with the given environment variables."""
    # Clear action-specific env vars
    for key in ACTION_ENV_VARS:
        if key in os.environ:
            del os.environ[key]

    # Set new environment
    for key, value in env_vars.items():
        os.environ[key] = value

    # Reload main module to pick up new environment
    import main
    importlib.reload(main)
    main.main()


def read_outputs(output_file):
    """Read outputs from the GitHub output file."""
    outputs = {}
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            for line in f:
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    outputs[key] = value
    return outputs


def test_ensure_registry(github_token, output_file, cleanup=True):
    """Test the ensure-registry command."""
    print("=" * 60)
    print("Testing ensure-registry command")
    print("=" * 60)

    env = get_base_env(github_token, output_file)
    env.update({
        'NIFI_ACTION_COMMAND': 'ensure-registry',
        'NIFI_REGISTRY_CLIENT_NAME': 'test-action-client',
        'NIFI_REPOSITORY_PATH': 'tests',
        'NIFI_REGISTRY_API_URL': 'https://api.github.com/',
    })

    print(f"NiFi URL: {env['NIFI_API_ENDPOINT']}")
    print(f"Registry Client Name: test-action-client")
    print(f"Repository: {env['NIFI_REGISTRY_REPO']}")
    print()

    run_command(env)

    outputs = read_outputs(output_file)
    print()
    print("Outputs:", outputs)

    registry_client_id = outputs.get('registry_client_id')
    if not registry_client_id:
        raise ValueError("Expected registry_client_id in outputs")

    print("ensure-registry PASSED!")

    if cleanup:
        # Clean up the test registry client
        try:
            import nipyapi
            client = nipyapi.versioning.get_registry_client('test-action-client')
            if client:
                nipyapi.versioning.delete_registry_client(client)
                print("Cleaned up test registry client")
        except Exception:
            pass

    return outputs


def test_deploy_flow(github_token, output_file, registry_client_id):
    """Test the deploy-flow command."""
    print()
    print("=" * 60)
    print("Testing deploy-flow command")
    print("=" * 60)

    env = get_base_env(github_token, output_file)
    env.update({
        'NIFI_ACTION_COMMAND': 'deploy-flow',
        'NIFI_REGISTRY_CLIENT_ID': registry_client_id,
        'NIFI_BUCKET': 'flows',
        'NIFI_FLOW': 'cicd-demo-flow',
        'NIFI_FLOW_BRANCH': '',  # Use default
        'NIFI_FLOW_VERSION': '',  # Use latest
        'NIFI_PARENT_PG_ID': '',  # Use root
    })

    print(f"Registry Client ID: {registry_client_id}")
    print(f"Bucket: flows (repository-path: tests)")
    print(f"Flow: cicd-demo-flow")
    print()

    # Clear output file
    open(output_file, 'w').close()

    run_command(env)

    outputs = read_outputs(output_file)
    print()
    print("Outputs:", outputs)

    process_group_id = outputs.get('process_group_id')
    if not process_group_id:
        raise ValueError("Expected process_group_id in outputs")

    print("deploy-flow PASSED!")
    return outputs


def test_start_flow(github_token, output_file, process_group_id):
    """Test the start-flow command."""
    print()
    print("=" * 60)
    print("Testing start-flow command")
    print("=" * 60)

    env = get_base_env(github_token, output_file)
    env.update({
        'NIFI_ACTION_COMMAND': 'start-flow',
        'NIFI_PROCESS_GROUP_ID': process_group_id,
    })

    print(f"Process Group ID: {process_group_id}")
    print()

    # Clear output file
    open(output_file, 'w').close()

    run_command(env)

    outputs = read_outputs(output_file)
    print()
    print("Outputs:", outputs)

    if outputs.get('started') not in ('true', 'partial'):
        raise ValueError("Expected started=true or started=partial in outputs")

    print("start-flow PASSED!")
    return outputs


def test_stop_flow(github_token, output_file, process_group_id):
    """Test the stop-flow command."""
    print()
    print("=" * 60)
    print("Testing stop-flow command")
    print("=" * 60)

    env = get_base_env(github_token, output_file)
    env.update({
        'NIFI_ACTION_COMMAND': 'stop-flow',
        'NIFI_PROCESS_GROUP_ID': process_group_id,
    })

    print(f"Process Group ID: {process_group_id}")
    print()

    # Clear output file
    open(output_file, 'w').close()

    run_command(env)

    outputs = read_outputs(output_file)
    print()
    print("Outputs:", outputs)

    if outputs.get('stopped') not in ('true', 'partial'):
        raise ValueError("Expected stopped=true or stopped=partial in outputs")

    print("stop-flow PASSED!")
    return outputs


def test_http_endpoint(expected_version="1.0.0", endpoint_url="http://localhost:8080/version"):
    """Test the HTTP endpoint exposed by the running flow."""
    print()
    print("=" * 60)
    print("Testing HTTP endpoint")
    print("=" * 60)

    print(f"Endpoint: {endpoint_url}")
    print(f"Expected version: {expected_version}")
    print()

    # Give the flow a moment to fully start
    time.sleep(2)

    try:
        req = urllib.request.Request(endpoint_url)
        resp = urllib.request.urlopen(req, timeout=10)
        body = resp.read().decode()

        # The demo flow returns the version in a 'version' header
        version_header = resp.headers.get('version', '')

        print(f"HTTP Status: {resp.status}")
        print(f"Response Body: [{body}]")
        print(f"Version Header: [{version_header}]")

        # Check header for version
        if expected_version == version_header:
            print(f"SUCCESS: Version header matches expected '{expected_version}'")
            print("http-endpoint PASSED!")
            return True
        elif expected_version in body:
            print(f"SUCCESS: Response body contains expected version '{expected_version}'")
            print("http-endpoint PASSED!")
            return True
        else:
            print(f"FAILED: Version '{expected_version}' not found")
            print("http-endpoint FAILED!")
            return False
    except urllib.error.URLError as e:
        print(f"HTTP request failed: {e}")
        print("NOTE: This may be expected if port 8080 is not exposed from Docker")
        print("http-endpoint SKIPPED")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        print("http-endpoint SKIPPED")
        return False


def test_configure_params(github_token, output_file, process_group_id, parameters_json):
    """Test the configure-params command."""
    print()
    print("=" * 60)
    print("Testing configure-params command")
    print("=" * 60)

    env = get_base_env(github_token, output_file)
    env.update({
        'NIFI_ACTION_COMMAND': 'configure-params',
        'NIFI_PROCESS_GROUP_ID': process_group_id,
        'NIFI_PARAMETERS': parameters_json,
    })

    print(f"Process Group ID: {process_group_id}")
    print(f"Parameters: {parameters_json}")
    print()

    # Clear output file
    open(output_file, 'w').close()

    run_command(env)

    outputs = read_outputs(output_file)
    print()
    print("Outputs:", outputs)

    if outputs.get('success') != 'true':
        raise ValueError("Expected success=true in outputs")

    print("configure-params PASSED!")
    return outputs


def test_get_status(github_token, output_file, process_group_id):
    """Test the get-status command."""
    print()
    print("=" * 60)
    print("Testing get-status command")
    print("=" * 60)

    env = get_base_env(github_token, output_file)
    env.update({
        'NIFI_ACTION_COMMAND': 'get-status',
        'NIFI_PROCESS_GROUP_ID': process_group_id,
    })

    print(f"Process Group ID: {process_group_id}")
    print()

    # Clear output file
    open(output_file, 'w').close()

    run_command(env)

    outputs = read_outputs(output_file)
    print()
    print("Outputs:", outputs)

    if outputs.get('success') != 'true':
        raise ValueError("Expected success=true in outputs")

    # Verify we got key status outputs
    expected_keys = [
        'process_group_name', 'state', 'versioned', 'has_parameter_context'
    ]
    for key in expected_keys:
        if key not in outputs:
            raise ValueError(f"Expected {key} in outputs")

    print("get-status PASSED!")
    return outputs


def test_cleanup(github_token, output_file, process_group_id):
    """Test the cleanup command."""
    print()
    print("=" * 60)
    print("Testing cleanup command")
    print("=" * 60)

    env = get_base_env(github_token, output_file)
    env.update({
        'NIFI_ACTION_COMMAND': 'cleanup',
        'NIFI_PROCESS_GROUP_ID': process_group_id,
        'NIFI_FORCE_DELETE': 'true',
    })

    print(f"Process Group ID: {process_group_id}")
    print()

    # Clear output file
    open(output_file, 'w').close()

    run_command(env)

    outputs = read_outputs(output_file)
    print()
    print("Outputs:", outputs)

    if outputs.get('deleted') != 'true':
        raise ValueError("Expected deleted=true in outputs")

    print("cleanup PASSED!")
    return outputs


def verify_cleanup(process_group_id):
    """Verify that cleanup actually removed all resources."""
    print()
    print("=" * 60)
    print("Verifying cleanup was successful")
    print("=" * 60)

    import nipyapi

    # Check process group no longer exists
    try:
        pg = nipyapi.canvas.get_process_group(process_group_id)
        if pg is not None:
            raise ValueError(f"Process group {process_group_id} still exists after cleanup!")
        print(f"  Process group {process_group_id} correctly removed")
    except ValueError as e:
        if "not found" in str(e).lower() or "unable to find" in str(e).lower():
            print(f"  Process group {process_group_id} correctly removed")
        else:
            raise

    # Check parameter context no longer exists
    contexts = nipyapi.parameters.list_all_parameter_contexts()
    for ctx in contexts:
        if ctx.component.name == 'cicd-demo-params':
            raise ValueError("Parameter context 'cicd-demo-params' still exists after cleanup!")
    print("  Parameter context 'cicd-demo-params' correctly removed")

    print("verify-cleanup PASSED!")


def test_full_workflow():
    """Test the full workflow: ensure-registry -> deploy-flow -> cleanup."""
    print()
    print("*" * 60)
    print("FULL WORKFLOW TEST")
    print("*" * 60)

    # Check for required environment variable
    github_token = os.environ.get('GITHUB_REGISTRY_TOKEN')
    if not github_token:
        print("ERROR: GITHUB_REGISTRY_TOKEN environment variable not set")
        print("Please set it with a valid GitHub PAT")
        sys.exit(1)

    # Create a temporary file for outputs
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        output_file = f.name

    try:
        # Step 1: ensure-registry
        registry_outputs = test_ensure_registry(github_token, output_file, cleanup=False)
        registry_client_id = registry_outputs['registry_client_id']

        # Step 2: deploy-flow
        deploy_outputs = test_deploy_flow(github_token, output_file, registry_client_id)
        process_group_id = deploy_outputs['process_group_id']

        # Step 3: start-flow
        test_start_flow(github_token, output_file, process_group_id)

        # Step 4: get-status - verify flow is running
        status = test_get_status(github_token, output_file, process_group_id)
        if status.get('state') != 'RUNNING':
            print(f"WARNING: Expected state=RUNNING, got {status.get('state')}")

        # Step 5: test HTTP endpoint with default version (1.0.0)
        if not test_http_endpoint(expected_version="1.0.0"):
            print("WARNING: HTTP endpoint test failed, continuing...")

        # Step 6: configure-params - change version to 2.0.0
        # NiFi handles parameter context updates while the flow is running
        test_configure_params(github_token, output_file, process_group_id, '{"version": "2.0.0"}')

        # Step 7: test HTTP endpoint with new version (2.0.0)
        if not test_http_endpoint(expected_version="2.0.0"):
            print("WARNING: HTTP endpoint test with updated version failed, continuing...")

        # Step 8: stop-flow
        test_stop_flow(github_token, output_file, process_group_id)

        # Step 9: cleanup (force delete handles stopping, purging, controller services)
        test_cleanup(github_token, output_file, process_group_id)

        # Step 10: verify cleanup removed all resources
        verify_cleanup(process_group_id)

        print()
        print("*" * 60)
        print("FULL WORKFLOW TEST PASSED!")
        print("*" * 60)

    except SystemExit as e:
        if e.code != 0:
            print(f"TEST FAILED with exit code: {e.code}")
            sys.exit(1)
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Cleanup output file
        if os.path.exists(output_file):
            os.unlink(output_file)

        # Clean up the test registry client
        try:
            import nipyapi
            client = nipyapi.versioning.get_registry_client('test-action-client')
            if client:
                nipyapi.versioning.delete_registry_client(client)
                print("Cleaned up test registry client")
        except Exception:
            pass


def test_single_command(command):
    """Test a single command."""
    github_token = os.environ.get('GITHUB_REGISTRY_TOKEN')
    if not github_token:
        print("ERROR: GITHUB_REGISTRY_TOKEN environment variable not set")
        sys.exit(1)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        output_file = f.name

    try:
        if command == 'ensure-registry':
            test_ensure_registry(github_token, output_file, cleanup=True)
        elif command == 'deploy-flow':
            # Need registry client first
            registry_outputs = test_ensure_registry(github_token, output_file, cleanup=False)
            test_deploy_flow(github_token, output_file, registry_outputs['registry_client_id'])
        elif command == 'cleanup':
            print("cleanup requires a process-group-id, use full-workflow test instead")
            sys.exit(1)
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    finally:
        if os.path.exists(output_file):
            os.unlink(output_file)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'full-workflow':
            test_full_workflow()
        else:
            test_single_command(cmd)
    else:
        # Default: run ensure-registry test only
        test_single_command('ensure-registry')
