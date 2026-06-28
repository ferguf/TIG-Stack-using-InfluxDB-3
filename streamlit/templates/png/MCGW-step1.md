Here’s a clear, architecture‑grade description of the **MCGW Limited Functionality** service, written in the same style as your Full‑flavor documentation but scoped down to the constraints you listed. This version is crisp, deterministic, and ready to drop into an HLD or service catalog.

---

# **MCGW Limited Functionality — Service Description**

The **MCGW Limited** flavor is a streamlined variant of the Multi‑Cloud Gateway service, designed for **single‑site, single‑cloud** use cases where simplicity, predictable behavior, and minimal provisioning overhead are the primary goals. Unlike the Full flavor—which supports multi‑port, multi‑cloud, and high‑availability routing constructs—the Limited flavor provides a **constrained, single‑attachment architecture** optimized for customers with a single on‑premise location and a single AWS cloud presence.

This offering is ideal for customers who require deterministic, private connectivity to AWS but do not need multi‑site routing, redundant port attachments, or complex traffic engineering.

---

## **1. Architectural Scope**

### **Customer Topology**
- **One customer site only**  
- **One CE–Fabric attachment**  
- **No multi‑site routing, no hub‑and‑spoke, no mesh**

### **Cloud Topology**
- **One AWS ILM (Interconnect Link Module)** instance  
- No multi‑region, multi‑VPC, or multi‑cloud expansion  
- No secondary cloud routers or redundant ILM paths

### **Fabric Topology**
- **One Fabric Port** assigned to the customer  
- No LAG, no dual‑port redundancy  
- No multi‑port bandwidth aggregation

This creates a deterministic, single‑path architecture with minimal routing complexity.

---

## **2. Functional Characteristics**

### **2.1 Single VRF / Service Context**
The Limited flavor provisions a **single VRF** with:
- One Route Target pair  
- One routing adjacency to AWS  
- One routing adjacency to the customer site  

No additional VRFs, segmentation, or multi‑tenant constructs are supported.

---

### **2.2 Single Fabric Port Attachment**
The customer is connected to the fabric through **one physical or virtual port**, which serves as the sole ingress/egress point for all traffic.

Implications:
- No primary/secondary failover  
- No diverse paths  
- No bandwidth pooling across ports  

This simplifies provisioning and reduces operational overhead.

---

### **2.3 Single AWS ILM Instance**
The Limited flavor supports **one AWS ILM**, which provides:
- A single logical connection to AWS  
- A single BGP session (or pair, depending on AWS requirements)  
- A single VXC or cloud interconnect path  

No additional ILMs, regions, or cloud routers can be added under the Limited SKU.

---

### **2.4 Simplified Routing Model**
Routing is intentionally constrained:
- One CE–Fabric routing adjacency  
- One Fabric–AWS routing adjacency  
- No multi‑neighbor redundancy  
- No complex route‑maps or policy‑based routing  

This ensures deterministic behavior and reduces misconfiguration risk.

---

## **3. Supported Use Cases**

The Limited flavor is designed for:
- A single enterprise site connecting to AWS  
- Basic hybrid cloud workloads  
- Low‑to‑moderate bandwidth requirements  
- Environments where high availability is not mandatory  
- Customers who want a low‑complexity, low‑cost cloud on‑ramp  

It is **not** intended for:
- Multi‑site WAN architectures  
- Redundant or high‑availability cloud connectivity  
- Multi‑cloud or multi‑region deployments  
- Traffic engineering or advanced routing policies  

---

## **4. Technical Constraints**

| Feature | Limited Flavor Constraint |
|--------|----------------------------|
| Customer Sites | 1 site only |
| Fabric Ports | 1 port only |
| AWS ILM Instances | 1 ILM only |
| Redundancy | Not supported |
| LAG / Multi‑Port | Not supported |
| Multi‑Cloud | Not supported |
| Multi‑Region AWS | Not supported |
| Routing | Single adjacency per side |
| MTU | Standard or Jumbo (based on AWS support) |

---

## **5. Operational Behavior**

- **Provisioning is linear**: VRF → Port → ILM → Routing  
- **Health monitoring is simplified**: one path, one cloud, one port  
- **Troubleshooting is deterministic**: no alternate paths or failover states  
- **Bandwidth validation is straightforward**: one connection, one limit  

This makes the Limited flavor extremely predictable and easy to support.

---

## **6. Summary**

The **MCGW Limited Functionality** service is a **single‑site, single‑port, single‑AWS‑ILM** cloud connectivity solution. It provides a clean, deterministic, low‑complexity path between a customer’s on‑premise environment and AWS, without the multi‑port, multi‑cloud, or high‑availability features found in the Full flavor.

It is the ideal choice for customers who want a simple, reliable, and cost‑efficient cloud on‑ramp without the architectural overhead of a full multi‑cloud gateway.
