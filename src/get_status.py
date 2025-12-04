"""Handler for the get-status command."""

import nipyapi
from nipyapi.utils import getenv


def run_get_status(set_output):
    """
    Get comprehensive status information for a process group.

    Returns structured information about the process group, its processors,
    controller services, version control state, and parameter context.


    Args:
        set_output: Function to set output values
    """
    pg_id = getenv('NIFI_PROCESS_GROUP_ID')

    if not pg_id:
        raise ValueError("process-group-id is required")

    print(f"Getting status for process group: {pg_id}")

    # Get process group entity with full status using existing helper
    pg = nipyapi.canvas.get_process_group_status(pg_id, detail="all")
    if not pg:
        raise ValueError(f"Process group not found: {pg_id}")

    pg_name = pg.component.name
    print(f"Found process group: {pg_name}")

    set_output('process_group_id', pg_id)
    set_output('process_group_name', pg_name)

    # Extract processor counts from the entity
    # These are available directly on ProcessGroupEntity
    running = str(pg.running_count or 0)
    stopped = str(pg.stopped_count or 0)
    invalid = str(pg.invalid_count or 0)
    disabled = str(pg.disabled_count or 0)

    # Determine state based on counts
    if pg.running_count and pg.running_count > 0:
        state = 'RUNNING'
    elif pg.stopped_count and pg.stopped_count > 0:
        state = 'STOPPED'
    else:
        state = 'EMPTY'

    total = str(sum([
        pg.running_count or 0,
        pg.stopped_count or 0,
        pg.invalid_count or 0,
        pg.disabled_count or 0
    ]))

    set_output('state', state)
    set_output('total_processors', total)
    set_output('running_processors', running)
    set_output('stopped_processors', stopped)
    set_output('invalid_processors', invalid)
    set_output('disabled_processors', disabled)

    print(f"  State: {state}")
    print(f"  Processors: {running} running, {stopped} stopped, "
          f"{invalid} invalid, {disabled} disabled")

    # Get queued flowfile info from status if available
    if pg.status and pg.status.aggregate_snapshot:
        agg = pg.status.aggregate_snapshot
        set_output('queued_flowfiles', str(agg.flow_files_queued or 0))
        set_output('queued_bytes', str(agg.bytes_queued or 0))

    # Get controller services status using existing helper
    controllers = nipyapi.canvas.list_all_controllers(pg_id, descendants=True)
    if controllers:
        enabled = sum(1 for c in controllers if c.component.state == 'ENABLED')
        disabled_ctrl = sum(1 for c in controllers if c.component.state == 'DISABLED')
        enabling = sum(1 for c in controllers if c.component.state == 'ENABLING')
        disabling = sum(1 for c in controllers if c.component.state == 'DISABLING')

        set_output('total_controllers', str(len(controllers)))
        set_output('enabled_controllers', str(enabled))
        set_output('disabled_controllers', str(disabled_ctrl))
        set_output('enabling_controllers', str(enabling))
        set_output('disabling_controllers', str(disabling))

        print(f"  Controllers: {enabled} enabled, {disabled_ctrl} disabled")
    else:
        set_output('total_controllers', '0')
        set_output('enabled_controllers', '0')
        set_output('disabled_controllers', '0')
        print("  Controllers: none")

    # Get version control information from component
    vci = pg.component.version_control_information
    if vci:
        set_output('versioned', 'true')
        set_output('version_id', vci.version or '')
        set_output('flow_id', vci.flow_id or '')
        set_output('flow_name', vci.flow_name or '')
        set_output('bucket_id', vci.bucket_id or '')
        set_output('bucket_name', vci.bucket_name or '')
        set_output('registry_id', vci.registry_id or '')
        set_output('registry_name', vci.registry_name or '')
        set_output('version_state', vci.state or '')
        modified = str(vci.state not in ['UP_TO_DATE', 'SYNC_FAILURE']).lower()
        set_output('modified', modified)

        print(f"  Version: {vci.version} ({vci.state})")
        print(f"  Flow: {vci.flow_name} in {vci.bucket_name}")
    else:
        set_output('versioned', 'false')
        set_output('modified', 'false')
        print("  Version control: not versioned")

    # Get parameter context information from component
    pc_ref = pg.component.parameter_context
    if pc_ref and pc_ref.id:
        set_output('has_parameter_context', 'true')
        set_output('parameter_context_id', pc_ref.id)
        pc_name = pc_ref.component.name if pc_ref.component else ''
        set_output('parameter_context_name', pc_name)

        # Get parameter count using existing helper
        try:
            pc = nipyapi.parameters.get_parameter_context(pc_ref.id)
            param_count = len(pc.component.parameters) if pc.component.parameters else 0
            set_output('parameter_count', str(param_count))
            print(f"  Parameter context: {pc_name} ({param_count} parameters)")
        except Exception:
            set_output('parameter_count', '0')
            print(f"  Parameter context: {pc_name}")
    else:
        set_output('has_parameter_context', 'false')
        set_output('parameter_count', '0')
        print("  Parameter context: none")

    print()
    print("Status retrieved successfully")
