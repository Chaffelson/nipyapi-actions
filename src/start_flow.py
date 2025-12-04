#!/usr/bin/env python
"""
start-flow command handler

Starts a deployed process group in NiFi.
Enables controller services first, then starts processors.
"""

import nipyapi
from nipyapi.utils import getenv, getenv_bool


def run_start_flow(set_output):
    """
    Start a process group.

    Enables all controller services in the process group first,
    then starts all processors. This mirrors the typical NiFi UI workflow.

    Args:
        set_output: Function to set output values
    """
    # Get required inputs
    process_group_id = getenv('NIFI_PROCESS_GROUP_ID')

    if not process_group_id:
        raise ValueError("process-group-id is required for start-flow command")

    # Optional: skip enabling controllers (default True)
    enable_controllers = getenv_bool('NIFI_ENABLE_CONTROLLERS', default=True)

    print(f"Starting process group: {process_group_id}")

    # Get the process group to verify it exists and get its name
    try:
        process_group = nipyapi.canvas.get_process_group(process_group_id, 'id')
    except nipyapi.nifi.rest.ApiException as e:
        if e.status == 404:
            raise ValueError(f"Process group {process_group_id} not found") from e
        raise

    pg_name = process_group.component.name
    print(f"Found process group: {pg_name}")

    # Enable controller services first (required before starting processors)
    if enable_controllers:
        print("Enabling controller services...")
        nipyapi.canvas.schedule_all_controllers(process_group_id, scheduled=True)
        print("Controller services enabled")

    # Start the process group (processors)
    print("Starting processors...")
    result = nipyapi.canvas.schedule_process_group(process_group_id, scheduled=True)

    if result:
        print(f"Process group '{pg_name}' started successfully")
        set_output('started', 'true')
        set_output('process_group_name', pg_name)
        set_output('message', f'Successfully started process group: {pg_name}')
    else:
        print(f"Warning: Process group '{pg_name}' may not have fully started")
        print("Some components may be in invalid states")
        set_output('started', 'partial')
        set_output('process_group_name', pg_name)
        set_output('message', f'Process group started but some components may be invalid: {pg_name}')
