# Design Guide: Fabric Service Management

## 1. Module Purpose

The **Fabric Service** module is the orchestrator of logical connectivity within the infrastructure. It acts as the container for network products (such as E-Line, E-LAN, or Cloud Connect) associated with a specific customer.

While a `Customer` represents a legal/billing entity, the `FabricService` represents a specific provisioned instance of a network product, holding critical routing metadata like **Route Targets** and **Service Types**.

---

## 2. Technical Design

### Data Entity: `FabricService`

The model is designed to be the "parent" of physical port assignments and logical connections.

| Attribute | Type | Description |
| --- | --- | --- |
| `service_type` | **String** | The classification of service (e.g., 'Layer2', 'VPRN'). |
| `route_target` | **String** | The BGP community string used for VRF import/export logic. |
| `health_status` | **Integer** | Real-time operational state (Default: 4/Unknown). |
| `service_alias` | **String** | Customer-facing secondary identifier. |

### Relational Dynamics

* **Many-to-One (`Customer`)**: Multiple services can be "owned" by a single customer.
* **One-to-Many (`Port`)**: A service can span multiple physical ports across different devices.
* **Recursive Cleanup**: The `cascade="all, delete-orphan"` ensures that when a service is terminated, its associated logical port configurations are purged to prevent "zombie" configs in the database.

---

## 3. Operational Logic

### Hierarchical Querying

The API supports two primary retrieval patterns:

1. **Global Registry**: `GET /` for administrative overviews.
2. **Customer-Centric**: `GET /customer/{customer_id}` to power customer portals or billing audits.

### The "Patch" Update Strategy

In the `update_fabric_service` function, we utilize the `exclude_unset=True` pattern. This is a critical design choice for network infrastructure APIs, as it allows the system to update a single field (like a `service_description`) without risking the accidental nullification of critical networking fields like `route_target`.

```python
for field, value in data.dict(exclude_unset=True).items():
    setattr(service, field, value)

```

---

## 4. API Implementation Patterns

### Response Validation

The use of `FabricServiceOut.model_validate(s)` ensures that sensitive database fields (like internal DB IDs or raw transaction logs) are stripped before being sent to the client, returning only what is defined in the Pydantic schema.

### Error Handling

The `delete_fabric_service` endpoint implements an explicit check for existence. If a deletion is attempted on a non-existent UUID, the system returns a standard `404 Not Found` rather than a database error, providing a cleaner interface for automation scripts.

---

## 5. Architectural Recommendations

> [!IMPORTANT]
> **Schema Consistency**: The `DeleteResponse` message currently refers to `FabricPort` in the logic, but the route is for `FabricService`. For documentation clarity, the success message should be updated to match the entity name.

### Future Roadmap

* **Service Orchestration**: Integrate a `POST` hook that triggers an Ansible or Terraform run whenever a service is created with a valid `route_target`.
* **State Machine**: Transition `health_status` from a simple integer to a dedicated state machine that reflects the actual BGP/UP-DOWN status of the underlying infrastructure.

---

**Would you like me to draft the "Patch Panel" or "Cross Connect" design guide next to complete the physical layer documentation?**