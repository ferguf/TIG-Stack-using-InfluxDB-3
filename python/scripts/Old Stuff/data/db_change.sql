-- -- DROP TABLE IF EXISTS fabric_connection CASCADE;

-- -- CREATE TABLE fabric_connection (
-- --     connection_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
-- --     connection_name VARCHAR(100) UNIQUE NOT NULL,
-- --     connection_status VARCHAR(100) UNIQUE NOT NULL,
-- --     service_id      UUID NOT NULL REFERENCES fabric_service(service_id) ON DELETE CASCADE,
-- --     interface_id    UUID NOT NULL REFERENCES interfaces(interface_id) ON DELETE CASCADE,
-- --     port_a_id       UUID NOT NULL REFERENCES ports(port_id) ON DELETE CASCADE,
-- --     port_b_id       UUID NOT NULL REFERENCES ports(port_id) ON DELETE CASCADE,
-- --     vrf_name        VARCHAR(50),
-- --     service_bw      INTEGER,                -- bandwidth in Mbps/Gbps
-- --     s_vlan          INTEGER,                -- service VLAN
-- --     c_vlan_list     VARCHAR(100),           -- customer VLAN list
-- --     health_status   INTEGER,                -- 1=Green, 2=Amber, 3=Red, 4=Unknown
-- --     created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
-- --     updated_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
-- -- );
-- -- CREATE INDEX idx_fabric_connection_service_id ON fabric_connection(service_id);
-- -- CREATE INDEX idx_fabric_connection_interface_id ON fabric_connection(interface_id);

-- -- ALTER TABLE fabric_services
-- -- ADD COLUMN updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP;

-- -- ALTER TABLE fabric_connection
-- -- RENAME TO fabric_connections;

-- -- ALTER TABLE fabric_connections
-- -- DROP CONSTRAINT fabric_connection_interface_id_fkey;
-- -- ALTER TABLE fabric_connections
-- -- ALTER COLUMN interface_id DROP NOT NULL;


-- -- ALTER TABLE devices
-- -- RENAME COLUMN device_description TO description;
-- DROP VIEW IF EXISTS v_fabric_connections CASCADE;

-- CREATE OR REPLACE VIEW v_fabric_connections AS
-- SELECT 
--     c.customer_id,
--     c.customer_name,
--     fs.service_id,
--     fs.service_name,
--     fs.service_type,
--     d.device_id,
--     d.device_name,
--     d.location,
--     d.device_role,
--     p.port_id,
--     p.port_name,
--     p.port_type,
--     p.port_service_status,
--     fc.connection_id,
--     fc.connection_name,
--     fc.connection_status,
--     fc.vrf_name,
--     fc.service_bw,
--     fc.s_vlan,
--     fc.c_vlan_list,
--     fc.health_status
-- FROM customers c
-- JOIN fabric_services fs
--     ON c.customer_id = fs.customer_id
-- LEFT JOIN ports p
--     ON fs.service_id = p.service_id
-- LEFT JOIN devices d
--     ON p.device_id = d.device_id
-- LEFT JOIN fabric_connections fc
--     ON fs.service_id = fc.service_id
--    AND (p.port_id = fc.port_a_id OR p.port_id = fc.port_b_id);

-- CREATE OR REPLACE VIEW v_ports AS
-- SELECT 
--     d.device_id,
--     d.device_name,
--     d.location,
--     d.device_role,
--     d.device_model,
--     d.device_vendor,
--     d.serial_number,
--     d.availability_zone,
--     d.lifecycle_status,
--     d.planning_status,
--     d.health_status AS device_health,
--     p.port_id,
--     p.port_name,
--     p.port_type,
--     p.,
--     p.created_at AS port_created_at,
--     p.updated_at AS port_updated_at
-- FROM devices d
-- JOIN ports p
--     ON d.device_id = p.device_id;

--- Count port  per deviece and port type:
    SELECT 
    device_name,
    port_type,
    COUNT(port_id) AS port_count
FROM v_ports
GROUP BY device_id, device_name, port_type
ORDER BY device_name, port_type;

--- Count connections per service:
SELECT 
    customer_name,
    service_name,
    COUNT(DISTINCT connection_id) AS connection_count,
    COUNT(DISTINCT port_id) AS port_count
FROM v_fabric_connections
GROUP BY customer_name, service_name
ORDER BY customer_name, service_name;


--- List all ports and their devices for a given service:
SELECT customer_name, service_name, device_name, port_name, connection_name, connection_status
FROM v_fabric_connections
ORDER BY Customer_name;
