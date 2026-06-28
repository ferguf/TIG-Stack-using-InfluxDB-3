## Route Target Database Schema

This document describes the design and usage of the route_targets table in PostgreSQL. It is intended as a technical reference for engineers and onboarding teams who need to understand how route targets are stored, validated, and managed.

## Purpose

The route_targets table provides a reproducible schema for storing route target values associated with services. Each route target is unique and follows the format:

network:1XXXXXX

This ensures consistency across networks and metro encodings while maintaining cross‑reference capability with service records.

## Table Definition

CREATE TABLE public.route_targets (
    route_target_id   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    service_id        uuid NOT NULL,   -- FK to services table
    network_name      varchar(100) NOT NULL,  -- ASN (e.g. 3356, 209) or metro label (e.g. 'Metro Denver')
    network_base      integer NOT NULL,       -- Numeric base (e.g. 3356, 8001, 209)
    route_target      varchar(20) NOT NULL UNIQUE, -- "network:1XXXXXX"
    created_at        timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_service FOREIGN KEY (service_id) REFERENCES services(service_id)
);

## Key Points

UUID Primary Key: route_target_id ensures global uniqueness.

Service Reference: service_id links each route target to a service.

Network Name: Can be numeric ASN (3356, 209) or descriptive metro label ('Metro Denver').

Network Base: Always numeric, used for encoding (e.g. 8001).

Route Target: Unique string in the form network:1XXXXXX.

Audit Fields: created_at and updated_at track lifecycle changes.

## Example Inserts

INSERT INTO public.route_targets (
    service_id, network_name, network_base, route_target
) VALUES
    ('c0a80101-1234-5678-9abc-def012345678', '3356', 3356, '3356:1000001'),
    ('c0a80101-1234-5678-9abc-def012345679', 'Metro Denver', 8001, '8001:1000001'),
    ('c0a80101-1234-5678-9abc-def012345679', '209', 209, '209:1000001');

Best Practices

Always enforce unique route target values.

Use UUIDs for service references to avoid collisions.

Store human‑readable labels in network_name for clarity, while keeping network_base numeric.

Consider adding a CHECK constraint with regex on route_target to enforce the network:1XXXXXX format.

## Future Enhancements

Add indexing on service_id for faster lookups.

Extend schema with description or region fields for richer metadata.

Implement triggers to auto‑update updated_at on modification.

This schema ensures reproducibility, clarity, and onboarding‑friendly documentation for managing route targets across services and networks.