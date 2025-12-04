#!/usr/bin/env python
"""
change-version command handler

Changes the version of an already-deployed flow to a specified version.
Uses nipyapi's update_git_flow_ver function which handles Git-based registries.
"""

import nipyapi
from nipyapi.utils import getenv

from utils import resolve_version_ref


def run_change_version(set_output):
    """
    Change the version of a deployed flow.

    Args:
        set_output: Function to set output values

    Required environment variables:
        NIFI_PROCESS_GROUP_ID: The ID of the deployed process group

    Optional environment variables:
        NIFI_TARGET_VERSION: Version to change to (commit SHA or tag). If not
            specified, changes to the latest version.
        NIFI_FLOW_BRANCH: Branch to use (uses current branch if not specified)
    """
    # Get required inputs
    process_group_id = getenv('NIFI_PROCESS_GROUP_ID')

    if not process_group_id:
        raise ValueError("process-group-id is required for change-version command")

    # Optional inputs
    target_version_input = getenv('NIFI_TARGET_VERSION') or None
    branch = getenv('NIFI_FLOW_BRANCH') or None

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
            "version control. Cannot change version of an unversioned flow."
        )

    current_vci = version_info.version_control_information
    previous_version = current_vci.version

    print(f"Current version: {previous_version}")
    print(f"Current state: {current_vci.state}")

    # Resolve version ref if provided (tag/branch to SHA)
    target_version = None
    if target_version_input:
        target_version = resolve_version_ref(target_version_input)
        if target_version != target_version_input:
            print(f"Target version: {target_version_input} (resolved to {target_version[:12]}...)")
        else:
            print(f"Target version: {target_version}")
    else:
        print("Target version: latest")

    # Change the version
    print("Initiating version change...")
    result = nipyapi.versioning.update_git_flow_ver(
        process_group=process_group,
        target_version=target_version,
        branch=branch
    )

    # Get updated version info
    updated_pg = nipyapi.canvas.get_process_group(process_group_id, 'id')
    updated_vci = nipyapi.versioning.get_version_info(updated_pg)
    new_version = updated_vci.version_control_information.version
    new_state = updated_vci.version_control_information.state

    print(f"Version change completed!")
    print(f"  Previous version: {previous_version}")
    print(f"  New version: {new_version}")
    print(f"  New state: {new_state}")

    # Set outputs
    set_output('previous_version', previous_version)
    set_output('new_version', new_version)
    set_output('version_state', new_state)
