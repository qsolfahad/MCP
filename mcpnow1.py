import httpx

from mcp.server import MCPServer
 
mcp = MCPServer("ServiceNow")

# ==============================
# ServiceNow configuration
# ==============================

SERVICENOW_URL = "https://nowlearning-nlinst04600309-17cpv-0001.lab.service-now.com"
SERVICENOW_USERNAME = "admin"
SERVICENOW_PASSWORD = "UpdatedInstance@123"


# ==============================
# MCP Tool
# ==============================

@mcp.tool()
async def get_incident(incident_number: str) -> str:
    """
    Get a ServiceNow incident by incident number.
    Example: INC0009009
    """

    url = f"{SERVICENOW_URL}/api/now/table/incident"

    params = {
        "sysparm_query": f"number={incident_number}",
        "sysparm_limit": "1"
    }

    async with httpx.AsyncClient() as client:

        response = await client.get(
            url,
            params=params,
            auth=(
                SERVICENOW_USERNAME,
                SERVICENOW_PASSWORD
            ),
            headers={
                "Accept": "application/json"
            }
        )

    if response.status_code != 200:
        return f"ServiceNow error: {response.status_code}\n{response.text}"

    data = response.json()

    if not data.get("result"):
        return f"Incident {incident_number} was not found."

    incident = data["result"][0]

    return (
        f"Incident: {incident.get('number')}\n"
        f"Short Description: {incident.get('short_description')}\n"
        f"State: {incident.get('state')}\n"
        f"Priority: {incident.get('priority')}\n"
        f"Description: {incident.get('description')}"
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        import asyncio
        inc = sys.argv[2] if len(sys.argv) > 2 else "INC0009009"
        print(f"Testing get_incident('{inc}')...\n")
        print(asyncio.run(get_incident(inc)))
    else:
        try:
            sys.stderr.write("ServiceNow MCP server is running on stdio (press Ctrl+C to stop)...\n")
            mcp.run()
        except KeyboardInterrupt:
            sys.stderr.write("\nServer stopped.\n")
            sys.exit(0)