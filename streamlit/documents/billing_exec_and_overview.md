# Billing Models and Tokenization — Executive Overview

## Executive Summary

Network services need more than one billing model. Some customers want a fixed monthly price. Some want flexible bandwidth that can change as needed. Others want full-speed access to the network and a usage-based model that works across many ports and services.

This billing design supports three models:

1. **Fixed Billing** — the customer pays known one-time and monthly charges.
2. **On-Demand Billing** — the customer pays for the fabric port and activates or changes bandwidth as needed.
3. **Token-Based Billing** — the customer gets line-rate access to fabric ports and buys a shared usage pool measured in GB.

The goal is to use one simple billing structure that supports different commercial choices. The customer can use the same network platform, but select the billing model that best fits how they consume the service.

---

## Billing Models at a Glance

| Billing Model | Simple Meaning | Best Fit |
|---|---|---|
| Fixed | Customer pays set NRC and MRC charges. | Traditional enterprise services and predictable billing. |
| On-Demand | Customer keeps a port and changes service bandwidth when needed. | NaaS, cloud access, temporary bandwidth, API-driven service changes. |
| Token-Based | Customer gets line-rate port access and buys a shared GB usage pool. | Cloud, content, AI data movement, IPVPN, MCGW, and bursty workloads. |

---

## Core Billing Components

Each billing model uses the same major billing parts.

| Component | Description |
|---|---|
| Rate Card | Defines pricing that applies to a customer, provider, or service. |
| Billing Model | Defines whether the service is Fixed, On-Demand, or Token-Based. |
| Fabric Port | Customer attachment point, such as 1G, 10G, 100G, or 400G. |
| Access | ONNET, OFFNET, provider, or location-based access charge. |
| Service | IOD, IPVPN, VOD, MCGW, or another network service. |
| Bandwidth Tier | Service bandwidth charge, mainly used for Fixed and On-Demand models. |
| Token Package | Included GB, token price, and token monthly charge. |
| Usage Record | Measured usage for billing and reporting. |

---

## Fabric Port and Service Billing

A customer may be charged for both the fabric port and the service.

### Fabric Port Charges

| Charge | Description | Example Range |
|---|---|---:|
| Fabric Port NRC | One-time activation or install charge. | $0–$10,000 |
| Fabric Port MRC | Monthly charge for the port. | $0–$10,000 |

### Service Charges

| Charge | Description | Example Range |
|---|---|---:|
| Service NRC | One-time setup charge for IOD, IPVPN, VOD, or MCGW. | $0–$10,000 |
| Service MRC | Monthly charge for the network service. | $0–$10,000 |

The NRC or MRC can be zero if product or finance chooses to bundle the charge into another part of the offer.

---

## Simple Billing Formulas

### Fixed Billing

```text
Monthly Bill =
Fabric Port MRC
+ Access MRC
+ Service MRC
+ Bandwidth Tier MRC
```

```text
One-Time Bill =
Fabric Port NRC
+ Access NRC
+ Service NRC
```

### On-Demand Billing

```text
Monthly Bill =
Fabric Port MRC
+ Access MRC
+ Service Base MRC
+ Active Bandwidth Tier MRC
```

### Token-Based Billing

```text
Monthly Bill =
Fabric Port MRC
+ Access MRC
+ Token Package MRC
+ Overage Charge
```

```text
Overage Charge =
Max(0, Monthly Token Usage - Included Token Package)
× Selected Token Price
```

---

## Side-by-Side Comparison

| Item | Fixed | On-Demand | Token-Based |
|---|---|---|---|
| Port Access | Fixed port | Fixed port | Line-rate port access |
| Bandwidth | Fixed | Flexible | Not tied to fixed bandwidth |
| Usage Pool | No | Usually no | Yes |
| Traffic Counted | Not normally usage billed | Optional | Ingress + egress |
| Applies Across Ports | No | Sometimes | Yes |
| Overage | Usually not used | Usually not used | Billed at selected token price |
| Forecasting | Not required | Helpful | Required |
| Best For | Predictable billing | Flexible service changes | Usage-based digital services |

---

## Recommended Position

Lumen should support Fixed, On-Demand, and Token-Based billing on the same network platform.

- **Fixed** gives predictable billing.
- **On-Demand** gives service flexibility.
- **Token-Based** gives usage-based billing across ports, services, and traffic directions.

This supports both traditional enterprise services and newer digital services such as cloud, content, AI data movement, IPVPN, VOD, and MCGW.
