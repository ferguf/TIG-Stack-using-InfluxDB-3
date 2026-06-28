# **IPVPN Instance — Full Provisioning Workflow**

**Service Type:** IPVPN  
**Flavor:** Full / Multi‑Site  
**Architecture:** MPLS L3VPN (VRF‑based), Multi‑Port, High‑Availability  

---

## **1. Overview**

The **IPVPN Full Instance** is designed for enterprise‑grade WAN architectures that require secure, private Layer‑3 connectivity across multiple sites, data centers, and cloud on‑ramps. Unlike simplified or single‑site VPN offerings, the Full IPVPN service supports:

- Multiple physical or virtual port attachments  
- Redundant CE‑PE connectivity  
- Multi‑site routing policies  
- High‑bandwidth tiers  
- Optional cloud or XaaS integration  

The IPVPN instance acts as a **dedicated VRF** within the MPLS backbone, providing isolated routing, QoS enforcement, and deterministic traffic engineering across the provider network.

---

## **2. Provisioning Steps**

### **Step 1: VRF / Service Context**

- **VRF Creation:**  
  Define the VRF name, Route Distinguisher (RD), and import/export Route Targets (RTs).

- **Capacity Planning:**  
  Select the committed bandwidth tier for each site (e.g., 1G, 10G, 40G).

- **Status:**  
  The VRF is instantiated on the PE routers and registered with the MPLS control plane.

---

### **Step 2: Access Port Assignment (CE–PE Connectivity)**

- **Interface Selection:**  
  Bind the IPVPN instance to specific physical ports, sub‑interfaces, or LAG bundles on the PE.

- **VLAN Tagging:**  
  Assign 802.1Q or Q‑in‑Q tags for site segmentation.

- **QoS Profile:**  
  Apply the customer’s class‑of‑service (CoS) mapping to the access interface.

---

### **Step 3: Layer 3 Interface & Routing**

- **IP Addressing:**  
  Assign Point‑to‑Point (P2P) or LAN addressing between CE and PE.

- **Routing Protocol Setup:**  
  Configure the routing method for the site:  
  - **BGP** (recommended for Full IPVPN)  
  - **OSPF** (common for enterprise sites)  
  - **Static routing** (for simple or low‑change environments)

- **Redundancy:**  
  For dual‑homed sites, configure:  
  - Dual CE routers  
  - Dual PE routers  
  - Diverse access paths  

---

### **Step 4: Optional Cloud / XaaS Integration**

If the customer requires cloud connectivity:

- **Cloud Exchange Integration:**  
  Extend the IPVPN VRF to cloud on‑ramps (AWS, Azure, GCP).

- **Virtual Cross‑Connects (VXC):**  
  Provision virtual circuits from the IPVPN VRF to the cloud gateway.

- **Route Control:**  
  Apply prefix‑filters, RT‑constraints, or BGP communities to manage cloud route propagation.

---

### **Step 5: Connection & Traffic Management**

- **Traffic Policies:**  
  Apply per‑site bandwidth limits, QoS shaping, and class‑based queuing.

- **Validation:**  
  Ensure aggregate site bandwidth does not exceed the contracted IPVPN tier.

- **Security Controls:**  
  Optional features include:  
  - RTBH  
  - DDoS scrubbing  
  - Prefix‑limit enforcement  
  - BGP MD5 authentication  

---

## **3. Technical Constraints & Rules**

| Feature       | Constraint / Rule                                             |
|---------------|----------------------------------------------------------------|
| Bandwidth     | Must be ≤ contracted IPVPN tier                               |
| Routing       | Supports BGP, OSPF, static; BGP recommended for multi‑site     |
| Redundancy    | Dual‑CE or dual‑PE recommended for high availability           |
| MTU           | Standard (1500) or Jumbo (9000) depending on access method     |
| QoS           | Provider CoS mapping must match customer DSCP policy           |
| MPLS Labels   | RD/RT must be unique per VRF                                   |

---

## **4. Deployment Checklist**

- [ ] VRF name follows enterprise naming convention  
- [ ] RD and RT values are unique and registered  
- [ ] ASN (if BGP) is unique within the customer environment  
- [ ] All CE–PE IP addressing validated against IPAM  
- [ ] BGP prefix limits configured to prevent route table overflow  
- [ ] QoS policy mapped and validated  
- [ ] Redundancy tested (if dual‑homed)  
- [ ] Cloud routes filtered and validated (if applicable)  
