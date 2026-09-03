# ServiceNow MCP Server

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for integrating AI assistants (Claude, Cursor, etc.) with ServiceNow. Exposes tools to **get**, **update**, and **inspect** incident records directly from your AI chat.

---

## 🚀 Setup Guide (New Computer)

Follow these steps every time you set up on a new machine.

### Prerequisites

| Requirement | Notes |
|---|---|
| **Python 3.11+** | [Download](https://www.python.org/downloads/) — tick "Add to PATH" during install |
| **Git** | [Download](https://git-scm.com/downloads) |
| **Claude Desktop** (or another MCP host) | [Download](https://claude.ai/download) |

---

### Step 1 — Clone the repository

```bash
git clone https://github.com/qsolfahad/MCP.git servicenow-mcp
cd servicenow-mcp
```

---

### Step 2 — Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

| Platform | Command |
|---|---|
| **Windows (PowerShell)** | `.venv\Scripts\Activate.ps1` |
| **Windows (CMD)** | `.venv\Scripts\activate.bat` |
| **macOS / Linux** | `source .venv/bin/activate` |

---

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

---

### Step 4 — Configure your ServiceNow credentials

Open `mcpnow1.py` and update the three constants near the top of the file:

```python
SERVICENOW_URL      = "https://<your-instance>.service-now.com"
SERVICENOW_USERNAME = "admin"
SERVICENOW_PASSWORD = "your-password-here"
```

> **Tip:** Replace `<your-instance>` with your actual ServiceNow instance subdomain (e.g. `dev12345`).

---

### Step 5 — Test the server locally

Make sure the server can connect to ServiceNow before wiring it up to Claude.

```bash
# View an incident
python mcpnow1.py --test INC0009009

# Update a field on an incident
python mcpnow1.py --test-update INC0009009 work_notes "Testing from CLI"

# List all available incident fields
python mcpnow1.py --test-fields
```

A successful response prints the incident details. If you see an authentication error, re-check your credentials in Step 4.

---

### Step 6 — Register the MCP server in Claude Desktop

1. Open Claude Desktop.
2. Go to **Settings → Developer → Edit Config** (or open the config file directly).

   | Platform | Config file location |
   |---|---|
   | **Windows** | `%APPDATA%\Claude\claude_desktop_config.json` |
   | **macOS** | `~/Library/Application Support/Claude/claude_desktop_config.json` |

3. Add the following block inside `mcpServers`. Adjust the paths to match where you cloned the repo:

   **Windows example:**
   ```json
   {
     "mcpServers": {
       "servicenow": {
         "command": "C:\\servicenow-mcp\\.venv\\Scripts\\python.exe",
         "args": [
           "C:\\servicenow-mcp\\mcpnow1.py"
         ]
       }
     }
   }
   ```

   **macOS / Linux example:**
   ```json
   {
     "mcpServers": {
       "servicenow": {
         "command": "/path/to/servicenow-mcp/.venv/bin/python",
         "args": [
           "/path/to/servicenow-mcp/mcpnow1.py"
         ]
       }
     }
   }
   ```

4. **Save** the file, then **fully quit and restart** Claude Desktop.

5. You should see a 🔌 plug icon in the chat window confirming the MCP server is connected.

---

### Step 7 — Verify in Claude

Start a new Claude chat and try a prompt like:

> *"Get the details for incident INC0009009"*

Claude will call the `get_incident` tool automatically and show you the result.

---

## 🛠️ Tools Reference

### 1. `get_incident`
Retrieve incident details.

| Parameter | Type | Description |
|---|---|---|
| `incident_number` | string *(required)* | Incident number (e.g. `INC0009009`) or 32-char `sys_id` |
| `all_fields` | bool *(default: false)* | Return all 89+ fields on the record |
| `fields` | string *(optional)* | Comma-separated field names, e.g. `short_description,state,category` |

---

### 2. `update_incident`
Update any field on a ServiceNow incident.

| Parameter | Type | Description |
|---|---|---|
| `incident_number` | string *(required)* | Incident number or sys_id |
| `short_description` | string | Brief summary |
| `description` | string | Full description |
| `state` | string | `1` New · `2` In Progress · `3` On Hold · `6` Resolved · `7` Closed · `8` Canceled |
| `priority` | string | `1` Critical · `2` High · `3` Moderate · `4` Low · `5` Planning |
| `urgency` | string | `1` High · `2` Medium · `3` Low |
| `impact` | string | `1` High · `2` Medium · `3` Low |
| `category` | string | e.g. `inquiry`, `software`, `hardware`, `network` |
| `subcategory` | string | Subcategory |
| `caller_id` | string | Caller user ID or sys_id |
| `assigned_to` | string | Assignee user ID or sys_id |
| `assignment_group` | string | Group sys_id or name |
| `comments` | string | Customer-visible comments |
| `work_notes` | string | Internal technical notes |
| `close_code` | string | Resolution code |
| `close_notes` | string | Resolution notes |
| `hold_reason` | string | Hold reason code |
| `contact_type` | string | e.g. `phone`, `email`, `self-service` |
| `location` | string | Location name or sys_id |
| `cmdb_ci` | string | Configuration Item sys_id |
| `field_name` + `field_value` | string | Update any single arbitrary field |
| `fields` | dict | Update **any** fields at once: `{"u_custom_field": "value"}` |

---

### 3. `get_incident_fields`
Lists all 89+ field names available on the incident table — useful for knowing what you can query or update.

No parameters required.

---

## 💬 Example Prompts for Claude

```
Get incident INC0009009 and show me all fields.
Set the state of INC0009009 to In Progress and add a work note "Investigating now".
What fields are available on the incident table?
Update INC0009009: set priority to High, category to Software, and assigned_to to john.doe.
```

---

## 📁 Project Structure

```
servicenow-mcp/
├── mcpnow1.py          # MCP server + all tool definitions
├── requirements.txt    # Python dependencies
└── README.md           # This file
```
