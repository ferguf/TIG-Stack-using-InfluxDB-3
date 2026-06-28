Here is a detailed Design Guide for the **Customer Management Module**, written in the style of a technical architect.

---

# Design Guide: Customer Management Module

## Overview

The Customer Management module serves as the foundational identity layer for the infrastructure fabric. It manages the lifecycle of `Customer` entities, providing a centralized mapping between physical infrastructure (racks/ports) and logical ownership (accounts).

---

## 1. Architectural Patterns

### The Router-Operation-Schema Triad

This module follows a strict separation of concerns to ensure maintainability:

* **API Layer (`routers/customers.py`)**: Handles the HTTP interface, input validation via Pydantic, and status code management.
* **Logic Layer (`api_operation.py`)**: Abstracts database interactions. It encapsulates the "Session" context, preventing the API layer from leaking database transaction logic.
* **Data Layer (`Customer` Model)**: The SQLAlchemy representation of the database state.

### Dependency Management

To avoid circular imports and pathing issues in a distributed directory structure, we utilize dynamic path injection for script resolution:

```python
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(BASE_DIR, "..", "..", "scripts")
sys.path.append(SCRIPTS_DIR)

```

---

## 2. Data Model Design

### Customer Entity

The `Customer` entity is designed for high auditability and relational integrity.

| Attribute | Type | Purpose |
| --- | --- | --- |
| `customer_id` | **UUID** (PK) | Immutable unique identifier. |
| `customer_name` | **String(255)** | Human-readable identifier for UI/Display. |
| `account_id` | **String(50)** | Internal billing/CRM reference ID. |
| `created_at` | **DateTime** | Auto-populated timestamp on record creation. |

### Relational Constraints

The model implements a **Cascade Delete** strategy. Because a `Customer` is the root of the service tree, deleting a customer will trigger a recursive cleanup of all associated `FabricService` entries:
`cascade="all, delete-orphan"`

---

## 3. CRUD Implementation Details

### List & Filter (`GET /`)

Retrieves a full collection of customers. The API transforms the raw database model into the `CustomerOut` schema, injecting calculated fields such as `service_count` (defaulted to `0` in the current iteration).

### Safe Updates (`PUT /{id}`)

Updates utilize the `setattr` pattern to dynamically map incoming Pydantic schema data to the SQLAlchemy object. This ensures that only provided fields are modified while maintaining the integrity of metadata like `created_at`.

### Error Handling Protocol

The module utilizes a fail-fast approach with `fastapi.HTTPException`:

* **404 Not Found**: Returned when a UUID does not match an existing record.
* **400 Bad Request**: Returned if a creation attempt fails due to database constraints (e.g., unique name violations).

---

## 4. Operation Best Practices

> [!IMPORTANT]
> **Transaction Integrity**: All `api_operation` methods use the `with get_db_session() as db:` context manager. This ensures that database connections are automatically returned to the connection pool, even if a runtime error occurs during the transaction.

### Example Sequence: Creating a Customer

1. **Validation**: Pydantic validates the `CustomerIn` payload (JSON).
2. **Context**: The API invokes `api_operation.post_customer`.
3. **Persistence**: The DB session begins, the object is added, and `db.commit()` is called.
4. **Refresh**: `db.refresh(new_customer)` is called to retrieve the auto-generated UUID and timestamps.
5. **Output**: The record is serialized back to `CustomerOut`.

---

## 5. Future Extensibility

* **Service Counting**: The `service_count` field in `CustomerOut` is ready for a `func.count()` subquery to provide real-time metrics on customer footprint.
* **Soft Deletes**: Consider adding a `deleted_at` column instead of a hard `db.delete()` to preserve historical data for decommissioned customers.

