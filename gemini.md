This refined `gemini.md` integrates your specific directory structure, the **NDT** philosophy, and the **FastMCP** orchestration. It is designed to be the "source of truth" that prevents Gemini from hallucinating paths or breaking your architectural rules.

---

# 🌐 Project: NDT (Network Digital Twin)

## 🎯 Project Vision

NDT is a digital representation of the physical network. It synchronizes **Static Configuration (Postgres)** with **Real-time State (InfluxDB)** to provide a unified interface for automation and visualization.

## 🏗️ System Architecture

* **Backend (FastAPI):** The central nervous system.
* **Strict Rule:** No component (Streamlit or otherwise) connects to databases directly. All data must pass through the FastAPI layer.


* **Frontend (Streamlit):** 100% API consumer.
* **Visualization (Galileo):** A specialized module using **Plotly** for interactive topologies and telemetry heatmaps.
* **Data Persistence:**
* **PostgreSQL (SQLAlchemy 2.0):** Stores "Desired State" (Inventory, IPAM, Topology).
* **InfluxDB:** Stores "Actual State" (Interface counters, CPU/RAM, Latency).


* **Collection:** Telegraf via gNMI/SNMP.

---

## 📂 Directory Map & Context

### 🖥️ Backend (Python Root)

* `python/api/routers/`: FastAPI route definitions. Handles request validation (Pydantic) and calls backend scripts.
* `python/api/script/`: **The Engine Room.** Contains SQLAlchemy ORM models, Postgres queries, and InfluxDB logic.
* `python/mcp_fast/`: **The Bridge.** FastMCP server definitions that expose `api/script/` logic to the Gemini Agent.
* `python/galileo/`: Backend transformation logic for Plotly JSON structures.

### 🎨 Frontend (Streamlit Root)

* `/streamlit/pages/`: Multi-page UI logic (e.g., `Inventory.py`, `Telemetry.py`).
* `/streamlit/docs/`: Project documentation, business logic, and uploadable reference files.
* `/streamlit/src/utils/`: Shared utilities, primarily the **API Client wrapper**, **Forms** , **files handlers**.
* `/streamlit/src/galileo/`: Frontend Plotly implementation for maps and charts.
* `/streamlit/src/template/`: data for population table - likce devices.csv , *.PNG files .

---

## 📜 Development Standards

### 1. Database & ORM (SQLAlchemy 2.0)

* Models reside in `python/api/script/`.
* Use Declarative Mapping and `select()` statements (avoid legacy `.query`).
* Every table **must** have `created_at` and `updated_at` timestamps.
* Mandatory Foreign Keys for all network relationships (e.g., `interface.device_id`).

### 2. API Design & Logic

* **Error Handling:** Scripts in `api/script/` raise custom exceptions; Routers in `api/routers/` catch them to return `HTTPException`.
* **Validation:** Use the `ipaddress` module for all IPAM/CIDR validation.
* **Naming:** Use descriptive, action-oriented names (e.g., `sync_telemetry_to_twin()`).

### 3. FastMCP Integration

* Wrap existing functions from `python/api/script/`.
* Every tool **must** have a detailed docstring for the Agent to understand its purpose.


## 🤖 Agent Mode Guidelines

### Workflow Strategy

1. **Read Before Writing:** Always check `python/api/script/` before modifying backend logic.
2. **Tool-First Discovery:** If an MCP tool exists in `python/mcp_fast/` to perform a task, use it before suggesting new code.
3. **Path Awareness:** Maintain relative import integrity between `mcp_fast/` and `api/script/`.

### Specific Task Rules

* **Add Device:** Update SQLAlchemy model -> Create Pydantic schema -> Add FastAPI endpoint.
* **Topology View:** Ensure the `galileo` module output matches Plotly `go.Figure` requirements exactly.
* **UI Updates:** All data must be fetched via `streamlit/src/utils/api_client.py`.

