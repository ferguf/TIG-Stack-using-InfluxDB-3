# Route Targets Schema Documentation

## Overview

The `route_targets` table stores route target identifiers used in network routing policies. Route targets are essential in MPLS VPN and EVPN environments to control route import and export policies across different routing instances.

## Schema Definition

| Column Name | Data Type | Constraints | Description | 
| --- | --- | --- | --- | 
| id | integer | Primary Key, Auto-increment | Unique identifier for each route target entry | 
| name | string | Unique, Not Null | Human-readable name for the route target | 
| asn | integer | Not Null | Autonomous System Number part of the route target | 
| target | string | Not Null | Route target value in the format `ASN:NN` or `ASN:NNNN` | 
| description | string | Nullable | Optional description or notes about the route target | 
| created_at | datetime | Default current timestamp | Timestamp when the entry was created | 
| updated_at | datetime | Default current timestamp, updated on change | Timestamp when the entry was last updated | 

## Example Insert

```sql
INSERT INTO route_targets (name, asn, target, description) VALUES
('CustomerA-RT1', 3569, '8000:100001', 'Primary route target for Customer A'),
('CustomerA-RT1', 3569, '8000:100001', 'Primary route target for Customer B'),
('CustomerB-RT1', 'Metro denver', '8001:100001', 'Primary route target fabric path A in Mertro Denver '),
('CustomerB-RT1', 'Metro  NYC', '8002:100001', 'Primary route target fabric path A in Mertro NYC ');


Perfect — thanks for clarifying with the example. What you want is for the `route_target` column to **auto-generate a composite string like `network_base:some_sequence`**, rather than just `network_base:<network_base>`.

That means you need two things:
1. A **sequence or counter** that increments for each new row (to produce the `1000001` part in your example).  
2. A **default expression** that concatenates `network_base` with that sequence value.

---

### Example Schema

```sql
-- Create a sequence for route_target suffix
CREATE SEQUENCE route_target_seq START 1000001;

CREATE TABLE route_targets (
    route_target_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_id UUID,                          
    network VARCHAR(64) NOT NULL,             
    network_base INTEGER NOT NULL,            
    route_target VARCHAR(128) DEFAULT (
        network_base::text || ':' || nextval('route_target_seq')
    ), 
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### Example Inserts

#### Auto-generated
```sql
INSERT INTO route_targets (service_id, network, network_base)
VALUES (gen_random_uuid(), '3549', 8001);
```

**Resulting row:**

| route_target_id                          | service_id | network | network_base | route_target   | created_at           | updated_at           |
|------------------------------------------|------------|---------|--------------|----------------|----------------------|----------------------|
| 3f2a8c7e-9d4a-4b1a-9a2f-7c8f9a1d2b3c     | …          | 3549    | 8001         | 8001:1000001   | 2025-12-18 13:21:00 | 2025-12-18 13:21:00 |

---

#### Next Insert
```sql
INSERT INTO route_targets (service_id, network, network_base)
VALUES (gen_random_uuid(), '3549', 8001);
```

**Resulting row:**

| route_target_id                          | service_id | network | network_base | route_target   | created_at           | updated_at           |
|------------------------------------------|------------|---------|--------------|----------------|----------------------|----------------------|
drop 

---

### Key Notes
- The `route_target_seq` ensures uniqueness and increments automatically.  
- The `DEFAULT` expression concatenates `network_base` with the next sequence value.  
- You can still override `route_target` manually if needed by specifying it in the `INSERT`.

---

👉 This matches exactly the format you showed: `network_base:1000001`.  

Do you want me to also add a **unique constraint on `(network_base, route_target)`** so that no duplicates can ever slip in, even if someone overrides manually?
