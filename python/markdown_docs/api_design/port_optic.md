## 🔌 Port Optics Design Specification: Integrating with the `materials` Inventory

### Introduction

This document details the final relational design for managing Port Optics capabilities. Due to the requirement that each optic type is a managed asset with a unique ID, cost, and lifecycle status, the standard master optics table (`port_optics`) has been deprecated. The **`materials`** table now serves as the authoritative source for all certified optical transceiver specifications.

The core design principle is to create a Many-to-Many junction table that maps individual network **Ports** to the specific list of **Materials** (optics) certified for use on that interface.

-----

## I. Master Data Source: The `materials` Table

The existing `materials` table provides the foundation for identifying and tracking compatible transceivers. Our network capabilities schema relies on this table's `material_id` as the foreign key.

| Column | Role in Network Design |
| :--- | :--- |
| `material_id` | **Primary Key** referenced by all port capability tables. |
| `part_number` | Used for physical ordering/identification. |
| `description` | Used for human-readable optical specification (e.g., "100G - LR4"). |
| `certification_status` | Crucial for deployment logic (ensuring only certified optics are used). |

-----

## II. Capability Mapping: `port_supported_optics` (The Junction Table)

This table defines the list of certified optic materials (`materials.material_id`) that are compatible with a specific instance of a network port (`ports.port_id`). This mechanism provides the necessary granular control to enforce capability constraints at the port level, independent of the general device model.

| Column | Type | Nullable | Description |
| :--- | :--- | :--- | :--- |
| **`port_id`** | `UUID` | `NOT NULL` | **Foreign Key** to the `ports` table. Identifies the specific physical interface. |
| **`material_id`** | `UUID` | `NOT NULL` | **Foreign Key** to the `materials` table. Identifies the certified optic (material). |

### 🛠️ SQL Definition: `port_supported_optics`

```sql
CREATE TABLE IF NOT EXISTS public.port_supported_optics (
    port_id UUID NOT NULL,
    material_id UUID NOT NULL,
    
    -- Composite Primary Key ensures a port-optic material pair is unique
    PRIMARY KEY (port_id, material_id),
    
    -- Foreign Key to the Ports table (the specific interface)
    CONSTRAINT fk_pso_port_id
        FOREIGN KEY (port_id)
        REFERENCES public.ports(port_id) 
        ON DELETE CASCADE,
        
    -- Foreign Key to the Materials table (the certified optic)
    CONSTRAINT fk_pso_material_id
        FOREIGN KEY (material_id)
        REFERENCES public.materials(material_id) 
        ON DELETE RESTRICT -- Prevent deleting a material if a port references it
);
```

### Query Example: Validating Optic Insertion

To check if a specific optic (identified by its `material_id`) is valid for use in a specific port, the application would query:

```sql
SELECT EXISTS (
    SELECT 1
    FROM public.port_supported_optics
    WHERE port_id = 'PORT_UUID_HERE'
    AND material_id = 'OPTIC_MATERIAL_UUID_HERE'
);
```

This completes the highly granular modeling of Port Capabilities. The next logical step is to track how these capabilities are consumed by the actual circuits.

Would you like to design the **`fabric_connections`** table to track the instantiated circuits?