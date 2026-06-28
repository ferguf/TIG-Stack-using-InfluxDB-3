-- File Name: 'customer_setup.sql' and version '1.0.53' date: 'November 29, 2025 2:20 PM MST' (Comprehensive schema update including connections, IP addressing, static routing, BGP peering, and updated core tables.)

-- --- 0. Initial Cleanup ---

-- Drop new tables (must drop tables referencing others first)
DROP TABLE IF EXISTS bgp_neighbor_status_history CASCADE;
DROP TABLE IF EXISTS bgp_neighbor CASCADE;
DROP TABLE IF EXISTS static_routes CASCADE;
DROP TABLE IF EXISTS ipv6_interface CASCADE;
DROP TABLE IF EXISTS ipv4_interface CASCADE;
DROP TABLE IF EXISTS fabric_connection CASCADE;
DROP TABLE IF EXISTS route_target CASCADE;

-- Drop core tables
DROP TABLE IF EXISTS port_status CASCADE;
DROP TABLE IF EXISTS ports CASCADE;
DROP TABLE IF EXISTS devices CASCADE;
DROP TABLE IF EXISTS fabric_service CASCADE;
DROP TABLE IF EXISTS customer CASCADE;

-- Drop custom types, sequences, and extensions
DROP TYPE IF EXISTS port_op_status_enum CASCADE;
DROP TYPE IF EXISTS port_admin_status_enum CASCADE;
DROP TYPE IF EXISTS multihop_enum CASCADE;
DROP SEQUENCE IF EXISTS port_status_status_id_seq CASCADE;
DROP SEQUENCE IF EXISTS route_target_rt_id_seq CASCADE;

-- Drop trigger functions
DROP FUNCTION IF EXISTS set_updated_at CASCADE;
DROP FUNCTION IF EXISTS set_port_status_updated_at CASCADE;
DROP FUNCTION IF EXISTS init_port_status_on_planned CASCADE;
DROP FUNCTION IF EXISTS auto_assign_route_target CASCADE;
DROP FUNCTION IF EXISTS set_fabric_connection_updated_at CASCADE;
DROP FUNCTION IF EXISTS set_interface_ip_updated_at CASCADE;
DROP FUNCTION IF EXISTS set_static_routes_updated_at CASCADE;
DROP FUNCTION IF EXISTS set_bgp_neighbor_updated_at CASCADE;

-- Required for UUID generation functions like uuid_generate_v4()
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- --- 1. Custom Types ---

CREATE TYPE port_op_status_enum AS ENUM ('Up', 'Down', 'Unknown');
CREATE TYPE port_admin_status_enum AS ENUM ('Enabled', 'Disabled', 'Unknown');
CREATE TYPE multihop_enum AS ENUM ('yes', 'no');


-- --- 2. Core Tables ---

-- Customer Table
CREATE TABLE customer (
 customer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 customer_name VARCHAR(100) NOT NULL,
 account_id VARCHAR(50) UNIQUE NOT NULL, -- Publicly exposed ID
 created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
); 

-- Fabric Service Table (Updated with health_status)
CREATE TABLE fabric_service (
 service_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 customer_id UUID NOT NULL REFERENCES customer(customer_id) ON DELETE CASCADE,
 service_name VARCHAR(100) UNIQUE NOT NULL, -- Service identifier
 service_alias VARCHAR(100) NOT NULL,
 service_type VARCHAR(50) NOT NULL, -- e.g., E-LAN, E-Line
 service_description TEXT,
 route_target VARCHAR(100), -- Route target for VPN/service policies
 health_status INTEGER, -- e.g., 1 - Green, 2 Amber, 3 - Red, 4 unknown
 created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Devices Table (Updated)
CREATE TABLE devices (
 device_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 device_name VARCHAR(100) UNIQUE NOT NULL, 
 location VARCHAR(100) NOT NULL, -- Short Name or 8 CLLI Code
 device_role VARCHAR(50) NOT NULL, 
 device_model VARCHAR(100),
 device_vendor VARCHAR(100) NOT NULL, -- Device manufacturer
 serial_number VARCHAR(100) UNIQUE, -- Unique serial number
 availability_zone VARCHAR(100), -- Availability Zone 
 lifecycle_status VARCHAR(50) DEFAULT 'Active', -- Lifecycle status
 planning_status VARCHAR(50) DEFAULT 'Planned', -- Planning status
 health_status INTEGER, -- e.g., 1 - Green, 2 Amber, 3 - Red, 4 unknown
 device_description TEXT,
 created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Ports Table 
CREATE TABLE ports (
 port_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 mac_address VARCHAR(17), -- e.g., 00:1A:2B:3C:4D:5
 port_name VARCHAR(50) NOT NULL, -- e.g., ae0, gig-1/0/1
 port_speed VARCHAR(50) NOT NULL, -- e.g., 100G, 400G
 device_id UUID NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
 port_description VARCHAR(255),
 port_optic VARCHAR(100), -- e.g., 100G - LR4, 400G - FR4
 port_tagging VARCHAR(100), -- e.g., Untagged, Tagged
 port_cktid VARCHAR(100), -- e.g., Circuit ID associated with the port
 service_id UUID REFERENCES fabric_service(service_id) ON DELETE SET NULL, -- NULL means unassigned
 port_service_status VARCHAR(50) NOT NULL, -- e.g., Available, Configured, Assigned, Planned, Reserved,
 port_type VARCHAR(50) NOT NULL, -- e.g., Physical, LAG, Member-LAG, Fabric Port, UNI, ENNI 
 port_health_status INTEGER, -- e.g., 1 - Green, 2 Amber, 3 - Red, 4 unknown
 created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
 
 -- Port name must be unique per device
 UNIQUE (device_id, port_name)
);

-- Port Status Table 
CREATE SEQUENCE port_status_status_id_seq;

CREATE TABLE port_status (
 status_id BIGINT NOT NULL DEFAULT nextval('port_status_status_id_seq'::regclass),
 port_id UUID NOT NULL,
 operational_status port_op_status_enum NOT NULL,
 admin_status port_admin_status_enum NOT NULL,
 created_at TIMESTAMPTZ DEFAULT NOW(),
 updated_at TIMESTAMPTZ DEFAULT NOW(),
 status_change_at TIMESTAMPTZ,
 CONSTRAINT port_status_pkey PRIMARY KEY (status_id),
 CONSTRAINT fk_status_port FOREIGN KEY (port_id)
 REFERENCES ports(port_id) ON DELETE CASCADE
);
CREATE INDEX idx_port_status_port_id ON port_status(port_id);

-- Route Target Table 
CREATE TABLE route_target (
 rt_id BIGSERIAL PRIMARY KEY,
 network_id INTEGER NOT NULL, 
 target_value VARCHAR(50) UNIQUE, -- Auto-generated by trigger if NULL
 service_id UUID REFERENCES fabric_service(service_id) ON DELETE CASCADE,
 assigned_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);


-- --- 3. Configuration Tables ---

-- Fabric Connection Table
CREATE TABLE fabric_connection (
 connection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 connection_name VARCHAR(100) UNIQUE NOT NULL,
 service_id UUID NOT NULL REFERENCES fabric_service(service_id) ON DELETE CASCADE,
 vrf_name VARCHAR(50),
 service_bw INTEGER,
 s_vlan INTEGER,
 c_vlan_list VARCHAR(100),
 health_status INTEGER,
 created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- IPv4 Address Table 
CREATE TABLE ipv4_interface (
 ipaddress_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 port_id UUID NOT NULL REFERENCES ports(port_id) ON DELETE CASCADE, -- Links to ports
 bring_your_own_ip BOOLEAN DEFAULT FALSE,
 lumen_ipaddress INET,
 customer_ipaddress INET,
 network_mask VARCHAR(4) NOT NULL,
 primary_address BOOLEAN DEFAULT TRUE,
 created_at TIMESTAMPTZ DEFAULT NOW(),
 updated_at TIMESTAMPTZ DEFAULT NOW(),
 CONSTRAINT chk_ipv4_network_mask CHECK (network_mask IN ('/30','/29','/28','/27'))
);

-- IPv6 Address Table 
CREATE TABLE ipv6_interface (
 ipaddress_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 port_id UUID NOT NULL REFERENCES ports(port_id) ON DELETE CASCADE, -- Links to ports
 bring_your_own_ip BOOLEAN DEFAULT FALSE,
 lumen_ipaddress INET,
 customer_ipaddress INET,
 network_mask VARCHAR(4) NOT NULL CHECK (network_mask = '/64'),
 nexthop INET,
 metric INTEGER,
 primary_address BOOLEAN DEFAULT TRUE,
 created_at TIMESTAMPTZ DEFAULT NOW(),
 updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Static Routes Table
CREATE TABLE static_routes (
 route_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 device_id UUID REFERENCES devices(device_id) ON DELETE SET NULL,
 connection_id UUID REFERENCES fabric_connection(connection_id) ON DELETE CASCADE,
 service_id UUID REFERENCES fabric_service(service_id) ON DELETE CASCADE,
 destination CIDR NOT NULL,
 next_hop INET NOT NULL,
 route_status VARCHAR(20) NOT NULL DEFAULT 'active',
 created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- BGP Neighbor Table
CREATE TABLE bgp_neighbor (
 bgp_neighbor_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
 service_provider_as INTEGER NOT NULL DEFAULT 1,
 customer_as INTEGER NOT NULL,
 customer_neighbor_ip_address INET NOT NULL,
 service_provider_neighbor_ip_address INET NOT NULL,
 input_filter_list VARCHAR(100),
 output_filter_list VARCHAR(100),
 multihop multihop_enum NOT NULL DEFAULT 'no',
 service_id UUID REFERENCES fabric_service(service_id) ON DELETE SET NULL,
 port_id UUID REFERENCES ports(port_id) ON DELETE SET NULL,
 password_key VARCHAR(50),
 password_secret TEXT,
 created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- BGP Neighbor Status History Table
CREATE TABLE bgp_neighbor_status_history (
 status_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
 bgp_neighbor_id UUID NOT NULL REFERENCES bgp_neighbor(bgp_neighbor_id) ON DELETE CASCADE,
 old_status VARCHAR(20),
 new_status VARCHAR(20) NOT NULL,
 changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
 change_reason TEXT
);


-- --- 4. Trigger Functions and Triggers ---

-- Generic Function for updating 'updated_at' (used by devices and ports)
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
 NEW.updated_at = NOW();
 RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers using set_updated_at
CREATE TRIGGER trg_devices_updated_at
BEFORE UPDATE ON devices
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_ports_updated_at
BEFORE UPDATE ON ports
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();


-- Port Status Functions & Triggers (Specific logic)
CREATE OR REPLACE FUNCTION set_port_status_updated_at()
RETURNS TRIGGER AS $$
BEGIN
 NEW.updated_at = NOW();
 RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_port_status_updated_at
BEFORE UPDATE ON port_status
FOR EACH ROW
EXECUTE FUNCTION set_port_status_updated_at();

CREATE OR REPLACE FUNCTION init_port_status_on_planned()
RETURNS TRIGGER AS $$
BEGIN
 IF NEW.port_service_status = 'Planned' THEN
 INSERT INTO port_status (
 port_id,
 operational_status,
 admin_status,
 status_change_at
 )
 VALUES (
 NEW.port_id,
 'Unknown',
 'Unknown',
 NOW()
 );
 END IF;
 RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_init_port_status_on_planned
AFTER INSERT ON ports
FOR EACH ROW
EXECUTE FUNCTION init_port_status_on_planned();


-- Route Target Function & Trigger (Specific logic)
CREATE OR REPLACE FUNCTION auto_assign_route_target()
RETURNS TRIGGER AS $$
DECLARE
 suffix TEXT;
BEGIN
 -- Generate suffix based on rt_id sequence (ensures uniqueness)
 suffix := LPAD(NEXTVAL('route_target_rt_id_seq')::TEXT, 6, '0');

 -- If target_value not provided, auto-generate it
 IF NEW.target_value IS NULL OR NEW.target_value = '' THEN
 NEW.target_value := NEW.network_id || ':1' || suffix;
 END IF;

 RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_auto_assign_route_target
BEFORE INSERT ON route_target
FOR EACH ROW
EXECUTE FUNCTION auto_assign_route_target();


-- Fabric Connection Functions & Triggers
CREATE OR REPLACE FUNCTION set_fabric_connection_updated_at()
RETURNS TRIGGER AS $$
BEGIN
 NEW.updated_at = NOW();
 RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_fabric_connection_updated_at
BEFORE UPDATE ON fabric_connection
FOR EACH ROW
EXECUTE FUNCTION set_fabric_connection_updated_at();


-- IPv4/IPv6 Interface Address Functions & Triggers
CREATE OR REPLACE FUNCTION set_interface_ip_updated_at()
RETURNS TRIGGER AS $$
BEGIN
 NEW.updated_at = NOW();
 RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- IPv4 table trigger
CREATE TRIGGER trg_ipv4_interface_updated_at
BEFORE UPDATE ON ipv4_interface
FOR EACH ROW
EXECUTE FUNCTION set_interface_ip_updated_at();

-- IPv6 table trigger
CREATE TRIGGER trg_ipv6_interface_updated_at
BEFORE UPDATE ON ipv6_interface
FOR EACH ROW
EXECUTE FUNCTION set_interface_ip_updated_at();


-- Static Routes Functions & Triggers
CREATE OR REPLACE FUNCTION set_static_routes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
 NEW.updated_at = NOW();
 RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_static_routes_updated_at
BEFORE UPDATE ON static_routes
FOR EACH ROW
EXECUTE FUNCTION set_static_routes_updated_at();


-- BGP Neighbor Functions & Triggers
CREATE OR REPLACE FUNCTION set_bgp_neighbor_updated_at()
RETURNS TRIGGER AS $$
BEGIN
 NEW.updated_at = NOW();
 RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_bgp_neighbor_updated_at
BEFORE UPDATE ON bgp_neighbor
FOR EACH ROW
EXECUTE FUNCTION set_bgp_neighbor_updated_at();