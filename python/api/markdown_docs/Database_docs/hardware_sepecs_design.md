# 💾 Hardware Inventory and Specifications Database Design

## 1. Overview

This document describes the design of the database tables responsible for storing **static hardware specifications** and managing **individual device inventory** within the system. This design uses UUIDs for primary keys to ensure global uniqueness and scalability, and employs PostgreSQL's `TIMESTAMPTZ` and triggers for robust auditing.

## 2. Table Schemas

### 2.1. `power_options` (Reference Table)

Stores standard power configurations to ensure consistency across the system.

| Column Name | Data Type | Description | Constraints / Notes |
| :--- | :--- | :--- | :--- |
| `power_source_id` | `UUID` | **Primary Key.** Unique ID for the power type. | PK, `gen_random_uuid()` |
| `power_type` | `VARCHAR(50)` | AC or DC. | NOT NULL |
| `voltage` | `VARCHAR(50)` | Specific configuration (e.g., '120V', '-48V'). | NOT NULL |
| `description` | `VARCHAR(255)` | Full description of the power source. | |
| `created_at` | `TIMESTAMPTZ` | Record creation timestamp. | Auto-set |
| `updated_at` | `TIMESTAMPTZ` | Record last modification timestamp. | Triggered |

### 2.2. `hardware_specs` (Core Specifications Table)

Stores the generic, immutable specifications for a hardware model.

| Column Name | Data Type | Description | Constraints / Notes |
| :--- | :--- | :--- | :--- |
| `hardware_id` | `UUID` | **Primary Key.** Unique ID for the hardware model. | PK, `gen_random_uuid()` |
| `model_name` | `VARCHAR(100)` | Commercial name/model number. | NOT NULL |
| `manufacturer` | `VARCHAR(100)` | Manufacturer name. | |
| **Dimensions & Specs** | | | |
| `weight_kg` | `DECIMAL(6, 2)` | Weight in kilograms. | |
| `height_mm` | `DECIMAL(6, 2)` | Height in millimeters. | |
| `width_mm` | `DECIMAL(6, 2)` | Width in millimeters. | |
| `depth_mm` | `DECIMAL(6, 2)` | Depth in millimeters. | |
| `power_rating_w` | `DECIMAL(7, 2)` | Maximum power consumption in Watts. | |
| `airflow_direction` | `VARCHAR(50)` | Airflow path (e.g., 'Front-to-Back'). | |
| **Environmentals & Compliance** | | | |
| `power_source_id` | `UUID` | **Foreign Key** to `power_options`. | FK |
| `max_environment_tempc` | `DECIMAL(4, 2)` | Max operating temp (°C). | |
| `nebs_level` | `VARCHAR(50)` | NEBS compliance level. | |
| `certification_data` | `TEXT` | Summary of key certifications. | |
| `updated_at` | `TIMESTAMPTZ` | Record last modification timestamp. | Triggered |

### 2.3. `hardware_documents` (Document Linkage Table)

Links external documentation (PDFs, guides) to a specific `hardware_specs` model.

| Column Name | Data Type | Description | Constraints / Notes |
| :--- | :--- | :--- | :--- |
| `document_id` | `UUID` | **Primary Key.** | PK, `gen_random_uuid()` |
| `hardware_id` | `UUID` | **Foreign Key** to `hardware_specs`. | FK, NOT NULL |
| `document_type` | `VARCHAR(50)` | e.g., 'Installation Guide', 'Datasheet'. | |
| `storage_path` | `VARCHAR(512)` | URL or network path to the document file. | NOT NULL |
| `upload_date` | `TIMESTAMPTZ` | Date the document path was recorded. | Auto-set |

### 2.4. `devices` (Inventory Instance Tracking)

Tracks every unique physical unit deployed in the field. **Crucially links the specific unit to the generic `hardware_specs` via `hardware_id`.**

| Column Name | Data Type | Description | Constraints / Notes |
| :--- | :--- | :--- | :--- |
| `device_id` | `UUID` | **Primary Key.** Unique ID for the physical unit. | PK, `gen_random_uuid()` |
| `hardware_id` | `UUID` | **Foreign Key** to `hardware_specs`. | FK, NOT NULL |
| `serial_number` | `VARCHAR(100)` | Manufacturer's serial number. | UNIQUE, NOT NULL |
| `asset_tag` | `VARCHAR(100)` | Internal inventory tag. | |
| `status` | `VARCHAR(50)` | Current operational status. | |
| **Granular Location** | | | |
| `location_floor` | `VARCHAR(50)` | Building floor or zone. | |
| `location_isle` | `VARCHAR(50)` | Aisle/row identifier. | |
| `location_rack` | `VARCHAR(100)` | Specific rack ID. | |
| **Financials** | | | |
| `lric_costs` | `DECIMAL(15, 4)` | Total LRIC cost allocated to this specific device instance. | |

## 3. Relationships

The design utilizes a standard **One-to-Many** relationship:

* **`hardware_specs` 1 : M `devices`**: One hardware model can correspond to many physical devices.
* **`hardware_specs` 1 : M `hardware_documents`**: One hardware model can have multiple documents.


## 4. Technology

* **Database:** PostgreSQL
* **Key Type:** UUID (Primary/Foreign Keys)
* **Auditing:** `created_at` (Default `CURRENT_TIMESTAMP`) and `updated_at` (Managed by `set_updated_at_timestamp` Trigger).