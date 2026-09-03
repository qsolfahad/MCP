import sys
from typing import Any
import httpx

from mcp.server import MCPServer

mcp = MCPServer("ServiceNow")

# ==============================
# ServiceNow configuration
# ==============================

SERVICENOW_URL = "https://nowlearning-nlinst04600309-17cpv-0001.lab.service-now.com"
SERVICENOW_USERNAME = "admin"
SERVICENOW_PASSWORD = "UpdatedInstance@123"

STATE_MAP = {
    "1": "New",
    "2": "In Progress",
    "3": "On Hold",
    "6": "Resolved",
    "7": "Closed",
    "8": "Canceled"
}

PRIORITY_MAP = {
    "1": "1 - Critical",
    "2": "2 - High",
    "3": "3 - Moderate",
    "4": "4 - Low",
    "5": "5 - Planning"
}


def _get_auth():
    return (SERVICENOW_USERNAME, SERVICENOW_PASSWORD)


def _get_headers():
    return {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }


def _format_val(val: Any) -> Any:
    if isinstance(val, dict):
        if "display_value" in val and val["display_value"]:
            return val["display_value"]
        if "value" in val:
            return val["value"]
    return val


async def _fetch_incident_record(client: httpx.AsyncClient, incident_identifier: str) -> tuple[dict[str, Any] | None, str | None]:
    """
    Look up an incident by number (e.g. INC0009009) or sys_id (32-character hex).
    Returns (record, error_message).
    """
    url = f"{SERVICENOW_URL}/api/now/table/incident"

    # Try searching by number first, or if 32 hex chars, by sys_id
    is_sys_id = len(incident_identifier) == 32 and all(c in "0123456789abcdefABCDEF" for c in incident_identifier)
    query = f"sys_id={incident_identifier}" if is_sys_id else f"number={incident_identifier}"

    params = {
        "sysparm_query": query,
        "sysparm_limit": "1"
    }

    response = await client.get(url, params=params, auth=_get_auth(), headers=_get_headers())

    if response.status_code != 200:
        return None, f"ServiceNow query error ({response.status_code}): {response.text}"

    data = response.json()
    records = data.get("result", [])

    if not records and not is_sys_id:
        # Fallback: check if identifier was a sys_id
        fallback_params = {"sysparm_query": f"sys_id={incident_identifier}", "sysparm_limit": "1"}
        fb_response = await client.get(url, params=fallback_params, auth=_get_auth(), headers=_get_headers())
        if fb_response.status_code == 200:
            records = fb_response.json().get("result", [])

    if not records:
        return None, f"Incident '{incident_identifier}' was not found."

    return records[0], None


# ==============================
# MCP Tools
# ==============================

@mcp.tool()
async def get_incident(
    incident_number: str,
    all_fields: bool = False,
    fields: str | None = None
) -> str:
    """
    Get a ServiceNow incident by incident number or sys_id.
    
    Args:
        incident_number: The incident number (e.g. 'INC0009009') or sys_id.
        all_fields: If True, returns all 80+ fields on the incident record.
        fields: Optional comma-separated list of specific field names to retrieve (e.g. 'short_description,state,priority,assigned_to').
    """
    async with httpx.AsyncClient() as client:
        incident, error = await _fetch_incident_record(client, incident_number)
        if error:
            return error

    if not incident:
        return f"Incident {incident_number} was not found."

    # If specific fields requested
    if fields:
        requested_keys = [f.strip() for f in fields.split(",") if f.strip()]
        lines = [f"Incident: {incident.get('number')} (sys_id: {incident.get('sys_id')})"]
        for key in requested_keys:
            val = _format_val(incident.get(key))
            lines.append(f"{key}: {val}")
        return "\n".join(lines)

    # If all fields requested
    if all_fields:
        lines = [
            f"=== Incident: {incident.get('number')} (All Fields) ===",
            f"sys_id: {incident.get('sys_id')}"
        ]
        for k in sorted(incident.keys()):
            val = incident.get(k)
            if val not in (None, "", {}):
                val_formatted = _format_val(val)
                lines.append(f"{k}: {val_formatted}")
        return "\n".join(lines)

    # Default formatted summary with key fields
    state_code = str(incident.get("state") or "")
    state_label = f"{state_code} ({STATE_MAP.get(state_code, 'Unknown')})" if state_code in STATE_MAP else state_code

    priority_code = str(incident.get("priority") or "")
    priority_label = PRIORITY_MAP.get(priority_code, priority_code)

    lines = [
        f"Incident: {incident.get('number')}",
        f"Sys ID: {incident.get('sys_id')}",
        f"Short Description: {incident.get('short_description')}",
        f"Description: {incident.get('description')}",
        f"State: {state_label}",
        f"Priority: {priority_label}",
        f"Urgency: {incident.get('urgency')}",
        f"Impact: {incident.get('impact')}",
        f"Category: {incident.get('category')}",
        f"Subcategory: {incident.get('subcategory')}",
        f"Caller: {_format_val(incident.get('caller_id'))}",
        f"Assigned To: {_format_val(incident.get('assigned_to'))}",
        f"Assignment Group: {_format_val(incident.get('assignment_group'))}",
        f"Contact Type: {incident.get('contact_type')}",
        f"Location: {_format_val(incident.get('location'))}",
        f"CMDB CI: {_format_val(incident.get('cmdb_ci'))}",
        f"Close Code: {incident.get('close_code')}",
        f"Close Notes: {incident.get('close_notes')}",
        f"Hold Reason: {incident.get('hold_reason')}",
        f"Updated On: {incident.get('sys_updated_on')} by {incident.get('sys_updated_by')}"
    ]
    # Filter out empty fields for cleaner presentation
    display_lines = [line for line in lines if not line.endswith(": ") and not line.endswith(": None")]
    return "\n".join(display_lines)


@mcp.tool()
async def update_incident(
    incident_number: str,
    short_description: str | None = None,
    description: str | None = None,
    state: str | None = None,
    priority: str | None = None,
    urgency: str | None = None,
    impact: str | None = None,
    category: str | None = None,
    subcategory: str | None = None,
    caller_id: str | None = None,
    assigned_to: str | None = None,
    assignment_group: str | None = None,
    comments: str | None = None,
    work_notes: str | None = None,
    close_code: str | None = None,
    close_notes: str | None = None,
    hold_reason: str | None = None,
    contact_type: str | None = None,
    location: str | None = None,
    cmdb_ci: str | None = None,
    field_name: str | None = None,
    field_value: Any | None = None,
    fields: dict[str, Any] | None = None
) -> str:
    """
    Update any and all fields of a ServiceNow incident.

    You can update fields using:
    1. Direct named parameters for standard fields (e.g. short_description, state, priority, comments, work_notes, etc.).
    2. A generic 'fields' dictionary for ANY field on the incident table:
       fields={"cmdb_ci": "...", "watch_list": "...", "any_custom_field": "..."}
    3. A single arbitrary field using 'field_name' and 'field_value'.

    Common field values:
      - state: '1' (New), '2' (In Progress), '3' (On Hold), '6' (Resolved), '7' (Closed), '8' (Canceled)
      - priority: '1' (Critical), '2' (High), '3' (Moderate), '4' (Low), '5' (Planning)
      - urgency: '1' (High), '2' (Medium), '3' (Low)
      - impact: '1' (High), '2' (Medium), '3' (Low)
      - comments: Customer-visible updates
      - work_notes: Internal engineer notes

    Args:
        incident_number: The incident number (e.g. 'INC0009009') or sys_id.
        short_description: Brief summary of the incident.
        description: Full detailed description of the incident.
        state: Incident state code ('1', '2', '3', '6', '7', '8').
        priority: Incident priority code ('1' to '5').
        urgency: Urgency rating ('1' to '3').
        impact: Impact rating ('1' to '3').
        category: Incident category (e.g. 'Network', 'Hardware', 'Software', 'Inquiry').
        subcategory: Incident subcategory.
        caller_id: Caller sys_id or user ID.
        assigned_to: Assigned engineer sys_id or user ID.
        assignment_group: Assigned group sys_id or group name.
        comments: Customer-facing additional comments.
        work_notes: Internal technical work notes.
        close_code: Resolution code (e.g. 'Solved (Permanently)').
        close_notes: Resolution summary notes.
        hold_reason: Reason for On Hold state.
        contact_type: Contact method (e.g. 'phone', 'email', 'self-service').
        location: Incident location name or sys_id.
        cmdb_ci: Configuration Item name or sys_id.
        field_name: Any arbitrary field name to update (used with field_value).
        field_value: Value for field_name.
        fields: A dictionary of any arbitrary fields and their values to update: {field_name: value}.
    """
    payload: dict[str, Any] = {}

    # 1. Add fields from the generic fields dictionary if provided
    if fields:
        payload.update(fields)

    # 2. Add single arbitrary field if provided
    if field_name is not None:
        payload[field_name] = field_value

    # 3. Add explicit named parameters if provided
    explicit_params = {
        "short_description": short_description,
        "description": description,
        "state": state,
        "priority": priority,
        "urgency": urgency,
        "impact": impact,
        "category": category,
        "subcategory": subcategory,
        "caller_id": caller_id,
        "assigned_to": assigned_to,
        "assignment_group": assignment_group,
        "comments": comments,
        "work_notes": work_notes,
        "close_code": close_code,
        "close_notes": close_notes,
        "hold_reason": hold_reason,
        "contact_type": contact_type,
        "location": location,
        "cmdb_ci": cmdb_ci,
    }

    for k, v in explicit_params.items():
        if v is not None:
            payload[k] = v

    if not payload:
        return (
            "No fields provided to update. Please specify at least one field to edit.\n"
            "You can use named arguments (e.g. short_description='...', state='2', priority='1') "
            "or the 'fields' dictionary (e.g. fields={'custom_field': 'value'})."
        )

    async with httpx.AsyncClient() as client:
        # First find the incident to get its sys_id
        incident, error = await _fetch_incident_record(client, incident_number)
        if error:
            return error
        if not incident:
            return f"Incident '{incident_number}' was not found."

        sys_id = incident["sys_id"]
        number = incident.get("number", incident_number)

        # PATCH update to ServiceNow Table API
        patch_url = f"{SERVICENOW_URL}/api/now/table/incident/{sys_id}"
        response = await client.patch(
            patch_url,
            json=payload,
            auth=_get_auth(),
            headers=_get_headers()
        )

        if response.status_code not in (200, 201):
            return f"ServiceNow update error ({response.status_code}):\n{response.text}"

        updated_data = response.json().get("result", {})

    # Build confirmation message showing what fields were updated
    lines = [
        f"Successfully updated incident {number} (sys_id: {sys_id}):",
        "",
        "Updated Fields:"
    ]
    for key, new_val in payload.items():
        serv_val = _format_val(updated_data.get(key))
        if not serv_val:
            serv_val = new_val
        lines.append(f"  - {key}: {serv_val}")

    lines.extend([
        "",
        "Current Summary:",
        f"  - Short Description: {updated_data.get('short_description')}",
        f"  - State: {updated_data.get('state')}",
        f"  - Priority: {updated_data.get('priority')}",
        f"  - Updated On: {updated_data.get('sys_updated_on')} by {updated_data.get('sys_updated_by')}"
    ])

    return "\n".join(lines)


@mcp.tool()
async def get_incident_fields() -> str:
    """
    List all available field names on the ServiceNow incident table that can be viewed or edited.
    """
    url = f"{SERVICENOW_URL}/api/now/table/incident"
    params = {"sysparm_limit": "1"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, auth=_get_auth(), headers=_get_headers())

    if response.status_code != 200:
        return f"ServiceNow error ({response.status_code}): {response.text}"

    data = response.json()
    records = data.get("result", [])
    if not records:
        return "No incident records found to inspect schema."

    sample = records[0]
    keys = sorted(sample.keys())
    lines = [
        f"ServiceNow Incident Table Fields ({len(keys)} total available):",
        "",
        "All of these fields can be viewed or updated using update_incident:"
    ]
    for k in keys:
        lines.append(f"  - {k}")

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        import asyncio
        inc = sys.argv[2] if len(sys.argv) > 2 else "INC0009009"
        print(f"Testing get_incident('{inc}')...\n")
        print(asyncio.run(get_incident(inc)))
    elif len(sys.argv) > 1 and sys.argv[1] == "--test-update":
        import asyncio
        inc = sys.argv[2] if len(sys.argv) > 2 else "INC0009009"
        field = sys.argv[3] if len(sys.argv) > 3 else "work_notes"
        val = sys.argv[4] if len(sys.argv) > 4 else "Testing update via MCP CLI"
        print(f"Testing update_incident('{inc}', {field}='{val}')...\n")
        print(asyncio.run(update_incident(inc, field_name=field, field_value=val)))
    elif len(sys.argv) > 1 and sys.argv[1] == "--test-fields":
        import asyncio
        print("Testing get_incident_fields()...\n")
        print(asyncio.run(get_incident_fields()))
    else:
        try:
            sys.stderr.write("ServiceNow MCP server is running on stdio (press Ctrl+C to stop)...\n")
            mcp.run()
        except KeyboardInterrupt:
            sys.stderr.write("\nServer stopped.\n")
            sys.exit(0)