#!/usr/bin/env python
"""
NiFi Flow CI/CD Action - Main entry point

Routes commands to their respective handlers.
Uses nipyapi.profiles.switch('env') to configure the connection from environment variables.
"""

import sys

import nipyapi
from nipyapi import profiles
from nipyapi.utils import getenv

# Shared utilities
from utils import set_output

# Command handlers
from ensure_registry import run_ensure_registry
from deploy_flow import run_deploy_flow
from start_flow import run_start_flow
from stop_flow import run_stop_flow
from cleanup import run_cleanup
from configure_params import run_configure_params
from get_status import run_get_status
from change_version import run_change_version
from revert_flow import run_revert_flow


# Required inputs per command
COMMAND_REQUIREMENTS = {
    'ensure-registry': ['GH_REGISTRY_TOKEN'],
    'deploy-flow': ['NIFI_REGISTRY_CLIENT_ID', 'NIFI_BUCKET', 'NIFI_FLOW'],
    'start-flow': ['NIFI_PROCESS_GROUP_ID'],
    'stop-flow': ['NIFI_PROCESS_GROUP_ID'],
    'cleanup': ['NIFI_PROCESS_GROUP_ID'],
    'configure-params': ['NIFI_PROCESS_GROUP_ID', 'NIFI_PARAMETERS'],
    'get-status': ['NIFI_PROCESS_GROUP_ID'],
    'change-version': ['NIFI_PROCESS_GROUP_ID'],
    'revert-flow': ['NIFI_PROCESS_GROUP_ID'],
}

# Command handlers
COMMAND_HANDLERS = {
    'ensure-registry': run_ensure_registry,
    'deploy-flow': run_deploy_flow,
    'start-flow': run_start_flow,
    'stop-flow': run_stop_flow,
    'cleanup': run_cleanup,
    'configure-params': run_configure_params,
    'get-status': run_get_status,
    'change-version': run_change_version,
    'revert-flow': run_revert_flow,
}


def configure_nifi_connection():
    """
    Configure NiFi connection using nipyapi's 'env' profile.

    The 'env' profile uses pure environment variable configuration - no profiles
    file needed. All connection settings come from ENV_VAR_MAPPINGS in nipyapi.
    """
    nifi_url = getenv('NIFI_API_ENDPOINT')
    if not nifi_url:
        print("Error: nifi-api-endpoint is required")
        sys.exit(1)

    # Use nipyapi's 'env' profile - all config from environment variables
    # This handles SSL settings, authentication, and connection setup
    profiles.switch('env')

    print(f"Configured NiFi connection to: {nipyapi.config.nifi_config.host}")


def validate_command_inputs(command):
    """Validate that required inputs for the command are present."""
    required = COMMAND_REQUIREMENTS.get(command, [])
    missing = []
    for env_var in required:
        if not getenv(env_var):
            # Convert ENV_VAR to input-name for error message
            input_name = env_var.replace('_', '-').lower()
            missing.append(input_name)

    if missing:
        print(f"Error: Command '{command}' requires these inputs: {', '.join(missing)}")
        sys.exit(1)


def main():
    """Main entry point."""
    # Get command
    command = getenv('NIFI_ACTION_COMMAND')
    if not command:
        print("Error: 'command' input is required")
        sys.exit(1)

    print(f"Running command: {command}")

    # Validate command exists
    if command not in COMMAND_HANDLERS:
        available = ', '.join(COMMAND_HANDLERS.keys())
        print(f"Error: Unknown command '{command}'. Available: {available}")
        sys.exit(1)

    # Validate required inputs for this command
    validate_command_inputs(command)

    # Configure NiFi connection
    configure_nifi_connection()

    # Run the command handler
    try:
        handler = COMMAND_HANDLERS[command]
        handler(set_output)
        set_output('success', 'true')
    except Exception as e:
        print(f"Error executing command '{command}': {e}")
        set_output('success', 'false')
        sys.exit(1)


if __name__ == '__main__':
    main()
