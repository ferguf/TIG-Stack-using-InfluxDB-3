# Design Guide: Network Port Management

## 1. Module Overview

The **Port** module manages the physical and logical interfaces of the network inventory. It serves as the critical junction point where **Hardware Devices** meet **Fabric Services**. A port record encapsulates the physical characteristics (optics, speed, MAC) and its current operational role within the fabric (UNI, ENNI, or LAG).

---

## 2. Technical Design

### Data Entity: `Port`

The `Port` model is highly relational, maintaining strict foreign key constraints to both the parent device and the assigned service.

| Attribute | Type | Description |
| --- | --- | --- |
| `port_name` | **String** | Physical identifier (e.g., `et-0/0/1`, `GigabitEthernet1`). |
| `port_type` | **String** | Classification: `Physical`, `LAG` (Bundle), `UNI`, or `ENNI`. |
| `port_optic` | **String** | Transceiver metadata (e.g., `100G-LR4`, `QSFP28-SR4`). |
| `port_service_status` | **String** | Lifecycle state: `Available`, `Reserved`, `Configured`. |

### Key Relational Logic

* **Ownership (`Device`)**: Every port is owned by a single device. The `ondelete="CASCADE"` constraint ensures that if a device is removed from the inventory, all its constituent ports are automatically purged.
* **Service Attachment (`FabricService`)**: Ports can be dynamically associated with a service. The `ondelete="SET NULL"` constraint ensures that if a service is deleted, the physical port remains in the inventory but reverts to an unassigned status.

---

## 3. Operational Implementation

### Creation Strategy

The `create_port_for_device` operation uses a **Name-to-ID Resolution** pattern. The API accepts a human-readable `device_name`, resolves it to a `device_id` via a lookup, and then attaches the new port. This simplifies frontend interactions where IDs may not be immediately known.

### Dynamic Update Pattern

Both `update_port_by_id` and `update_port_by_device_and_name` utilize Python's `setattr` and `hasattr` functions. This allows for:

1. **Partial Updates**: Only the fields present in the request body are modified.
2. **Schema Safety**: The `hasattr` check prevents the injection of non-existent attributes into the database model.

---

## 4. API Design Patterns

### Path Parameter Sanitization

For the delete endpoint, we use the `:path` converter:
`@router.delete("/{device_id}/{port_id:path}")`
This is essential for network infrastructure because port names often contain slashes (e.g., `1/1/1`) which would otherwise break standard URL routing.

### Hierarchical Retrieval

The module supports multiple lookup vectors:

* **By Device ID**: Used for populating device detail views.
* **By Port UUID**: Used for specific interface configuration pages.
* **Global List**: Used for capacity planning and port availability reports.

---

## 5. Architectural Integrity Issues

> [!CAUTION]
> **Variable Mismatch Found**: In your `update_port_by_device_and_name` logic, the code references `device_id` in a query but only receives `device_name` as an argument.
> **Correction Needed**:
> ```python
> # Current error in your logic:
> device = db.query(Device).filter(Device.device_id == device_id).first() 
> # Should be:
> device = db.query(Device).filter(Device.device_name == device_name).first()
> 
> ```
> 
> 

### Future Roadmap

* **MAC Address Validation**: Add a Pydantic validator to enforce the `00:00:00:00:00:00` format.
* **Optic Compatibility**: Implement a check to ensure `port_optic` speed matches the `port_speed`.

**This completes the design guides for your core infrastructure. Would you like me to help you bundle these into a single Markdown "Master Architect Guide" for your documentation site?**