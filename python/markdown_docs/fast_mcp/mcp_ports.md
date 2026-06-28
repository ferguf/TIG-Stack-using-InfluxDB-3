
Here is the function definition from `mcp_tools/mcp_ports.py`:

```python
@mcp.tool
def provision_new_port(customer_id: str, device_name: str, port_speed_gbps: int) -> str:
    """
    Provisions a new physical or logical port on a specified network device...
    """
    logger.info(f"MCP Tool: Provisioning port for {customer_id}...")
    # Call your service layer here
    return f"Successfully queued port provisioning request for {customer_id} on {device_name}."


## 2. Markdown Tables

Tables are created using **pipes (`|`)** for columns and **hyphens (`-`)** for the header separator.

#### Standard Markdown for Tables

```markdown
Here is a comparison of the key elements in the MCP Tool Definition:

| Element | Role in MCP | AI Agent Interpretation |
| :--- | :--- | :--- |
| **`@mcp.tool` Decorator** | Registers the Python function as an available tool. | "I can call this function." |
| **Type Hinting** (`str`, `int`) | Defines the expected data types for the inputs. | "The `port_speed_gbps` must be a numerical integer." |
| **Docstring** (Summary) | Provides the high-level description of the tool's utility. | "I should use this tool when the user asks to provision a port." |



# MCP Tool Definition Breakdown

Here is a detailed breakdown of the `provision_new_port` tool, showing the role of each element:

| Element | Role in MCP | AI Agent Interpretation |
| :--- | :--- | :--- |
| **`@mcp.tool` Decorator** | Registers the Python function as an available tool. | "I can call this function." |
| **Type Hinting** (`str`, `int`) | Defines the expected data types for the inputs. | "The `port_speed_gbps` must be a numerical integer." |
| **Docstring** (Summary) | Provides the high-level description of the tool's utility. | "I should use this tool when the user asks to provision a port." |

## Code Implementation (`mcp_tools/mcp_ports.py`)

The logic is housed in a separate file to decouple the AI tool layer from the main API.

```python
@mcp.tool
def provision_new_port(customer_id: str, device_name: str, port_speed_gbps: int) -> str:
    """
    Provisions a new physical or logical port on a specified network device 
    and assigns it to a customer. Returns the fully qualified port ID or a status message.
    """
    logger.info(f"MCP Tool: Provisioning port for {customer_id} on {device_name}...")
    
    # --- PLACEHOLDER: REPLACE WITH REAL SERVICE CALL ---
    # Example: result = ports.service_layer.provision(customer_id, device_name, port_speed_gbps)
    # return result
    
    return f"Successfully queued port provisioning request for {customer_id} on {device_name}. (Placeholder)"