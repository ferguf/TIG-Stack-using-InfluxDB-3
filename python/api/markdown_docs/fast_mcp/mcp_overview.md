# 🤖 FastMCP Integration: Network-as-Inventory Architectural Design

This document details the architectural pattern used to integrate the Model Context Protocol (MCP) server into the FastAPI-based Network-as-Inventory application. This design leverages the **FastMCP** library to create a robust, scalable, and natural language interface for network provisioning and management, maintaining a clean separation between REST API and AI tool interfaces.

---

## I. Overview of FastMCP Capabilities

The Model Context Protocol (MCP) defines a standard communication layer that allows AI agents (like Claude Code) to dynamically discover and securely call external functions, often referred to as "Tools." FastMCP is the official Python library that streamlines this process, translating standard, type-hinted Python functions into a formal, discoverable tool schema.

### Key Capabilities and Architectural Benefits:

| Capability | Description | Architectural Benefit |
| :--- | :--- | :--- |
| **Schema Generation** | Automatically converts Python function signatures and docstrings (with type hints) into the required MCP JSON Schema. | Eliminates manual OpenAPI/Schema maintenance for AI agents, guaranteeing consistency. |
| **Tool Execution** | Provides a secure HTTP-based wrapper (ASGI) that receives the agent's tool call requests and executes the corresponding Python function. | Decouples network provisioning logic from the web server, ensuring calls are validated before execution. |
| **Protocol Handling** | Manages all MCP communication, including discovery, streaming, and error handling, abstracting complex protocol details. | Simplifies development, allowing focus on core business logic rather than protocol compliance. |
| **FastAPI Integration** | Built specifically to be mounted as an ASGI application, enabling a single deployment to serve both traditional REST APIs and MCP Tools. | Unified deployment model (single Docker container) for both REST and Agent traffic. |

---

## II. The Core Orchestrator: `main.py`

The `main.py` file serves as the singular entry point and orchestrator for the application, initializing all services and binding the REST and MCP interfaces.

### 1. Initialization and Routing

* **Single FastAPI Instance:** The file strictly initializes one `FastAPI` instance, which acts as the core router for all traffic.
* **REST API Inclusion:** Standard REST API endpoints (e.g., `/customers`, `/devices`) are loaded via `app.include_router()`.

### 2. The Integrated Documentation Service

The `/md/{page_path:path}` route provides an integrated documentation service:

* **Path Parameter (`{page_path:path}`):** The use of the `:path` type annotation is crucial, allowing the parameter to consume multi-segment URLs (e.g., `/md/api_design/customer`), creating a navigable document hierarchy.
* **Dynamic Resolution:** The route first attempts to find an exact file match (`file_name.md`) and then checks for an `index.md` within the path, providing robust navigation similar to a static web server.

### 3. The MCP Integration Hook (The Mount Point)

The crucial architectural role of `main.py` is to mount the dedicated MCP server, achieving a clean separation of concerns:

```python
# main.py excerpt
from mcp_tools.mcp_ports import mcp_app # Import from dedicated directory
# ...
app.mount("/mcp", mcp_app) # Expose the MCP server at a single path