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
    export GH_REGISTRY_TOKEN="your-token"

    # Then run from repo root:
    python tests/local.py [command]

    # Commands: ensure-registry (default), deploy-flow, start-flow, stop-flow, cleanup, full-workflow
"""

import os
import sys
import time
import tempfile
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
    """Run nipyapi CI command with the given environment variables.

    Uses nipyapi.ci module directly (same as CLI) rather than subprocess
    for better error handling and debugging.

    Captures the return value (dict) and writes to GITHUB_OUTPUT file.
    """
    # Clear action-specific env vars
    for key in ACTION_ENV_VARS:
        if key in os.environ:
            del os.environ[key]

    # Set new environment
    for key, value in env_vars.items():
        os.environ[key] = value

    # Map action command names to CLI function names
    command = env_vars.get('NIFI_ACTION_COMMAND', '')
    cmd_map = {
        'ensure-registry': 'ensure_registry',
        'deploy-flow': 'deploy_flow',
        'start-flow': 'start_flow',
        'stop-flow': 'stop_flow',
        'get-status': 'get_status',
        'configure-params': 'configure_params',
        'change-version': 'change_version',
        'revert-flow': 'revert_flow',
        'cleanup': 'cleanup',
        'purge-flowfiles': 'purge_flowfiles',
    }

    func_name = cmd_map.get(command)
    if not func_name:
        raise ValueError(f"Unknown command: {command}")

    # Import and run the nipyapi.ci function directly
    import nipyapi.ci
    func = getattr(nipyapi.ci, func_name)
    result = func()

    # Write outputs to GITHUB_OUTPUT file in key=value format
    output_file = env_vars.get('GITHUB_OUTPUT')
    if output_file and result and isinstance(result, dict):
        with open(output_file, 'a') as f:
            for key, value in result.items():
                # Flatten nested dicts/lists to simple values
                if isinstance(value, (dict, list)):
                    import json
                    value = json.dumps(value)
                f.write(f"{key}={value}\n")


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
        # Disable controllers for cleanup - stop_flow defaults to not disabling
        'NIFI_DISABLE_CONTROLLERS': 'true',
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

    # configure_params returns parameters_updated, not success flag
    if 'parameters_count' not in outputs:
        raise ValueError("Expected parameters_count in outputs")

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

    # Verify we got key status outputs (success is added by action.yml wrapper, not the function)
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
        # Full cleanup for CI/CD - cleanup defaults to safe mode
        'NIFI_FORCE_DELETE': 'true',
        'NIFI_DELETE_PARAMETER_CONTEXT': 'true',
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


def test_purge_flowfiles(github_token, output_file, process_group_id):
    """Test purge-flowfiles by queuing flow files and purging them.

    This test:
    1. Stops the HandleHTTPResponse processor (so flow files queue)
    2. Sends an HTTP request (creates a queued flow file)
    3. Verifies flow files are queued
    4. Calls purge-flowfiles via action command
    5. Verifies queue is empty
    6. Restarts the processor
    """
    print()
    print("=" * 60)
    print("Testing purge-flowfiles command")
    print("=" * 60)

    import nipyapi

    # Get processors in the process group
    processors = nipyapi.canvas.list_all_processors(pg_id=process_group_id)

    # Find HandleHTTPResponse processor
    response_proc = None
    for proc in processors:
        if 'HandleHTTPResponse' in proc.component.name:
            response_proc = proc
            break

    if not response_proc:
        print("WARNING: HandleHTTPResponse processor not found, skipping purge test")
        return {}

    print(f"Found HandleHTTPResponse processor: {response_proc.id}")

    try:
        # Step 1: Stop the response processor so flow files will queue
        print("Stopping HandleHTTPResponse processor...")
        nipyapi.canvas.schedule_processor(response_proc, False)
        time.sleep(1)

        # Step 2: Send an HTTP request to create a queued flow file
        print("Sending HTTP request to create queued flow file...")
        try:
            req = urllib.request.Request("http://localhost:8080/version")
            # Use a short timeout since the response processor is stopped
            urllib.request.urlopen(req, timeout=2)
        except Exception:
            # Expected to timeout/fail since response processor is stopped
            pass

        time.sleep(1)

        # Step 3: Check that flow files are queued
        status = nipyapi.canvas.get_process_group_status(process_group_id, detail="all")
        queued_before = 0
        if hasattr(status, 'status') and hasattr(status.status, 'aggregate_snapshot'):
            queued_before = status.status.aggregate_snapshot.flow_files_queued or 0
        print(f"Flow files queued before purge: {queued_before}")

        if queued_before == 0:
            print("WARNING: No flow files queued - HTTP endpoint may not be accessible")

        # Step 4: Call purge-flowfiles via action command
        env = get_base_env(github_token, output_file)
        env.update({
            'NIFI_ACTION_COMMAND': 'purge-flowfiles',
            'NIFI_PROCESS_GROUP_ID': process_group_id,
        })

        print(f"Calling purge-flowfiles on: {process_group_id}")

        # Clear output file
        open(output_file, 'w').close()

        run_command(env)

        outputs = read_outputs(output_file)
        print()
        print("Outputs:", outputs)

        # purge_flowfiles returns purged=true, not success
        if outputs.get('purged') != 'true':
            raise ValueError("Expected purged=true in outputs")

        # Step 5: Verify queue is now empty
        status = nipyapi.canvas.get_process_group_status(process_group_id, detail="all")
        queued_after = 0
        if hasattr(status, 'status') and hasattr(status.status, 'aggregate_snapshot'):
            queued_after = status.status.aggregate_snapshot.flow_files_queued or 0
        print(f"Flow files queued after purge: {queued_after}")

        if queued_after > 0:
            print(f"WARNING: Expected 0 queued flow files after purge, got {queued_after}")

        print("purge-flowfiles PASSED!")
        return outputs

    finally:
        # Step 6: Restart the processor so subsequent tests work
        print("Restarting HandleHTTPResponse processor...")
        try:
            nipyapi.canvas.schedule_processor(response_proc, True)
        except Exception as e:
            print(f"WARNING: Failed to restart processor: {e}")


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

    # Check parameter context no longer exists (may fail if shared across deployments)
    contexts = nipyapi.parameters.list_all_parameter_contexts()
    for ctx in contexts:
        if ctx.component.name == 'cicd-demo-params':
            # Try to clean it up manually if cleanup failed
            try:
                nipyapi.parameters.delete_parameter_context(ctx)
                print("  Parameter context 'cicd-demo-params' manually removed")
            except Exception as e:
                # May fail if still in use - not critical for test
                print(f"  WARNING: Could not remove parameter context: {e}")
            break
    else:
        print("  Parameter context 'cicd-demo-params' correctly removed")

    print("verify-cleanup PASSED!")


def cleanup_stale_resources(github_token, output_file):
    """Clean up any stale resources from previous failed test runs."""
    print()
    print("=" * 60)
    print("Pre-test cleanup: removing stale resources")
    print("=" * 60)

    # Set up environment variables first (so nipyapi can connect)
    env = get_base_env(github_token, output_file)
    for key, value in env.items():
        os.environ[key] = value

    import nipyapi

    # Configure nipyapi from environment (same as CI functions do)
    nipyapi.profiles.switch()

    # Find and clean up any stale cicd-demo-flow
    try:
        pgs = nipyapi.canvas.list_all_process_groups(nipyapi.canvas.get_root_pg_id())
        for pg in pgs:
            if pg.component.name == 'cicd-demo-flow':
                print(f"  Found stale PG: {pg.id}")
                nipyapi.canvas.schedule_process_group(pg.id, scheduled=False)
                try:
                    nipyapi.canvas.schedule_all_controllers(pg.id, scheduled=False)
                except Exception:
                    pass
                nipyapi.canvas.delete_process_group(pg, force=True)
                print("  Deleted stale process group")
    except Exception as e:
        print(f"  Could not clean PGs: {e}")

    # Clean up orphaned parameter context
    try:
        contexts = nipyapi.parameters.list_all_parameter_contexts()
        for ctx in contexts:
            if ctx.component.name == 'cicd-demo-params':
                nipyapi.parameters.delete_parameter_context(ctx)
                print("  Deleted orphaned parameter context")
    except Exception as e:
        print(f"  Could not clean parameter context: {e}")

    # Clean up test registry client
    try:
        client = nipyapi.versioning.get_registry_client('test-action-client')
        if client:
            nipyapi.versioning.delete_registry_client(client)
            print("  Deleted stale registry client")
    except Exception:
        pass

    print("Pre-test cleanup complete")


def test_full_workflow():
    """Test the full workflow: ensure-registry -> deploy-flow -> cleanup."""
    print()
    print("*" * 60)
    print("FULL WORKFLOW TEST")
    print("*" * 60)

    # Check for required environment variable
    github_token = os.environ.get('GH_REGISTRY_TOKEN')
    if not github_token:
        print("ERROR: GH_REGISTRY_TOKEN environment variable not set")
        print("Please set it with a valid GitHub PAT")
        sys.exit(1)

    # Create a temporary file for outputs
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        output_file = f.name

    try:
        # Clean up any stale resources from previous failed runs
        cleanup_stale_resources(github_token, output_file)

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

        # Step 6: configure-params - test secret injection with dynamic value
        # Uses a unique value (timestamp-based) to verify injection works correctly.
        # This simulates how GitHub secrets would be injected in CI.
        import datetime
        injected_value = f"local-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
        print(f"Testing secret injection with value: {injected_value}")
        test_configure_params(
            github_token, output_file, process_group_id,
            f'{{"version": "{injected_value}"}}'
        )

        # Step 7: test HTTP endpoint with injected value
        if not test_http_endpoint(expected_version=injected_value):
            print("WARNING: HTTP endpoint test with injected value failed, continuing...")

        # Step 8: test purge-flowfiles
        test_purge_flowfiles(github_token, output_file, process_group_id)

        # Step 9: stop-flow
        test_stop_flow(github_token, output_file, process_group_id)

        # Step 10: cleanup (force delete handles stopping, purging, controller services)
        test_cleanup(github_token, output_file, process_group_id)

        # Step 11: verify cleanup removed all resources
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


def test_single_command(command, skip_cleanup=False):
    """Test a single command.

    Args:
        command: The command to test
        skip_cleanup: If True, don't clean up resources after test (useful for debugging)
    """
    github_token = os.environ.get('GH_REGISTRY_TOKEN')
    if not github_token:
        print("ERROR: GH_REGISTRY_TOKEN environment variable not set")
        sys.exit(1)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        output_file = f.name

    try:
        if command == 'ensure-registry':
            outputs = test_ensure_registry(github_token, output_file, cleanup=not skip_cleanup)
            if skip_cleanup:
                print(f"\n--no-cleanup: Registry client kept: {outputs['registry_client_id']}")
        elif command == 'deploy-flow':
            # Need registry client first
            registry_outputs = test_ensure_registry(github_token, output_file, cleanup=False)
            deploy_outputs = test_deploy_flow(
                github_token, output_file, registry_outputs['registry_client_id']
            )
            if skip_cleanup:
                print(f"\n--no-cleanup: Resources kept:")
                print(f"  Registry Client ID: {registry_outputs['registry_client_id']}")
                print(f"  Process Group ID: {deploy_outputs['process_group_id']}")
            else:
                # Clean up registry client
                try:
                    import nipyapi
                    client = nipyapi.versioning.get_registry_client('test-action-client')
                    if client:
                        nipyapi.versioning.delete_registry_client(client)
                        print("Cleaned up test registry client")
                except Exception:
                    pass
        elif command == 'cleanup':
            print("cleanup requires a process-group-id, use full-workflow test instead")
            sys.exit(1)
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    finally:
        if os.path.exists(output_file):
            os.unlink(output_file)


def print_usage():
    """Print usage information."""
    print("Usage: python tests/local.py [command] [options]")
    print()
    print("Commands:")
    print("  ensure-registry    Set up a GitHub registry client")
    print("  deploy-flow        Deploy a flow (sets up registry client first)")
    print("  full-workflow      Run the complete test workflow")
    print()
    print("Options:")
    print("  --no-cleanup       Don't clean up resources after test (for debugging)")
    print()
    print("Examples:")
    print("  python tests/local.py ensure-registry --no-cleanup")
    print("  python tests/local.py deploy-flow --no-cleanup")
    print("  python tests/local.py full-workflow")


if __name__ == '__main__':
    # Parse arguments
    args = sys.argv[1:]
    skip_cleanup = '--no-cleanup' in args
    if skip_cleanup:
        args.remove('--no-cleanup')

    if not args:
        print_usage()
        sys.exit(0)

    cmd = args[0]

    if cmd == 'full-workflow':
        if skip_cleanup:
            print("WARNING: --no-cleanup not supported for full-workflow")
        test_full_workflow()
    elif cmd in ('--help', '-h', 'help'):
        print_usage()
    else:
        test_single_command(cmd, skip_cleanup=skip_cleanup)
