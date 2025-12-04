#!/usr/bin/env python
"""
revert-flow command handler

Reverts uncommitted local changes to a deployed flow, restoring it to the
last committed version in the registry.
Uses nipyapi's revert_flow_ver function with wait=True for synchronous operation.
"""

import nipyapi
from nipyapi.utils import getenv


def run_revert_flow(set_output):
    """
    Revert uncommitted changes to a deployed flow.

    This command reverts any local modifications to a process group, restoring
    it to match the version currently tracked in the registry. This is useful
    when you want to discard local changes without changing to a different version.

    Args:
        set_output: Function to set output values

    Required environment variables:
        NIFI_PROCESS_GROUP_ID: The ID of the deployed process group
    """
    # Get required inputs
    process_group_id = getenv('NIFI_PROCESS_GROUP_ID')

    if not process_group_id:
        raise ValueError("process-group-id is required for revert-flow command")

    # Get the process group
    print(f"Getting process group: {process_group_id}")
    process_group = nipyapi.canvas.get_process_group(process_group_id, 'id')

    if not process_group:
        raise ValueError(f"Process group not found: {process_group_id}")

    # Get current version info
    version_info = nipyapi.versioning.get_version_info(process_group)
    if not version_info or not version_info.version_control_information:
        raise ValueError(
            f"Process group '{process_group.component.name}' is not under "
            "version control. Cannot revert an unversioned flow."
        )

    current_vci = version_info.version_control_information
    current_version = current_vci.version
    current_state = current_vci.state

    print(f"Current version: {current_version}")
    print(f"Current state: {current_state}")

    # Check if revert is needed
    if current_state == 'UP_TO_DATE':
        print("Flow is already up to date with registry. No changes to revert.")
        set_output('reverted', 'false')
        set_output('version', current_version)
        set_output('state', current_state)
        return

    if current_state != 'LOCALLY_MODIFIED':
        print(f"Warning: Flow state is '{current_state}', not 'LOCALLY_MODIFIED'.")
        print("Proceeding with revert anyway...")

    # Revert the flow (wait=True ensures we wait for completion)
    print("Reverting local changes...")
    result = nipyapi.versioning.revert_flow_ver(process_group, wait=True)

    # Get final state
    final_state = result.version_control_information.state
    final_version = result.version_control_information.version

    print(f"Revert completed!")
    print(f"  Version: {final_version}")
    print(f"  State: {final_state}")

    # Set outputs
    set_output('reverted', 'true')
    set_output('version', final_version)
    set_output('state', final_state)
