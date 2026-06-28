Here is the documentation for the `lric_cost_model` table, written in the style of a technical design document.

-----

# Long-Run Incremental Cost (LRIC) Model Specification

## 1\. Introduction: Purpose and Scope

The **`lric_cost_model`** table is a critical component for financial and regulatory compliance within the network inventory system. It is designed to store the parameters necessary to calculate the Long-Run Incremental Cost (LRIC) associated with specific network elements, devices, or services.

The primary function of this model is to provide auditable, calculated cost figures based on a set of input variables, notably the **base cost** and the regulatory **LRIC fill percentage**.

## 2\. LRIC Model Schema (`lric_cost_model`)

This table uses a generated column to ensure that the final, calculated LRIC cost is always synchronized with its source inputs, enforcing data integrity at the database layer.

### 2.1. Table Definition

| Column Name | Data Type | Nullable | Default / Constraint | Description |
| :--- | :--- | :--- | :--- | :--- |
| `cost_model_id` | `UUID` | NO | `gen_random_uuid()` | Primary Key. Unique identifier for this cost model record. |
| `model_id` | `UUID` | NO | None | Foreign Key to the specific resource being costed (e.g., a Device ID, a Port ID). |
| `model_type` | `VARCHAR(50)` | NO | None | The type of resource this model applies to (e.g., 'Device', 'Port', 'FiberSpan'). |
| `description` | `VARCHAR(255)` | YES | None | Detailed description of the cost model's application. |
| **`base_cost`** | `NUMERIC(15, 4)` | NO | None | The unadjusted, raw long-run cost (e.g., annualized capital cost + Opex). |
| **`lric_fill`** | `INTEGER` | YES | Check (`0` to `100`) | The percentage of capacity utilization mandated by the LRIC methodology. |
| `min_fill` | `INTEGER` | YES | None | The minimum required capacity fill percentage. |
| `type` | `VARCHAR(50)` | YES | None | Internal classification for the cost record (e.g., 'Transport', 'Access'). |
| `min_level` | `NUMERIC(15, 4)` | YES | None | Used in certain capacity-based cost formulas. |
| `level` | `NUMERIC(15, 4)` | YES | None | Used in certain capacity-based cost formulas. |
| **`calculated_lric_cost`** | `NUMERIC(15, 4)` | YES | **GENERATED ALWAYS STORED** | The final, calculated LRIC cost. |
| `created_at` | `timestamptz` | NO | `CURRENT_TIMESTAMP` | Record creation timestamp. |
| `updated_at` | `timestamptz` | NO | `CURRENT_TIMESTAMP` | Record update timestamp. |

### 2.2. Generated Column Logic

The **`calculated_lric_cost`** is a **computed column**, calculated directly within the database engine using the following formula:

$$\text{Calculated Cost} = \text{Base Cost} \times \left( \frac{\text{LRIC Fill}}{100.0} \right)$$

**PostgreSQL DDL Definition:**

```sql
calculated_lric_cost numeric(15,4)
GENERATED ALWAYS AS ((base_cost * (lric_fill::numeric / 100.0))) STORED
```

This design ensures that:

1.  The `calculated_lric_cost` is read-only from the application layer.
2.  Any update to `base_cost` or `lric_fill` automatically updates the calculated value immediately and consistently.

## 3\. Data Flow and API Interaction

### 3.1. Create (POST) and Update (PUT)

When creating or updating an LRIC record via the API:

  * The application must supply the **`base_cost`** and **`lric_fill`** (which must be between 0 and 100).
  * The application **must not** supply the `calculated_lric_cost`.
  * The database validates the inputs and automatically populates the `calculated_lric_cost` upon commit.

### 3.2. Retrieval (GET)

When retrieving an LRIC record:

  * The `LRICCostModelOut` Pydantic schema will include the `calculated_lric_cost`.
  * This value can be used directly for financial reports or forwarded to billing systems.

### 3.3. Foreign Key Relationship

The `lric_cost_model` is a parent table. Its `cost_model_id` is referenced by downstream operational tables, such as the `devices` table.

$$\text{devices.lric\_model\_id} \rightarrow \text{lric\_cost\_model.cost\_model\_id}$$

This linkage allows the system to instantly determine the regulatory cost associated with any piece of installed hardware or defined service.

## 4\. API Design Summary (Endpoints)

The FastAPI implementation provides standard RESTful access:

| Method | Endpoint | Description | Pydantic Schema |
| :--- | :--- | :--- | :--- |
| `GET` | `/lric-cost-models` | Retrieves all LRIC models. | `List[LRICCostModelOut]` |
| `GET` | `/lric-cost-models/{cost_model_id}` | Retrieves a single model by ID. | `LRICCostModelOut` |
| `POST` | `/lric-cost-models` | Creates a new LRIC model record. | `LRICCostModelIn` |
| `PUT` | `/lric-cost-models/{cost_model_id}` | Updates an existing model record. | `LRICCostModelUpdate` |
| `DELETE` | `/lric-cost-models/{cost_model_id}` | Deletes a model record (fails if referenced by devices). | `dict` |

-----

