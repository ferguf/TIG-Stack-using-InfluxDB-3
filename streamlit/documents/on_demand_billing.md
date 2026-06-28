# On-Demand Billing Model

## Overview

On-demand billing gives the customer more flexibility than fixed billing. The customer keeps a fabric port in place and can activate, change, or resize service bandwidth as needed.

This model works well for customers that need flexible capacity, cloud access, temporary bandwidth, or API-driven service changes.

---

## Best Fit

On-demand billing is best for:

- Network-as-a-Service
- Cloud access
- Temporary bandwidth increases
- Event-based capacity
- Customer-controlled service changes
- API-first service activation
- Flexible MCGW, IPVPN, VOD, or IOD services

---

## On-Demand Billing Characteristics

| Item | Behavior |
|---|---|
| Port speed | Fixed physical or logical port |
| Bandwidth | Can change by service tier |
| Usage metering | Useful for reporting and policy |
| NRC | Often reduced or waived |
| MRC | Changes based on active service state |
| Customer benefit | Flexible bandwidth |
| Best use case | NaaS, cloud access, temporary capacity |

---

## Billing Components

| Component | Description |
|---|---|
| Fabric Port NRC | One-time port activation charge. May be zero. |
| Fabric Port MRC | Monthly charge for the port. |
| Access NRC | One-time access charge. May be zero depending on offer. |
| Access MRC | Monthly access charge. |
| Service NRC | One-time setup charge. Often zero for digital offers. |
| Service Base MRC | Monthly charge to keep the service available. |
| Active Bandwidth Tier MRC | Monthly charge for the bandwidth currently activated. |

---

## On-Demand Billing Formula

```text
Monthly Bill =
Fabric Port MRC
+ Access MRC
+ Service Base MRC
+ Active Bandwidth Tier MRC
```

```text
One-Time Bill =
Fabric Port NRC
+ Access NRC
+ Service NRC
```

---

## Example

| Component | Example |
|---|---:|
| Billing Model | On-Demand |
| Fabric Port | 100G |
| Fabric Port NRC | $0 |
| Fabric Port MRC | $5,000 |
| Service | MCGW |
| Service NRC | $0 |
| Service Base MRC | $1,000 |
| Active Bandwidth Tier | 10G |
| Bandwidth Tier MRC | $4,000 |
| Monthly Bill | $10,000 |
| One-Time Bill | $0 |

```text
Monthly Bill =
$5,000 + $1,000 + $4,000
= $10,000
```

---

## Customer Experience

The customer keeps a larger fabric port available, but only activates the service bandwidth they need. This gives the customer more control over cost and capacity.

For example, a customer may have a 100G port but only activate 10G of MCGW service during normal operations. If more capacity is needed, the customer can move to a higher active bandwidth tier.

---

## Simple Positioning

On-demand billing is the right model when the customer wants a flexible network service that can change as business needs change.
