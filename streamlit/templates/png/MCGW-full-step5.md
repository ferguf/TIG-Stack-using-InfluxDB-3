# **MCGW Full Provisioning Workflow**

**Service Type:** Multi-Cloud Gateway (MCGW)  
**Flavor:** Full  
**Architecture:** Multi-port / High-Availability Virtual Routing Instance  
---
## **1. Overview**
The **MCGW Full** flavor is designed for enterprise‑grade multi‑cloud architectures. Unlike the Limited version, the Full service supports:

- Multiple physical or virtual port attachments  
- Higher bandwidth tiers  
- Redundant routing constructs  
It functions as a **centralized routing hub** within the network fabric, aggregating traffic from:
- AWS  
- Azure  
- Google Cloud  
- On‑premise data centers  
---
## **2. Provisioning Steps**
### **Step 1: VRF / Service Context**
- **Instance Creation:**  
  Define the VRF name and global Route Target (RT).
- **Capacity Planning:**  
  Select bandwidth throughput (e.g., 10G, 50G, Unlimited).
- **Status:**  
  The logical routing container is initialized in the fabric controller.
---
### **Step 2: Fabric Port Assignment**
- **Interface Selection:**  
  Associate the gateway with specific physical handoffs or LAG (Link Aggregation) groups.
- **VLAN Tagging:**  
  Assign outer 802.1Q tags for traffic separation.
---
### **Step 3: Layer 3 Interface & Routing**
- **IP Assignment:**  
  Define Point‑to‑Point (P2P) addressing for cloud interconnects.
- **BGP Configuration:**  
  Establish BGP peering sessions.  
  Full mode typically includes multiple neighbors for redundancy.
- **Static Routes (Optional):**  
  Define manual overrides for specific prefix reachability.
---
### **Step 4: Private Peering (XaaS)**
- **Cloud Exchange:**  
  Connect the MCGW to Cloud Service Providers (CSPs).
- **Virtual Cross‑Connects (VXC):**  
  Provision virtual circuits bridging the Fabric Port to the Cloud Router.
---
### **Step 5: Connection Management**
- **Traffic Policy:**  
  Apply bandwidth limits per connection.
- **Validation:**  
  Ensure the sum of all connection bandwidths does not exceed the MCGW Service BW selected in Step 1.
---
## **3. Technical Constraints & Rules**

| Feature       | Constraint                                              |
|---------------|----------------------------------------------------------|
| Bandwidth     | Must be ≤ aggregate gateway tier                         |
| Peering       | Supports Multi‑Hop BGP and MD5 authentication            |
| Redundancy    | Primary/Secondary port pairing highly recommended        |
| MTU           | Standard (1500) or Jumbo (9000) based on CSP support    |
---
## **4. Deployment Checklist**
- [ ] VRF name matches naming convention  
- [ ] ASN is unique within the tenant  
- [ ] All P2P IP addresses validated against IPAM  
- [ ] BGP prefix limits configured to prevent route table overflow  