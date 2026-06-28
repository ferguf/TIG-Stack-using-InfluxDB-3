Here is the documentation for the `Network_links` and `ROP_channel_members` tables, presented in the style of a technical design document.

***

# Network Links and ROP Channel Management Design Specification

## 1. Introduction: The Need for Abstract Topology

In a complex network inventory system, linking entities together to describe connectivity is essential. However, connectivity exists across multiple layers: physical (port-to-port), logical (interface-to-interface), and abstract (LAGs, ROPs). The **`network_links`** table is designed as a single, flexible solution to capture these **polymorphic** and **abstract** relationships, agnostic of the underlying entity type.

The **`rop_channel_members`** table then provides the required detail to manage the channelized nature of Routed Optical Paths (ROPs), enforcing the crucial constraint that each constituent channel within a given ROP is unique.

## 2. Network Links (`network_links`)

The `network_links` table is the central hub for defining peer-to-peer relationships between any two trackable UUID-identified entities in the system.

### 2.1. Table Schema (`network_links`)

| Column Name | Data Type | Nullable | Description | Key / Constraint |
| :--- | :--- | :--- | :--- | :--- |
| `link_id` | `UUID` | NO | Primary Key. Unique identifier for the abstract link. | **PK** |
| `a_side_id` | `UUID` | NO | UUID of the source entity. | |
| `a_side_type` | `VARCHAR(50)` | NO | Type of source entity (e.g., 'Device', 'Interface', 'Port'). | |
| `z_side_id` | `UUID` | NO | UUID of the destination entity. | |
| `z_side_type` | `VARCHAR(50)` | NO | Type of destination entity. | |
| `link_type` | `VARCHAR(50)` | NO | Classification of the link (e.g., 'Physical', 'ROP', 'Intra-Pop'). | |
| `description` | `VARCHAR(512)` | YES | Human-readable explanation of the link's purpose. | |
| `channel` | `INTEGER` | YES | Optional: Used to identify specific channels within an ROP LAG (1-32). | |
| `frequency` | `VARCHAR(50)` | YES | Optional: Used for DWDM/optical frequency information on ROPs. | |
| `created_at` | `timestamptz` | NO | Record creation timestamp. | |
| `updated_at` | `timestamptz` | NO | Record update timestamp. | |

### 2.2. Link Type Examples

The `link_type` field categorizes the relationship, making the link graph queryable based on abstraction level.

| `link_type` | A-Side Entity | Z-Side Entity | Example Relationship |
| :--- | :--- | :--- | :--- |
| **Physical** | `Port` or `PanelPort` | `Port` or `PanelPort` | Device-A/Port#X **to** Device-B/Port#Y (Direct cable run) |
| **LAG (L2/L3)** | `Interface` (e.g., `xe-1/0/0`) | `Interface` (e.g., `xe-1/0/1`) | Logical link between two interfaces **on the same device** forming a bundle. |
| **AE** | `Interface` (e.g., `ae1`) | `Interface` (e.g., `ae2`) | Logical link **between two aggregate interfaces** (AE bundles). |
| **ROP** | `Interface` (e.g., `ae1`) | `Interface` (e.g., `ae1`) | **Routed Optical Path:** Used to signify an aggregated, high-capacity, channelized optical link between two devices. The link is defined between the two devices' LAG interfaces. |
| **Intra-Pop** | `Interface` | `Interface` | Logical link between two endpoints **within the same Point of Presence (PoP)**. |
| **Inter-Pop** | `Interface` | `Interface` | Logical link connecting two endpoints **in different PoPs**. |

## 3. ROP Channel Management (`rop_channel_members`)

When the `link_type` in `network_links` is **'ROP'** (representing a high-level LAG/Bundle), the actual physical or logical channels that make up that bundle need to be tracked. The `rop_channel_members` table handles this assignment.

### 3.1. Table Schema (`rop_channel_members`)

| Column Name | Data Type | Nullable | Description | Key / Constraint |
| :--- | :--- | :--- | :--- | :--- |
| `rop_member_id` | `UUID` | NO | Primary Key for the channel member record. | **PK** |
| `rop_link_id` | `UUID` | NO | Foreign Key to the parent 'ROP' link in `network_links`. | **FK** to `network_links.link_id` |
| `channel_id` | `INTEGER` | NO | The specific channel number (1-32) assigned to this member. | |
| `a_side_endpoint_id` | `UUID` | NO | UUID of the physical interface/port making up the A-side channel. | |
| `a_side_endpoint_type` | `VARCHAR(50)` | NO | Type of A-side endpoint (e.g., 'Interface', 'Port'). | |
| `z_side_endpoint_id` | `UUID` | NO | UUID of the physical interface/port making up the Z-side channel. | |
| `z_side_endpoint_type` | `VARCHAR(50)` | NO | Type of Z-side endpoint. | |
| `description` | `VARCHAR(255)` | YES | Channel-specific description. | |
| `created_at` | `timestamptz` | NO | Record creation timestamp. | |
| `updated_at` | `timestamptz` | NO | Record update timestamp. | |

### 3.2. ROP Channel Constraint

The core business logic is enforced by a unique constraint on the pair:

$$\text{Unique Constraint: } (\text{rop\_link\_id}, \text{channel\_id})$$

This ensures that within a single ROP bundle (e.g., ROP-1), you cannot assign Channel 5 more than once. 

## 4. Operational Flow Example

Here is a step-by-step example of how a channelized ROP link is modeled:

### Step 1: Define the Aggregate ROP Link (in `network_links`)

A high-level ROP is created, linking two aggregate interfaces (AE bundles) that terminate the logical path.

| `link_id` | `a_side_id` | `a_side_type` | `z_side_id` | `z_side_type` | `link_type` | `channel` | `description` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `ROP-123` | `AE-A-UUID` | `Interface` | `AE-B-UUID` | `Interface` | `ROP` | NULL | Aggregate ROP between Device A and Device B. |

### Step 2: Define Individual Channel Members (in `rop_channel_members`)

Individual channels are then defined, linking the physical interfaces that are members of the respective AE bundles.

| `rop_member_id` | `rop_link_id` | `channel_id` | `a_side_endpoint_id` | `a_side_endpoint_type` | `z_side_endpoint_id` | `z_side_endpoint_type` | `description` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `Chan-1-UUID` | `ROP-123` | **1** | `Intf-A-01` | `Interface` | `Intf-B-11` | `Interface` | Channel 1, 100G service. |
| `Chan-2-UUID` | `ROP-123` | **2** | `Intf-A-02` | `Interface` | `Intf-B-12` | `Interface` | Channel 2, 10G protection. |
| `Chan-3-UUID` | `ROP-123` | **3** | `Intf-A-03` | `Interface` | `Intf-B-13` | `Interface` | Channel 3, Provisioning spare. |

### Step 3: Define a Simple Physical Link (in `network_links`)

For comparison, a simple physical link (e.g., a cross-connect termination) is also stored in `network_links`.

| `link_id` | `a_side_id` | `a_side_type` | `z_side_id` | `z_side_type` | `link_type` | `channel` | `description` |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PHY-456` | `Port-A-UUID` | `PanelPort` | `Port-B-UUID` | `PanelPort` | `Physical` | NULL | Cross-connect Jumper from Patch Panel A to Patch Panel B. |

ROP (Regional Optical Platform) Hierarchy
The design distinguishes between a "Link" (the physical fiber path) and "Channels" (individual wavelengths or logical members within that path).

NetworkLink (Parent): Represents the aggregate ROP span.

ROPChannelMember (Child): Represents specific channel IDs (1-32) within that span.

3. Operational Implementation
Integrity Constraints
The module implements a complex UniqueConstraint within the rop_channel_members table. This prevents "Channel Collision" by ensuring a channel_id is unique only within the scope of its specific parent rop_link_id.

Python

__table_args__ = (
    UniqueConstraint('rop_link_id', 'channel_id', name='uq_rop_link_channel'),
)
Transaction Management
The api_operation layer utilizes an explicit rollback() strategy. Because network links often involve multiple polymorphic checks, an IntegrityError (such as a duplicate channel ID) triggers a clean state reversal to prevent partial or orphaned data.

4. API Specification
Polymorphic Link Creation
The POST /network-links/ endpoint acts as a universal connector.

[!IMPORTANT] Application-Level Validation: While the database stores the a_side_id, the application logic must verify that the ID exists within the table specified by a_side_type.

Channel Member Resolution
The API provides a hierarchical lookup to find all members of an optical span: GET /network-links/ROP/{rop_link_id}

5. Maintenance & Safety
Safe Updates
The put_network_link method uses model_dump(exclude_unset=True). In a ROP environment, this is critical; it allows an operator to update the frequency of a span without inadvertently changing the link_type or endpoint identifiers.

Error Handling
The module maps sqlalchemy.exc.IntegrityError to a readable ValueError. This ensures that if a user tries to assign a channel ID that is already in use for that specific span, the API returns a 400 Bad Request with a clear explanation rather than a 500 Internal Server Error.