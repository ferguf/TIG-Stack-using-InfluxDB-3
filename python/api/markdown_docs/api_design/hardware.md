This is a sophisticated topic that requires documentation clarity. Adopting the style of a technical author writing for a Materials and BOM (Bill of Materials) audience ensures precision and standardization.

Here is the design document in the requested technical style and Markdown format.

---

## 📄 `materials_and_bom.md`

# 🔩 Component and Material Management Design Specification (CMMS)

## 1. Introduction and Scope

This document details the database schema for the management of raw materials, components, and the definition of component qualification lists (Bill of Materials - BOMs) for manufactured or deployed hardware models. The design focuses on standardizing part numbers, tracking vendor information, lifecycle status, and formally defining the relationship between generic materials and specific hardware products.

## 2. Entity Specifications

### 2.1. `materials` (Material Master Data)

This table serves as the single source of truth for all physical components and inventory items within the organization.

| Field Name | Data Type | Description | Constraints / Usage Notes |
| :--- | :--- | :--- | :--- |
| `material_id` | `UUID` | **Primary Key.** Unique Material Master record identifier. | PK, `gen_random_uuid()`, Globally Unique |
| `material_type` | `VARCHAR(50)` | Component category (e.g., 'Hardware', 'Fiber', 'Passive', 'Cable'). | **Crucial for classification.** |
| `part_number` | `VARCHAR(100)` | The manufacturer's or vendor's official part number. | **UNIQUE, NOT NULL**, Essential for procurement. |
| `description` | `VARCHAR(255)` | Detailed, standardized component description. | |
| **Lifecycle & Compliance** | | | |
| `EOL_date` | `DATE` | **End-of-Life Date.** Date the item will no longer be supported/produced. | |
| `certification_status` | `VARCHAR(50)` | Regulatory compliance status (e.g., 'Certified', 'Pending', 'Failed'). | |
| `is_active` | `BOOLEAN` | Flag indicating if the item is currently available for procurement/use. | Default: TRUE |
| **Vendor & Costing** | | | |
| `vendor_name` | `VARCHAR(100)` | Primary manufacturer/supplier. | |
| `vendor_id` | `VARCHAR(50)` | Vendor-specific identifier. | |
| `unit_of_measure` | `VARCHAR(20)` | UOM for inventory (e.g., 'Each', 'Meter', 'Roll'). | NOT NULL |
| `lumen_cost` | `DECIMAL(15, 4)` | Calculated final internal cost per unit. | |
| `created_at` | `TIMESTAMPTZ` | Record insertion timestamp. | |
| `updated_at` | `TIMESTAMPTZ` | Record last modification timestamp. | |

### 2.2. `hardware_material_qualification` (BOM/Superset Junction)

This table establishes the Many-to-Many relationship between a specific hardware model (`hardware_specs`) and the materials that are either required or qualified for use. This design effectively manages both **As-Built** and **Superset** material lists.

| Field Name | Data Type | Description | Constraints / Usage Notes |
| :--- | :--- | :--- | :--- |
| `hardware_material_id` | `UUID` | **Primary Key.** Unique linkage identifier. | PK, `gen_random_uuid()` |
| `hardware_id` | `UUID` | **Foreign Key** to the parent hardware model (`hardware_specs`). | FK, NOT NULL |
| `material_id` | `UUID` | **Foreign Key** to the component (`materials`). | FK, NOT NULL |
| **`bom_type`** | `VARCHAR(50)` | **List Classification:** 'Required' (As-Built BOM) or 'Qualified' (Superset/Compatibility List). | NOT NULL |
| `quantity` | `DECIMAL(10, 2)` | The component count required for the parent unit (if `bom_type`='Required'). | NOT NULL |
| `notes` | `VARCHAR(255)` | Specific notes on installation, substitution, or qualification status. | |
| **Composite Key** | | | `UNIQUE(hardware_id, material_id, bom_type)` |

## 3. Relational Model and Data Flow

The relationship is defined by linking the two primary entity tables (`hardware_specs` and `materials`) through the `hardware_material_qualification` junction table. This structure is essential for decoupling the product definition from the component list. 

### 3.1. Foreign Key Constraints

| Parent Table | Child Table | Foreign Key Field | Description |
| :--- | :--- | :--- | :--- |
| `hardware_specs` | `hardware_material_qualification` | `hardware_id` | Links the BOM to the physical product model definition. |
| `materials` | `hardware_material_qualification` | `material_id` | Links the BOM to the specific component master record. |

### 3.2. List Differentiation (`bom_type`)

The design supports two distinct list definitions, queried using the `bom_type` field:

1.  **Required (As-Built BOM):** Components necessary for the initial assembly or deployment of the hardware unit. Used for procurement and final assembly instructions.
2.  **Qualified (Superset List):** Components that are certified as compatible and can be used for maintenance, upgrades, or field replacement. Used for inventory and maintenance planning.

## 4. Implementation Details

* **Database:** PostgreSQL
* **Keying:** All primary and foreign keys utilize the `UUID` data type to support distributed systems and prevent sequential data bottlenecks.
* **Uniqueness:** A composite unique key is enforced on (`hardware_id`, `material_id`, `bom_type`) to ensure a single hardware model cannot have redundant listings for the same material within the same list classification.
* **Data Integrity:** The final cost (`lumen_cost`) should ideally be calculated and populated by a backend service to maintain accuracy based on the `vendor_unit_cost` and `vendor_unit_discount`.