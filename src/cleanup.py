#!/usr/bin/env python
"""
cleanup command handler

Stops and deletes a deployed process group from NiFi.
Uses nipyapi's canvas functions for process group management.
"""

import nipyapi
from nipyapi.utils import getenv, getenv_bool


def run_cleanup(set_output):
    """
    Stop and delete a process group, optionally including its parameter context.

    Args:
        set_output: Function to set output values
    """
    # Get required inputs
    process_group_id = getenv('NIFI_PROCESS_GROUP_ID')

    if not process_group_id:
        raise ValueError("process-group-id is required for cleanup command")

    # Optional inputs - defaults ensure proper cleanup for CI/CD
    force = getenv_bool('NIFI_FORCE_DELETE', default=True)
    delete_params = getenv_bool('NIFI_DELETE_PARAM_CONTEXT', default=True)

    print(f"Cleaning up process group: {process_group_id}")

    # Get the process group
    try:
        process_group = nipyapi.canvas.get_process_group(process_group_id, 'id')
    except nipyapi.nifi.rest.ApiException as e:
        if e.status == 404:
            print(f"Process group {process_group_id} not found - may already be deleted")
            set_output('deleted', 'false')
            set_output('message', 'Process group not found')
            return
        raise

    pg_name = process_group.component.name
    print(f"Found process group: {pg_name}")

    # Get parameter context reference before deleting PG
    param_ctx_id = None
    param_ctx_name = None
    if delete_params and process_group.component.parameter_context:
        param_ctx_id = process_group.component.parameter_context.id
        param_ctx_name = process_group.component.parameter_context.component.name
        print(f"Found parameter context: {param_ctx_name} (ID: {param_ctx_id})")

    # Stop the process group first
    print("Stopping process group...")
    nipyapi.canvas.schedule_process_group(process_group_id, scheduled=False)
    print("Process group stopped")

    # Delete the process group
    print("Deleting process group...")
    nipyapi.canvas.delete_process_group(process_group, force=force)
    print(f"Process group '{pg_name}' deleted successfully")

    # Delete the parameter context if requested and found
    if delete_params and param_ctx_id:
        try:
            print(f"Deleting parameter context: {param_ctx_name}...")
            ctx = nipyapi.parameters.get_parameter_context(param_ctx_id, identifier_type='id')
            nipyapi.parameters.delete_parameter_context(ctx)
            print(f"Parameter context '{param_ctx_name}' deleted successfully")
        except Exception as e:
            print(f"Warning: Could not delete parameter context: {e}")

    # Set outputs
    set_output('deleted', 'true')
    set_output('deleted_name', pg_name)
    set_output('message', f'Successfully deleted process group: {pg_name}')
