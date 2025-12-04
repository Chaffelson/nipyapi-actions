#!/usr/bin/env python
"""
deploy-flow command handler

Deploys a flow from a Git-based registry to the NiFi canvas.
Uses nipyapi's built-in Git registry functions.
"""

import nipyapi
from nipyapi.utils import getenv

from utils import resolve_version_ref


def run_deploy_flow(set_output):
    """
    Deploy a flow from a Git-based registry to NiFi.

    Args:
        set_output: Function to set output values
    """
    # Get required inputs
    registry_client_id = getenv('NIFI_REGISTRY_CLIENT_ID')
    bucket = getenv('NIFI_BUCKET')
    flow = getenv('NIFI_FLOW')

    if not registry_client_id:
        raise ValueError("registry-client-id is required for deploy-flow command")
    if not bucket:
        raise ValueError("bucket is required for deploy-flow command")
    if not flow:
        raise ValueError("flow is required for deploy-flow command")

    # Optional inputs (convert empty strings to None for proper defaults)
    parent_id = getenv('NIFI_PARENT_PG_ID') or None
    branch = getenv('NIFI_FLOW_BRANCH') or None  # None = use registry client default
    version_input = getenv('NIFI_FLOW_VERSION') or None  # None = latest
    location_x = getenv('NIFI_LOCATION_X')
    location_y = getenv('NIFI_LOCATION_Y')

    # Resolve version ref (tag/branch/SHA) to commit SHA
    # This allows users to specify tags like "v1.0.0" instead of full SHAs
    version = resolve_version_ref(version_input)

    # Default to root process group if not specified
    if not parent_id:
        parent_id = nipyapi.canvas.get_root_pg_id()
        print(f"No parent specified, using root process group: {parent_id}")

    # Build location tuple
    location = None
    if location_x or location_y:
        x = int(location_x) if location_x else 0
        y = int(location_y) if location_y else 0
        location = (x, y)

    print(f"Deploying flow '{flow}' from bucket '{bucket}'")
    if branch:
        print(f"  Branch: {branch}")
    if version_input:
        if version != version_input:
            print(f"  Version: {version_input} (resolved to {version[:12]}...)")
        else:
            print(f"  Version: {version}")
    else:
        print("  Version: latest")

    # Deploy the flow using nipyapi's function
    process_group = nipyapi.versioning.deploy_git_registry_flow(
        registry_client_id=registry_client_id,
        bucket_id=bucket,
        flow_id=flow,
        parent_id=parent_id,
        location=location,
        version=version,
        branch=branch
    )

    # Get version info from the deployed PG
    version_info = process_group.component.version_control_information
    deployed_version = version_info.version if version_info else 'unknown'

    print(f"Flow deployed successfully!")
    print(f"  Process Group ID: {process_group.id}")
    print(f"  Process Group Name: {process_group.component.name}")
    print(f"  Deployed Version: {deployed_version}")

    # Set outputs
    set_output('process_group_id', process_group.id)
    set_output('process_group_name', process_group.component.name)
    set_output('deployed_version', deployed_version)
