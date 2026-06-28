Here is the **Technical Design Guide** for the **Network Device Management** module, tailored to your provided implementation.

---

# Design Guide: Network Device & Hardware Specification

## 1. Module Architecture

The `devices` module provides a comprehensive lifecycle management system for physical network assets. It utilizes a multi-layered approach to separate hardware definitions (specifications and documentation) from logical deployment instances (location and status).

---

## 2. Core Entities

### Device Entity

The primary record for any physical asset in the network.

* **UUID-based Identity**: Uses `as_uuid=True` for native PostgreSQL UUID support.
* **Health Mapping**: Uses an integer-based health status (1-Green, 2-Amber, 3-Red, 4-Unknown) for lightweight monitoring integration.
* **Orphan Cleanup**: Implements `cascade="all, delete-orphan"` on the `ports` relationship, ensuring that when a device is decommissioned, its port records do not clutter the database.

### Supporting Sub-Modules

| Sub-Module | Purpose |
| --- | --- |
| **Hardware Specs** | Standardized definitions of device capabilities (e.g., Juniper MX10004). |
| **Hardware Docs** | Links to technical manuals, pinout diagrams, and vendor datasheets. |
| **LRIC Cost Model** | Tracks Long-Run Incremental Costs for financial auditing and depreciation. |
| **Location** | Tracks the physical rack coordinates (Room, Rack, RU) for a specific `device_id`. |

---

## 3. Implementation Patterns

### Dependency Injection with `get_db`

Unlike the simple context manager pattern, this module utilizes FastAPI's `Depends(get_db)`. This allows for better unit testing by mocking the session and provides automatic cleanup of database connections after the request completes.

```python
@router.post("/", response_model=DeviceOut)
def post_device(data: DeviceIn, db: Session = Depends(get_db)):
    new_device = api_operation.post_device(db, data)
    return DeviceOut.model_validate(new_device)

```

### Enhanced Error Messaging

This module implements "Explanatory Errors." Instead of a generic `404`, the API provides a `detail` object containing the **reason** and a **hint** to assist frontend developers.

```json
{
  "error": "Device not found or update failed",
  "reason": "Invalid device_id or duplicate field values",
  "hint": "Verify device_id exists and unique fields are not duplicated"
}

```

---

## 4. CRUD Operations & Logic

### Creation Sequence

1. **Schema Validation**: Pydantic validates the `DeviceIn` object (e.g., verifying `device_vendor` is present).
2. **Operations Layer**: `api_operation.post_device` explicitly maps fields from the Pydantic schema to the SQLAlchemy `Device` model.
3. **Commit & Refresh**: The database generates the `created_at` and `updated_at` timestamps, which are refreshed back into the Python object.
4. **Validation**: `DeviceOut.model_validate(new_device)` ensures the response matches the security and visibility requirements of the API.

### The `put_device` Dynamic Mapping

To handle partial updates, the logic uses the `setattr` pattern. This allows the API to scale; if a new field (like `serial_number`) is added to the database, the update logic does not need to be rewritten.

---

## 5. Deployment Considerations

> [!WARNING]
> **Serial Number Uniqueness**: Ensure that the `serial_number` column (referenced in `post_device` but missing from the `Device` class snippet) is added with a `unique=True` constraint to prevent duplicate assets in the inventory.

### Scaling Advice

* **Pagination**: As the device count exceeds 1,000, the `get_devices()` endpoint should be updated to include `limit` and `offset` parameters to prevent memory exhaustion.
* **Health Monitoring**: The `health_status` integer is ready to be polled by an asynchronous background task (e.g., Celery or FastAPI BackgroundTasks) to update statuses based on SNMP or ICMP results.

