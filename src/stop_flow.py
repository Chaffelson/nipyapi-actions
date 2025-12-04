#!/usr/bin/env python
"""
stop-flow command handler

Stops a running process group in NiFi.
Stops processors first, then disables controller services.
"""

import nipyapi
from nipyapi.utils import getenv, getenv_bool


def run_stop_flow(set_output):
    """
    Stop a process group.

    Stops all processors first, then disables controller services.
    This mirrors the typical NiFi UI workflow (reverse of start).

    Args:
        set_output: Function to set output values
    """
    # Get required inputs
    process_group_id = getenv('NIFI_PROCESS_GROUP_ID')

    if not process_group_id:
        raise ValueError("process-group-id is required for stop-flow command")

    # Optional: skip disabling controllers (default True)
    disable_controllers = getenv_bool('NIFI_DISABLE_CONTROLLERS', default=True)

    print(f"Stopping process group: {process_group_id}")

    # Get the process group to verify it exists and get its name
    try:
        process_group = nipyapi.canvas.get_process_group(process_group_id, 'id')
    except nipyapi.nifi.rest.ApiException as e:
        if e.status == 404:
            raise ValueError(f"Process group {process_group_id} not found") from e
        raise

    pg_name = process_group.component.name
    print(f"Found process group: {pg_name}")

    # Stop processors first
    print("Stopping processors...")
    result = nipyapi.canvas.schedule_process_group(process_group_id, scheduled=False)

    # Disable controller services after processors stopped
    if disable_controllers:
        print("Disabling controller services...")
        nipyapi.canvas.schedule_all_controllers(process_group_id, scheduled=False)
        print("Controller services disabled")

    if result:
        print(f"Process group '{pg_name}' stopped successfully")
        set_output('stopped', 'true')
        set_output('process_group_name', pg_name)
        set_output('message', f'Successfully stopped process group: {pg_name}')
    else:
        print(f"Warning: Process group '{pg_name}' stop requested but threads may still be active")
        set_output('stopped', 'partial')
        set_output('process_group_name', pg_name)
        set_output('message', f'Stop requested but some threads may still be active: {pg_name}')
