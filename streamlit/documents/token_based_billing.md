# Token-Based Billing Model

## Overview

Token-based billing is a usage-based model. The customer gets access to the full line-rate speed of each fabric port, from 1G to 400G, and buys a shared pool of usage tokens measured in GB.

Tokens are not tied to one port. They are applied across the customer’s eligible network services and ports.

For example, if a customer has ten 1G fabric ports, the customer does not need ten token packages. The customer buys one token package, and usage across all eligible ports consumes that shared pool.

---

## Best Fit

Token-based billing is best for:

- API-first digital services
- Cloud access
- Content traffic
- AI data movement
- IPVPN
- VOD
- MCGW
- Bursty workloads
- Customers that want usage-based network billing

---

## Token-Based Billing Characteristics

| Item | Behavior |
|---|---|
| Port speed | Customer gets line-rate access, from 1G to 400G |
| Usage pool | Shared across eligible ports |
| Service scope | Can apply to IOD, IPVPN, VOD, or MCGW |
| Traffic counted | Ingress plus egress |
| Traffic direction | North-south and east-west |
| Token unit | GB |
| Overage | Billed at selected token package price |
| Optional feature | Auto-upgrade to next token tier |
| Customer benefit | Usage-based service across the network |

---

## Token Scope

Tokens are customer-wide or service-wide. They are not assigned to one port.

```text
Customer Token Pool
   |
   |-- Fabric Port 1
   |-- Fabric Port 2
   |-- Fabric Port 3
   |-- Fabric Port 4
   |-- Fabric Port 5
   |-- Fabric Port 6
   |-- Fabric Port 7
   |-- Fabric Port 8
   |-- Fabric Port 9
   |-- Fabric Port 10
```

All eligible usage across these ports burns against the same token pool.

---

## Traffic Included

Token usage includes both north-south and east-west traffic.

### North-South Traffic

North-south traffic includes traffic between the customer and external destinations such as:

- Internet
- Cloud providers
- SaaS platforms
- Content platforms
- Public network services

### East-West Traffic

East-west traffic includes traffic between customer locations or network endpoints, such as:

- Site to site
- Region to region
- Data center to data center
- Cloud to cloud
- IPVPN endpoint to endpoint
- MCGW location to MCGW location
- Fabric port to fabric port

---

## Token Usage Rule

```text
Token Usage =
North-South Ingress
+ North-South Egress
+ East-West Ingress
+ East-West Egress
```

This keeps the customer model simple. The customer does not need separate token plans for ingress, egress, north-south, or east-west traffic.

---

## Telemetry-Based Token Calculation

Tokens are calculated from fabric port telemetry.

Each enabled fabric port reports:

- Bits in
- Bits out
- Time interval
- Port identifier
- Customer or service association

The platform calculates usage in 1-minute time slots.

```text
Minute Bytes =
(bits_in + bits_out) / 8
```

```text
Minute GB =
((bits_in + bits_out) / 8) / 1,000,000,000
```

If one token equals one GB, then each GB burns one token.

---

## Monthly Token Rollup

Monthly token usage is the sum of every 1-minute usage record across all eligible ports.

```text
Monthly Token Usage =
Σ ((bits_in + bits_out) / 8 / 1,000,000,000)
```

The sum includes:

- All eligible customer ports
- All 1-minute intervals
- Both ingress and egress
- North-south traffic
- East-west traffic
- Eligible service traffic

---

## Token Package Options

| Token Package | Included Usage | Example Token Price | Overage Rule |
|---|---:|---:|---|
| Small | 100K GB | $1.00 / GB | Overage billed at $1.00 / GB |
| Medium | 1M GB | $0.95 / GB | Overage billed at $0.95 / GB |
| Large | 10M GB | $0.85 / GB | Overage billed at $0.85 / GB |
| Extra Large | 100M GB | $0.75 / GB | Overage billed at $0.75 / GB |

Example prices are for illustration only.

---

## Overage Billing

If the customer exceeds the selected token package, the excess usage is billed at the token price for that package.

```text
Overage GB =
max(0, Monthly Token Usage - Included Token Package)
```

```text
Overage Charge =
Overage GB × Selected Token Price
```

---

## Example — 1M GB Package

| Item | Value |
|---|---:|
| Selected Package | 1M GB |
| Token Price | $0.95 / GB |
| Actual Usage | 1.2M GB |
| Overage | 200K GB |
| Overage Charge | $190,000 |

```text
Overage =
1.2M - 1M
= 200K GB
```

```text
Overage Charge =
200K × $0.95
= $190,000
```

---

## Optional Auto-Upgrade

Lumen can offer an auto-upgrade option. If the customer’s actual or projected usage shows that a larger token package is a better fit, the customer can be moved to the next package.

| Method | Description |
|---|---|
| Customer-approved upgrade | Lumen recommends the next package and the customer approves it. |
| Automatic upgrade | Customer opts in, and Lumen moves the customer to the next package when usage or projected usage exceeds the threshold. |

---

## Forecasting View

The billing view should show both actual and projected usage.

| Metric | Meaning |
|---|---|
| Tokens Purchased | Selected token package size |
| Tokens Used | Actual GB used so far |
| Tokens Remaining | Package size minus actual usage |
| Current Run Rate | Usage rate based on recent telemetry |
| Projected Usage | Expected usage by month end |
| Upper Band | Higher-side forecast |
| Lower Band | Lower-side forecast |
| Expected Overage | Forecasted usage above package |
| Recommended Package | Better token tier if needed |
| Auto-Upgrade Status | Enabled or disabled |

---

## Simple Positioning

Token-based billing is the right model when the customer wants full-speed network access and usage-based billing across ports, services, and traffic directions.
