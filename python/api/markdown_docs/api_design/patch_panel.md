This is a comprehensive set of tables designed to capture all necessary information for a patch panel port used in a cross-connect (LOA/LFA) in a data center or colo environment.

The documentation is split into three tables for clarity: **Local Panel ID**, **Remote Endpoint ID**, and **Service/Order Details**.

---

## 1. 🏢 Local Patch Panel & Port (Your Side)

This table focuses on the exact physical location and port number within your managed space. This data often represents the **LFA** (Local Facility Assignment) provided to the third party.

| Attribute | Field Type | Example Data | Notes |
| :--- | :--- | :--- | :--- |
| **Data Center / Colo** | Text (Dropdown) | DCX-ASHBURN-01 | Facility name/code for multi-site management. |
| **Rack ID** | Text | **RACK-A05** | The specific cabinet your equipment is in. |
| **Patch Panel ID** | Text (Asset Tag) | **PP-FIBER-01A** | Unique ID for the panel in the rack (e.g., RU 40). |
| **Local Port** | Number/Text | **03** | The exact port number on your panel (e.g., 1, 2, 3, 4...). **CRITICAL.** |
| **Media Type** | Dropdown | SMF LC/PC | Single Mode Fiber (SMF), Multi-Mode Fiber (MMF), or Copper (CAT6). |
| **Connector Type** | Dropdown | LC/PC (Blue) | Connector face (e.g., LC, SC, MTP, RJ45) and polish (PC, UPC, APC). |
| **Connected Device** | Text | Router-A05-E01 | The device port connected to the *rear* of this patch panel port. |

---

## 2. 🤝 Remote Endpoint & Third-Party Details

This table captures the information about the other side of the cross-connect, as requested in the LOA or CFA document.

| Attribute | Field Type | Example Data | **User Request Match** |
| :--- | :--- | :--- | :--- |
| **3rd Party Name** | Text (Dropdown) | **Network Provider Z** | **3rd party name** |
| **3rd Party ID** | Text | **CIRCUIT-NPZ-7890** | **ID** (Their Circuit/Customer ID) |
| **Remote Panel (Text)** | Text (Detailed) | **MMR-A, Rack 1-12, Panel 4, Ports 1-2** | **remote panel (text)** (Exact description from the LOA/CFA) |
| **Remote Port** | Text/Number | **1** | The specific port number used on their panel. |
| **Remote Location Type**| Dropdown | Meet-Me-Room (MMR) | E.g., MMR, Telco Cage, Other Customer Cage. |
| **LOA / CFA #** | Text | **LOA-456789** | The official document reference number. |

---

## 3. 📝 Service and Status Tracking

This table provides operational context and documentation links.

| Attribute | Field Type | Example Data | Notes |
| :--- | :--- | :--- | :--- |
| **Internal Circuit ID** | Text | **CC-FIBER-2025001** | Your internal, unique tracking ID for the connection. |
| **Service Description** | Text | AWS Direct Connect 10G | A brief description of the service using this port. |
| **Status** | Dropdown | **Active** | Active, Testing, Scheduled Disconnect, Disconnected. |
| **Activation Date** | Date | 2025-11-15 | The date the circuit was physically completed. |
| **Documentation Link** | URL | https://sharepoint/docs/LOA-456789.pdf | Link to the stored LOA/LFA document. |
| **Bandwidth (Rate)** | Text/Number | 10 Gbps | The speed of the service this port supports. |

***

### Combined Documentation Example

A practical view of how this would look in a DCIM or spreadsheet tool:

| Internal ID | Local Rack | Local Panel | Local Port | 3rd Party Name | 3rd Party ID | Remote Panel (Text) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CC-FIBER-2025001** | RACK-A05 | PP-FIBER-01A | **03** | Network Provider Z | CIRCUIT-NPZ-7890 | **MMR-A, Rack 1-12, Panel 4, Ports 1-2** | Active |
| **CC-COPPER-2025002** | RACK-B12 | PP-COPPER-02 | **14** | ISP - Regional | CUST-ID-3349 | **TELCO-ROOM, RACK D02, Cross-Connect Panel, Port J4** | Testing |

This combined view offers the quickest way to see the **A-side (Local)** and the **Z-side (Remote)** connection points that the field technicians need.


I will document the design for the `panel_port` table using the **Conditional Foreign Key (Polymorphic Association)** pattern, as discussed, which allows a port to connect to either a specific device port (`ports` table) or a cross-connect circuit (`cross_connect` table).

## 🗄️ `panel_port` Table Design Specification

This document defines the schema for the `panel_port` table, which tracks every individual port on a patch panel device and its current connection status.

---

### Table Definition: `panel_port`

| Column | Type | Nullable | Default Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| **`panel_port_id`** | `UUID` | `NOT NULL` | `gen_random_uuid()` | **Primary Key.** The unique identifier for this port. |
| **`panel_id`** | `UUID` | `NOT NULL` | | **Foreign Key** to the `devices` table (specifically, the device acting as the patch panel). |
| **`port_number`** | `INT` | `NOT NULL` | | The sequential physical number (e.g., 1, 2, 3...) of the port on the panel. |
| **`media_type`** | `VARCHAR(20)` | `NOT NULL` | | The type of physical media (e.g., `'Copper'`, `'Fiber'`, `'Coax'`). |
| `connector_id` | `UUID` | `NULL` | | **Foreign Key** to a `connector_types` table (if present) for standardized connector information (e.g., SC, LC, RJ45). |
| `connector_identifier`| `VARCHAR(50)` | `NULL` | | A textual identifier for the physical connector type. |
| `is_local_port` | `BOOLEAN` | `NULL` | `FALSE` | Flag indicating if this is an internal-use port (e.g., connecting two local racks). |
| `third_party_name` | `VARCHAR(255)` | `NULL` | | If connected to a third-party, their name/identifier. |
| `third_party_remote_panel_text`| `VARCHAR(255)`| `NULL` | | Notes on the remote endpoint location/panel. |
| `created_at` | `TIMESTAMPTZ`| `NULL` | `CURRENT_TIMESTAMP` | Audit timestamp. |
| `updated_at` | `TIMESTAMPTZ`| `NULL` | `CURRENT_TIMESTAMP` | Audit timestamp. |

---

## 🔗 Conditional Connection (Polymorphic Association)

The following columns implement the relationship where a `panel_port` can connect to either a normal `ports` table record (for another piece of hardware) or a `cross_connect` record (for a circuit).

| Column | Type | Nullable | Role |
| :--- | :--- | :--- | :--- |
| **`connected_object_id`** | `UUID` | `NULL` | **Polymorphic Foreign Key.** Holds the ID of the connected endpoint. |
| **`connected_object_type`**| `VARCHAR(20)` | `NULL` | **Discriminator Column.** Specifies *which* table `connected_object_id` references (`'Port'` or `'CrossConnect'`). |

### Rules for the Polymorphic Association

1.  If `connected_object_type` = `'Port'`, then `connected_object_id` must reference `ports.port_id`.
2.  If `connected_object_type` = `'CrossConnect'`, then `connected_object_id` must reference `cross_connect.connector_id`.
3.  If both `connected_object_id` and `connected_object_type` are `NULL`, the port is unused (available).
4.  The combination of `panel_id` and `port_number` must be unique.



---

## Constraints & Relationships

### Primary and Unique Constraints
* `panel_port_pkey`: **Primary Key** on `panel_port_id`.
* `panel_port_unique_port`: **Unique Constraint** on (`panel_id`, `port_number`).

### Foreign Key Constraints

| Constraint Name | Column | References Table | References Column | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `fk_panel_port_panel_id` | `panel_id` | `devices` | `device_id` | Links the port back to the device (patch panel) it resides on. |
| `fk_panel_port_connector_id` | `connector_id` | `connector_types` | `connector_id` | Links to the physical interface specifications. |

***

Would you like to review the next table in the sequence, perhaps the **`cross_connects`** table, to ensure it uses the final `device_id` scheme?