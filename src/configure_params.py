#!/usr/bin/env python
"""
configure-params command handler

Sets parameter values on a parameter context associated with a process group.
"""

import json

import nipyapi
from nipyapi.utils import getenv


def run_configure_params(set_output):
    """
    Configure parameters on a process group's parameter context.

    Args:
        set_output: Function to set output values
    """
    process_group_id = getenv('NIFI_PROCESS_GROUP_ID')
    parameters_json = getenv('NIFI_PARAMETERS')

    if not process_group_id:
        raise ValueError("process-group-id is required for configure-params command")
    if not parameters_json:
        raise ValueError("parameters is required for configure-params command")

    # Parse the JSON parameters
    try:
        parameters = json.loads(parameters_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in parameters: {e}")

    if not isinstance(parameters, dict):
        raise ValueError("parameters must be a JSON object with key-value pairs")

    print(f"Configuring {len(parameters)} parameter(s) on process group: {process_group_id}")

    # Get the process group using helper function
    pg = nipyapi.canvas.get_process_group(process_group_id, identifier_type='id')
    if not pg:
        raise ValueError(f"Process group not found: {process_group_id}")

    print(f"Found process group: {pg.component.name}")

    # Check for parameter context reference
    if not pg.component.parameter_context:
        raise ValueError(
            f"Process group '{pg.component.name}' has no parameter context attached. "
            "Attach a parameter context to the process group before configuring parameters."
        )

    ctx_ref = pg.component.parameter_context
    print(f"Parameter context: {ctx_ref.component.name} (ID: {ctx_ref.id})")

    # Get the full parameter context
    ctx = nipyapi.parameters.get_parameter_context(ctx_ref.id, identifier_type='id')

    # Prepare all parameters as a batch
    prepared_params = []
    for param_name, param_value in parameters.items():
        param = nipyapi.parameters.prepare_parameter(
            name=param_name,
            value=str(param_value),
            sensitive=False
        )
        prepared_params.append(param)
        print(f"  Preparing {param_name} = {param_value}")

    # Apply all parameters in a single update call
    ctx.component.parameters = prepared_params
    nipyapi.parameters.update_parameter_context(ctx)

    updated_params = list(parameters.keys())
    print(f"Updated {len(updated_params)} parameter(s) successfully")

    # Set outputs
    set_output('parameters_updated', ','.join(updated_params))
    set_output('parameters_count', str(len(updated_params)))
    set_output('context_name', ctx_ref.component.name)
    set_output('success', 'true')
