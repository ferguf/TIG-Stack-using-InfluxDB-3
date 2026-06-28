# Fixed Billing Model

## Overview

Fixed billing is the simplest billing model. The customer buys a known port, service, and bandwidth level. The price is predictable because the customer pays fixed one-time and monthly charges.

This model works well when the customer wants a stable bill and does not need frequent bandwidth changes.

---

## Best Fit

Fixed billing is best for:

- Traditional enterprise services
- Committed IOD
- Fixed MCGW services
- Fixed IPVPN services
- Private connectivity
- Customers that want predictable monthly billing

---

## Fixed Billing Characteristics

| Item | Behavior |
|---|---|
| Port speed | Fixed |
| Bandwidth | Fixed |
| Usage metering | Optional for reporting, not required for billing |
| NRC | Usually applies |
| MRC | Stable monthly charge |
| Customer benefit | Predictable bill |
| Best use case | Committed enterprise services |

---

## Billing Components

| Component | Description |
|---|---|
| Fabric Port NRC | One-time charge to activate the port. |
| Fabric Port MRC | Monthly charge for the port. |
| Access NRC | One-time access install or setup charge. |
| Access MRC | Monthly access charge. |
| Service NRC | One-time setup charge for the service. |
| Service MRC | Monthly service charge. |
| Bandwidth Tier MRC | Monthly charge for selected bandwidth, if billed separately. |

---

## Fixed Billing Formula

```text
One-Time Charges =
Fabric Port NRC
+ Access NRC
+ Service NRC
```

```text
Monthly Charges =
Fabric Port MRC
+ Access MRC
+ Service MRC
+ Bandwidth Tier MRC
```

---

## Example

| Component | Example |
|---|---:|
| Billing Model | Fixed |
| Fabric Port | 10G |
| Fabric Port NRC | $1,000 |
| Fabric Port MRC | $2,500 |
| Service | IOD |
| Service NRC | $500 |
| Service MRC | $3,000 |
| Bandwidth Tier MRC | Included |
| Monthly Bill | $5,500 |
| One-Time Bill | $1,500 |

```text
Monthly Bill =
$2,500 + $3,000
= $5,500
```

```text
One-Time Bill =
$1,000 + $500
= $1,500
```

---

## Customer Experience

With fixed billing, the customer knows the monthly cost before the service is turned up. This makes budgeting easier and keeps the invoice simple.

The tradeoff is that the customer does not get the same flexibility as on-demand or token-based billing. If the customer needs more bandwidth, the service usually needs a change order or a new pricing step.

---

## Simple Positioning

Fixed billing is the right model when the customer wants a stable, committed service with predictable monthly charges.
