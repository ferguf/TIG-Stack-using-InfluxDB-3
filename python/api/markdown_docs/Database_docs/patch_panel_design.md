
## 📄 `patch_panel_design.md`

# 🔗 Patch Panel and Connectivity Management System (PCMS) Design Specification

## 1. Introduction and Scope

This document defines the database schema for tracking all physical patch panels, their installation locations, and the individual connectivity status of every port. The design employs three decoupled tables to ensure normalized storage of facility location, panel properties, and service-specific port data.

## 2. Entity Specifications

### 2.1. `location` (Facility Master Data)

A centralized table to define physical locations, allowing multiple assets (e.g., racks, devices, panels) to share a standardized location identifier.

| Field Name | Data Type | Description | Constraints / Usage Notes |
| :--- | :--- | :--- | :--- |
| `location_id` | `UUID` | **Primary Key.** Unique ID for the facility location record. | PK, `gen_random_uuid()` |
| `location_name` | `VARCHAR(100)` | General site identification (e.g., 'DAL01', 'NYC05'). | |
| `floor` | `VARCHAR(50)` | Floor identifier (e.g., '1st Floor', 'Mezzanine'). | |
| `isle` | `VARCHAR(50)` | Aisle or Row. | |
| `rack` | `VARCHAR(50)` | Specific Rack ID (e.g., 'R12'). | |
| `coordinates` | `VARCHAR(100)` | Optional internal grid coordinates. | |

### 2.2. `patch_panel` (Panel Master Asset)

Defines the physical characteristics and placement of the patch panel itself.

| Field Name | Data Type | Description | Constraints / Usage Notes |
| :--- | :--- | :--- | :--- |
| **`panel_id`** | `UUID` | **Primary Key.** Unique identifier for the panel asset. | PK, `gen_random_uuid()` |
| `panel_name` | `VARCHAR(255)` | Unique identifier reflecting placement (e.g., `PP.DAL01.1st.A3.R12.1`). | **UNIQUE, NOT NULL** |
| `panel_type` | `VARCHAR(50)` | Physical media type (e.g., 'Fiber', 'Copper CAT6', 'MPO'). | |
| `location_id` | `UUID` | **Foreign Key** to the `location` table. | FK to `location(location_id)` |
| `model` | `VARCHAR(100)` | Manufacturer's model number. | |
| `vendor` | `VARCHAR(100)` | Manufacturer or supplier. | |
| `zone` | `VARCHAR(50)` | Logical or security zone classification. | |
| `port_count` | `INTEGER` | Total physical ports on the panel. | |
| `created_at` | `TIMESTAMPTZ` | Record insertion timestamp. | |
| `updated_at` | `TIMESTAMPTZ` | Record last modification timestamp. | |

### 2.3. `pp_port` (Port Connectivity and Service Data)

Defines each individual port on a panel and tracks its connectivity state and associated service revenue. This table is the core of the connection tracking system. 

| Field Name | Data Type | Description | Constraints / Usage Notes |
| :--- | :--- | :--- | :--- |
| **`pp_port_id`** | `UUID` | **Primary Key.** Unique ID for the specific port instance. | PK, `gen_random_uuid()` |
| `panel_id` | `UUID` | **Foreign Key** to the parent `patch_panel`. | FK, NOT NULL |
| `port_number` | `INTEGER` | The physical number/position on the panel. | Combined with `panel_id` for UNIQUE constraint. |
| `port_label` | `VARCHAR(50)` | Physical label (e.g., '1A', 'P2-4'). | |
| `media_type` | `VARCHAR(50)` | Physical media type of the port (e.g., 'SMF', 'CAT6'). | |
| `port_description` | `VARCHAR(255)` | Notes on intended use or configuration. | |
| **Connectivity Tracking** | | | |
| `port_in_link_id` | `UUID` | **Self-Referencing FK.** Points to the port ID connected to the 'input' side. | FK to `pp_port(pp_port_id)`. Tracks the connection. |
| `port_out_link_id` | `UUID` | **Self-Referencing FK.** Points to the port ID connected to the 'output' side. | FK to `pp_port(pp_port_id)`. Tracks the connection. |
| **Service and Revenue** | | | |
| `service_status` | `VARCHAR(50)` | Current operational status (e.g., 'Active', 'Available', 'Testing'). | |
| `activation_date` | `DATE` | Date the circuit/service became active. | |
| `loa_order_id` | `VARCHAR(100)` | Identifier for the service authorization (LOA). | |
| `loa_side` | `VARCHAR(50)` | Indicates the service side (e.g., 'Customer', 'Carrier'). | |
| `mrr` | `DECIMAL(10, 4)` | Monthly Recurring Revenue. | |
| `nrc` | `DECIMAL(10, 4)` | Non-Recurring Charge. | |

## 3. Relational Model and Connectivity

The system is built on two primary **One-to-Many** relationships and a critical **Self-Referencing** relationship:

1.  **Location to Panel (1:M):** A single `location` can house many `patch_panel` assets.
2.  **Panel to Port (1:M):** A single `patch_panel` asset contains many `pp_port` records.
3.  **Port to Port (Self-Referencing):** The `pp_port` table links ports to other ports via `port_in_link_id` and `port_out_link_id`. This allows the system to trace a physical patch cord or circuit path across the facility.

**Unique Constraint:** A composite unique key on (`panel_id`, `port_number`) ensures that no two ports on the same physical panel can share the same port number.

This design provides a high degree of fidelity for managing physical network connectivity and its associated financial data.