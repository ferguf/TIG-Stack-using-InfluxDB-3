
-- \i /tmp/adhoc/db.sql # Initial database schema -    
-- C:\Users\fergu\TIG-Stack-using-InfluxDB-3>
-- docker compose exec postgres psql -U myuser -d mydatabase

-- CREATE TABLE gwinfo (
--     clli VARCHAR(12) NOT NULL,
--     shortname VARCHAR(20)  NOT NULL,
--     longname VARCHAR(50)  NOT NULL,    
--     street VARCHAR(250)  NOT NULL,    
--     note text,
--     city text,
--     region text,
--     zip text,
--     country text,
--     timezone text,
--     timezone_offset text,
--     latitude text,
--     longitude text,
--     Continent text,
--     create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- -- DROP TABLE gwinfo;


-- CREATE TABLE routedb (
--     service_rd VARCHAR(20) NOT NULL,
--     router_prefix VARCHAR(20) NOT NULL,
--     router_name VARCHAR(20) NOT NULL,
--     router_interface VARCHAR(20) NOT NULL,
--     interface_ip VARCHAR(20) NOT NULL,
--     nexthop_ip VARCHAR(20) NOT NULL,
--     route_type VARCHAR(20) NOT NULL,
--     route_as text,
--     route_state text,
--     route_lp text,
--     route_med text,
--     route_path text,
--     cktid VARCHAR(20) NOT NULL,
--     create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
--     updated_at TIMESTAMP 
-- );

-- INSERT INTO routedb (service_rd,router_prefix,router_name,router_interface,interface_ip,nexthop_ip,route_type,route_as,route_state,route_lp,route_med,route_path,cktid) VALUES
-- ('65000:100','10.23.0.0/24','var1.den1','G-0/1/0.333','192.168.1.9','192.168.1.10','bgp','65000','active','100','200','1 2 3','CKT12346');

-- CREATE TABLE routers (
--     router_id SERIAL PRIMARY KEY, -- Added a simple primary key for the router itself
--     gw_shortname VARCHAR(20) NOT NULL,
--     router_name VARCHAR(20) NOT NULL,
--     router_role VARCHAR(20) NOT NULL,
--     router_vendor VARCHAR(20) NOT NULL,
--     router_model VARCHAR(20) NOT NULL,
--     create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- INSERT INTO routers (gw_shortname,router_name,router_role,router_vendor,router_model) VALUES
-- ('den1','var1.den1','var','juniper','mx480'),
-- ('alb1','var1.alb1','var','juniper','mx10004'),
-- ('chi1','var1.chi1','var','juniper','mx480'),
-- ('nyc1','var1.nyc1','var','juniper','mx10004'),
-- ('sf1','var1.sf1','var','juniper','mx480'),
-- ('sea1','var1.sea1','var','juniper','mx480'),
-- ('atl1','var1.atl1','var','juniper','mx10004'),
-- ('bos1','var1.bos1','var','juniper','mx960'),
-- ('den1','var2.den1','var','juniper','mx480'),
-- ('alb1','var2.alb1','var','juniper','mx10004'),
-- ('chi1','var2.chi1','var','juniper','mx480'),
-- ('nyc1','var2.nyc1','var','juniper','mx10004'),
-- ('sf1','var2.sf1','var','juniper','mx480'),
-- ('sea1','var2.sea1','var','juniper','mx480'),
-- ('atl1','var2.atl1','var','juniper','mx10004'),
-- ('bos1','var2.bos1','var','juniper','mx960')
-- ;

-- CREATE TABLE interfaces (
--     interface_id SERIAL PRIMARY KEY, -- Added a simple primary key for the router itself
--     router_name VARCHAR(20) NOT NULL,
--     interface_name VARCHAR(20) NOT NULL,
--     Interface_ip VARCHAR(20) NOT NULL,
--     interface_type VARCHAR(20) NOT NULL,
--     interface_speed VARCHAR(20) NOT NULL,
--     interface_vlan VARCHAR(20) NOT NULL,
--     interface_bw VARCHAR(20) NOT NULL,
--     interface_status VARCHAR(20) NOT NULL,
--     cktid VARCHAR(20) NOT NULL,
--     fabric_service VARCHAR(20) NOT NULL,
--     create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );

-- INSERT INTO interfaces (router_name,interface_name,Interface_ip,interface_type,interface_speed,interface_vlan,interface_bw,interface_status,cktid,fabric_service) VALUES
-- ('var1.den1','G-0/1/0.333','192.168.1.1','Metro Direct','100G','333/100','1000','active','CKT12346','Fabric-1212'),
-- ('var1.den1','G-0/1/0.334','192.168.1.5','Metro Direct','100G','334/100','5000','active','CKT12347','Fabric-1213'),
-- ('var1.alb1','G-0/1/0.333','192.168.3.1','Metro Direct','100G','333/100','10000','active','CKT12348','Fabric-1214'),
-- ('var1.alb1','G-0/1/1.0','192.168.5.1','port','100G','334/100','500','active','CKT12349','Fabric-1215'),
-- ('var2.den1','G-0/1/0.333','192.168.10.1','Metro Direct','100G','333/100','1000','active','CKT12350','Fabric-1212'),
-- ('var2.den1','G-0/1/2.0','192.168.10.5','port','100G','334/100','1000','active','CKT12351','Fabric-1213'),
-- ('var2.alb1','G-0/1/0.333','192.170.1.1','Metro Direct','100G','333/100','1000','active','CKT12352','Fabric-1214'),
-- ('var2.alb1','G-0/1/1.0','182.170.1.5','port','100G','334/100','200','active','CKT12353','Fabric-1215'),
-- ('var1.chi1','G-0/1/1.0','192.180.1.1','port','100G','334/100','2000','active','CKT12354','Fabric-1212'),
-- ('var1.chi1','G-0/1/2.0','192.180.1.5','port','100G','334/100','1000','active','CKT12355','Fabric-1213'),
-- ('var2.chi1','G-0/1/0.333','192.180.1.9','Metro Direct','100G','333/100','200','active','CKT12356','Fabric-1214'), 
-- ('var2.chi1','G-0/1/1.0','192.180.1.13','port','100G','334/100','500','active','CKT12357','Fabric-1215')

-- CREATE TABLE services (
--     instance_id SERIAL PRIMARY KEY, -- Added a simple primary key for the router itself
--     instance_rt VARCHAR(20) NOT NULL,
--     instance_name VARCHAR(20) NOT NULL,
--     instance_alias VARCHAR(20) NOT NULL,
--     cktid VARCHAR(20) NOT NULL,
--     fabric_service VARCHAR(20) NOT NULL,
--     create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
-- );
-- ALTER TABLE services
-- ALTER COLUMN instance_name TYPE VARCHAR(200),
-- ALTER COLUMN instance_alias TYPE VARCHAR(200);


-- INSERT INTO services (instance_rt,instance_name,instance_alias,cktid,fabric_service) VALUES
-- ('65000:100','Service-1','Denver Warehouse','CKT12346','Fabric-1212'),
-- ('65000:100','Service-1','Chicago','CKT12350','Fabric-1212'),
-- ('65000:100','Service-1','Denver HQ','CKT12358','Fabric-1212'),
-- ('65000:200','Service-2','Albany Data Center','CKT12348','Fabric-1214'),
-- ('65000:200','Service-2','Albany Office','CKT12352','Fabric-1214'),
-- ('65000:200','Service-2','Chicago Office','CKT12356','Fabric-1214'),
-- ('65000:300','Service-3','New York Data Center','CKT12360','Fabric-1216'),
-- ('65000:300','Service-3','New York Office','CKT12362','Fabric-1216'),
-- ('65000:400','Service-4','San Francisco Data Center','CKT12364','Fabric-1218'),
-- ('65000:400','Service-4','San Francisco Office','CKT12366','Fabric-1218'),
-- ('65000:500','Service-5','Seattle Data Center','CKT12368','Fabric-1220'),
-- ('65000:500','Service-5','Seattle Office','CKT12370','Fabric-1220'),
-- ('65000:600','Service-6','Atlanta Data Center','CKT12372','Fabric-1222'),
-- ('65000:600','Service-6','Atlanta Office','CKT12374','Fabric-1222'),
-- ('65000:700','Service-7','Boston Data Center','CKT12376','Fabric-1224'),
-- ('65000:700','Service-7','Boston Office','CKT12378','Fabric-1224')
-- ;




-- ALTER TABLE Routers
-- RENAME COLUMN router_shortname TO gw_shortname;

-- ALTER TABLE gwinfo
-- ADD CONSTRAINT uq_gwinfo_shortname UNIQUE (shortname);

-- ALTER TABLE gwinfo ADD COLUMN country TIMESTAMP;

-- DROP TABLE gwinfo;

-- INSERT INTO USERS (username, email,lastlogin) VALUES 
-- ('jane', 'jane@gmail.com',CURRENTTIMESTAMP),
-- ('john', 'john@gmail.com',CURRENTTIMESTAMP),
-- ('jon', 'jon@gmail.com',CURRENTTIMESTAMP)
-- ;

-- UPDATE USERS SET lastlogin = CURRENTTIMESTAMP WHERE username = 'alice1';
-- DELETE FROM gwinfo WHERE clli = 'ALBYNYYC';
-- DELETE FROM USERS WHERE id = 1;

-- INSERT INTO gwinfo (clii,shortname,longname,street,note,city,region,zip,country,timezone,timezone_offset,latitude,longitude) 
-- VALUES
--  ('ALBYNYYC','alb3','Albany3','194 WASHINGTON AVE',' ','ALBANY','NEW YORK','12210','US','EASTERN TIME','-5','42.656502','-73.763')
--  ;



-- SELECT clli FROM gwinfo;

-- SELECT * FROM POSTS;

--  SELECT instance_name,instance_rt,instance_alias,interfaces.router_name,interfaces.interface_name,interfaces.interface_ip FROM services INNER JOIN interfaces
--  on interfaces.fabric_service = services.fabric_service;

-- CREATE VIEW PostDetails AS
--     SELECT title,content,username 
--     FROM POSTS INNER JOIN USERS
--     on POSTS.userid = USERS.id;

-- SELECT * FROM gwpop;

-- CREATE TABLE devices (
--     deviceId UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--     deviceName VARCHAR(50) NOT NULL UNIQUE,
--     gw_shortname VARCHAR(50) NOT NULL,
--     deviceRole VARCHAR(10) NOT NULL,
--     deviceType VARCHAR(255),
--     availabilityZone VARCHAR(255),
--     lifeCycleStatus VARCHAR(20) NOT NULL,
--     serviceStatus VARCHAR(20) NOT NULL,

--     -- Constraints for ENUM-like fields
--     CONSTRAINT chk_lifecycle_status CHECK (lifeCycleStatus IN ('Growth', 'Cap Growth', 'Cap provisioning', 'Remove')),
--     CONSTRAINT chk_service_status CHECK (serviceStatus IN ('Planned', 'Active', 'Capped'))
-- );


-- CREATE TABLE fabric_service (
--     service_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--     service_name VARCHAR(100) NOT NULL UNIQUE,
--     service_alias VARCHAR(100) NOT NULL UNIQUE,
--     service_description TEXT,
--     service_type service_type_enum NOT NULL, -- Restricted to the defined types   
--     -- Additional metadata
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
-- );

-- CREATE TYPE port_speed_enum AS ENUM (
--     '1G', '10G', '100G', '400G', 'Auto Negotiate (1G)'
-- );

-- CREATE TYPE port_optic_enum AS ENUM (
--     '1G - Copper', '1G - LR/LX', '10G - LR', '100G - LR4', '100G - CWDM4', '400G - LR4', '400G - FR4', 'unknown'
-- );

-- CREATE TYPE port_op_status_enum AS ENUM (
--     'up', 'down'
-- );

-- CREATE TYPE port_admin_status_enum AS ENUM (
--     'up', 'down'
-- );

-- CREATE TYPE port_service_status_enum AS ENUM (
--     'Active', 'Planned', 'Ready for Use', 'Do not Use', 'Reserved', 'Available', 'Capped'
-- );

-- CREATE TYPE port_tagging_enum AS ENUM (
--     'All-2-1 bundled', 'Tagged', 'Untagged', 'Not Configured'
-- );

-- CREATE TYPE fabric_port_type_enum AS ENUM (
--     'Fabric Port', 'Cloud Fabric port', 'ENNI Fabric port', 'port', 'UNI', 'Wholesale UNI', 'SAT Test Port'
-- );


-- CREATE TABLE fabric_port (
--     -- Unique Identifier
--     port_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

--     -- Basic Identification
--     port_name VARCHAR(100) NOT NULL UNIQUE,
--     customer_alias VARCHAR(255),
--     mac_address VARCHAR(17), -- Standard MAC format length
    
--     -- Configuration Details
--     port_speed port_speed_enum NOT NULL,
--     port_optic port_optic_enum,
--     fabric_port_type fabric_port_type_enum NOT NULL,
--     port_tagging port_tagging_enum NOT NULL DEFAULT 'Not Configured',

--     -- Capacity and Utilization (Stored as numeric for calculations, not strings like '200G')
--     max_fabric_services INTEGER,
--     fabric_services_count INTEGER,
    
--     -- Bandwidth capacities. Storing these as TEXT or BIGINT (for Mbps/Kbps) is typical. 
--     -- I will use BIGINT assuming the bandwidth is stored in Mbps/Kbps to allow calculation.
--     -- If '200G' is strictly a display value, use TEXT. Sticking to TEXT based on your examples.
--     used_services_bandwidth TEXT,
--     reserved_services_bandwidth TEXT,
--     available_services_bandwidth TEXT,
--     max_services_bandwidth TEXT,
    
--     -- Service Status
--     service_status port_service_status_enum NOT NULL DEFAULT 'Available'

--     -- Note: Foreign Keys for 'cloudPartner', 'serviceCapabilities', and 'portCapabilities' 
--     -- would require separate tables (like the nested port_status below).
-- );

-- CREATE TABLE port_status (
--     status_id BIGSERIAL PRIMARY KEY,
    
--     -- Foreign Key to the parent port
--     port_id UUID NOT NULL,
--     CONSTRAINT fk_status_port
--         FOREIGN KEY (port_id)
--         REFERENCES fabric_port (port_id)
--         ON DELETE CASCADE,

--     -- Status Details
--     operational_status port_op_status_enum NOT NULL,
--     admin_status port_admin_status_enum NOT NULL,
    
--     -- Timestamps (Using TIMESTAMP WITH TIME ZONE for robust storage)
--     created_at TIMESTAMP WITH TIME ZONE,
--     updated_at TIMESTAMP WITH TIME ZONE,
--     status_change_at TIMESTAMP WITH TIME ZONE

-- );

-- CREATE TABLE connection_port_link (
--     link_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
--     -- Foreign Key to the Connection
--     connection_id UUID NOT NULL,
--     CONSTRAINT fk_link_connection
--         FOREIGN KEY (connection_id)
--         REFERENCES fabric_connection (connection_id)
--         ON DELETE CASCADE,

--     -- Foreign Key to the Port
--     port_id UUID NOT NULL,
--     CONSTRAINT fk_link_port
--         FOREIGN KEY (port_id)
--         REFERENCES fabric_port (port_id)
--         ON DELETE RESTRICT,
        
--     -- Ensure a connection and port pair is only linked once
--     UNIQUE (connection_id, port_id)
-- );

-- CREATE TABLE fabric_connection (
--     connection_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--     connection_name VARCHAR(100) NOT NULL UNIQUE,
    
--     -- Foreign Key linking to Fabric Service (a connection MUST belong to a service)
--     service_id UUID NOT NULL,
--     CONSTRAINT fk_connection_service
--         FOREIGN KEY (service_id)
--         REFERENCES fabric_service (service_id)
--         ON DELETE CASCADE, -- If service is deleted, delete the connections
        
--     -- Additional fields for VRF/location (optional, based on your IPVPN/MCGW rules)
--     vrf_name VARCHAR(50), 
    
--     -- Additional metadata
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
-- );

-- CREATE VIEW gwpop AS
--     SELECT CLLI,shortname , Latitude ,Longitude 
--     FROM gwinfo; 
--     

-- SELECT enumlabel
-- FROM pg_enum
-- WHERE enumtypid = (
--     SELECT oid FROM pg_type WHERE typname = 'fabric_port_optic_enum'
-- );

-- SELECT
--     t.typname AS enum_type_name,
--     e.enumlabel AS allowed_value
-- FROM
--     pg_type t
-- JOIN
--     pg_enum e ON t.oid = e.enumtypid
-- JOIN
--     pg_namespace n ON t.typnamespace = n.oid
-- WHERE
--     n.nspname = 'public' -- Restrict to the 'public' schema
-- ORDER BY
--     enum_type_name, e.enumsortorder;


-- CREATE VIEW v_fabric_c AS
-- SELECT
--     -- Service Fields
--     fs.service_id,
--     fs.service_name,
--     fs.service_type,
--     fs.service_description
    
--     -- Connection Fields
--     fc.connection_id,
--     fc.connection_name,
--     fc.vrf_name,
--     fc.service_bw,
--     fc.s_vlan,
--     fc.c_vlan_list
-- FROM
--     fabric_service fs
-- LEFT JOIN
--     fabric_connection fc ON fs.service_id = fc.service_id;

-- CREATE VIEW v_service_ports AS
-- SELECT
--     fs.service_id,
--     fs.service_name,
--     fs.service_type,
--     fp.port_id,
--     fp.port_name,
--     fp.port_speed,
--     fp.fabric_port_type
-- FROM
--     fabric_service fs
-- LEFT JOIN
--     fabric_port fp ON fs.service_id = fp.service_id;

--  SELECT * FROM v_service_ports;

--  SELECT
--     service_type,
--     COUNT(service_id) AS service_count
-- FROM
--     fabric_service
-- GROUP BY
--     service_type
-- ORDER BY
--     service_count DESC;

-- SELECT
--     fabric_port_type,
--     COUNT(port_id)
-- FROM
--     fabric_port
-- GROUP BY
--     fabric_port_type;



-- SELECT
--     COUNT(connection_id)
-- FROM
--     fabric_connection

-- CREATE TABLE customer (
--     -- Primary Key (UUID for unique identification)
--  customer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
--     -- Customer Name
--     customer_name VARCHAR(255) NOT NULL,
    
--     -- Account Identifier
--     account_id VARCHAR(50) UNIQUE NOT NULL,
    
--     -- Metadata
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
-- );


-- ALTER TABLE fabric_service
-- ADD COLUMN customer_id UUID,
-- ADD CONSTRAINT fk_service_customer
--     FOREIGN KEY (customer_id)
--     REFERENCES customer (customer_id)
--     ON DELETE SET NULL;

-- INSERT INTO customer ( customer_name, account_id)
-- VALUES 
--     ('Innovate Solutions Inc.', 'IS-500'),
--     ('Quantum Dynamics LLC', 'QD-600'),
--     ('SecureGlobe Telecom', 'SG-700'),
--     ('NorthStar Data Corp', 'ND-800');

-- select * from customer;

-- UPDATE fabric_service
-- SET customer_id = CASE service_id
--     -- Assign Services to Innovate Solutions Inc. (89edfc42-...)
--     WHEN '243b5b0e-28f5-4198-b883-57562b9f7bd8' THEN '89edfc42-4d12-4639-9e29-7c04b33c52cc' -- EVPL Service 001
--     WHEN '0b68537f-0296-4823-af0d-7340c746d147' THEN '89edfc42-4d12-4639-9e29-7c04b33c52cc' -- EPL Service 001
    
--     -- Assign Services to Quantum Dynamics LLC (e41e679b-...)
--     WHEN 'ad4e788a-4ada-449a-b92d-87e25d6a5870' THEN 'e41e679b-50b5-4992-818b-ded1e112c7c6' -- EVPL Service 002
--     WHEN '0b562f26-d6d2-445f-8df4-ca58fcf2c339' THEN 'e41e679b-50b5-4992-818b-ded1e112c7c6' -- EVPL Service 004
    
--     -- Assign Services to SecureGlobe Telecom (17e613cb-...)
--     WHEN '90fe89ae-2d35-46a4-84ce-99c9fc17116b' THEN '17e613cb-7ddb-4494-9a47-a85eda06d759' -- MCGW Service 004
--     WHEN '0fba9304-0efa-4138-84cd-e9066c99ccec' THEN '17e613cb-7ddb-4494-9a47-a85eda06d759' -- IPVPN Service 001
    
--     -- Assign Service to NorthStar Data Corp (3b37fff7-...)
--     WHEN 'f854c34a-2abc-4df8-9fdd-1726a868e088' THEN '3b37fff7-3b1c-4a16-b237-ad45165dd9ff' -- Cloud Connection Service 001
    
--     -- Default action: keep the existing customer_id for any other service
--     ELSE customer_id 
-- END
-- -- Filter to only run the CASE logic on the services listed above
-- WHERE service_id IN (
--     '243b5b0e-28f5-4198-b883-57562b9f7bd8', '0b68537f-0296-4823-af0d-7340c746d147',
--     'ad4e788a-4ada-449a-b92d-87e25d6a5870', '0b562f26-d6d2-445f-8df4-ca58fcf2c339',
--     '90fe89ae-2d35-46a4-84ce-99c9fc17116b', '0fba9304-0efa-4138-84cd-e9066c99ccec',
--     'f854c34a-2abc-4df8-9fdd-1726a868e088'
-- )
-- RETURNING service_name, customer_id;

-- CREATE VIEW v_customer_service_map AS
-- SELECT
--     -- Customer Fields (Parent)
--     c.customer_id,
--     c.customer_name,
--     c.account_id,
    
--     -- Fabric Service Fields (Child)
--     fs.service_id,
--     fs.service_name,
--     fs.service_type,
--     fs.created_at AS service_creation_date
-- FROM
--     customer c
-- LEFT JOIN
--     fabric_service fs ON c.customer_id = fs.customer_id
-- ORDER BY
--     c.customer_name, fs.service_name;

-- CREATE VIEW v_service_topology AS
-- SELECT
--     Customer Fields
--     c.customer_id,
--     c.customer_name,
--     c.account_id,
    
--     Service Fields (fs.route_target added here)
--     fs.service_id,
--     fs.service_name,
--     fs.service_type,
--     fs.service_alias,
--     fs.service_description,
--     fs.route_target, -- <--- NEW COLUMN ADDED
    
--     Connection Fields
--     fc.connection_id,
--     fc.connection_name,
--     fc.service_bw,
--     fc.s_vlan,
--     fc.c_vlan_list,
    
--     Port Fields
--     fp.port_id,
--     fp.port_name,
--     fp.port_speed,
--     fp.port_tagging,
--     fp.fabric_port_type
-- FROM
--     customer c
-- 1. Link Customer to Service
-- LEFT JOIN
--     fabric_service fs ON c.customer_id = fs.customer_id
-- 2. Link Service to Connection
-- LEFT JOIN
--     fabric_connection fc ON fs.service_id = fc.service_id
-- 3. Link Service to Port Details (Note: Your original script used fs.service_id for this join)
-- LEFT JOIN
--     fabric_port fp ON fs.service_id = fp.service_id
-- ORDER BY
--     c.customer_name, fs.service_name, fc.connection_name, fp.port_name;

-- CREATE VIEW v_Customer_service AS
-- SELECT
--     Customer Fields
--     c.customer_id,
--     c.customer_name,
--     c.account_id,
    
--     Service Fields (fs.route_target added here)
--     fs.service_id,
--     fs.service_name,
--     fs.service_type,
--     fs.service_alias,
--     fs.service_description,
--     fs.route_target -- <--- NEW COLUMN ADDED
    
-- FROM
--     customer c
-- 1. Link Customer to Service
-- LEFT JOIN
--     fabric_service fs ON c.customer_id = fs.customer_id
-- ORDER BY
--     c.customer_name, fs.service_name;

-- CREATE VIEW v_customer_port AS
-- SELECT
--     -- Customer Fields
--     c.customer_id,
--     c.customer_name,
--     c.account_id,

--     -- Service Fields
--     fs.service_id,
--     fs.service_name,
--     fs.service_type,
    
--     -- Port Fields
--     fp.port_id,
--     fp.port_name,
--     fp.port_speed,
--     fp.port_optic,
--     fp.port_tagging,
--     fp.service_status,
--     fp.fabric_port_type

-- FROM
--     customer c
-- -- 1. Link Customer to Service (1:M)
-- LEFT JOIN
--     fabric_service fs ON c.customer_id = fs.customer_id
-- -- 2. Link Service to Port (1:M)
-- LEFT JOIN
--     fabric_port fp ON fs.service_id = fp.service_id
-- ORDER BY
--     c.customer_name, fs.service_name, fp.port_name;

-- ALTER TABLE devices
-- DROP COLUMN model,
-- DROP COLUMN vendor,
-- ADD COLUMN devicemodel VARCHAR(100),
-- ADD COLUMN devicevendor VARCHAR(100);


-- INSERT INTO devices (
--     deviceid,
--     devicename,
--     devicemodel,
--     devicevendor,
--     deviceRole,
--     gw_shortname,
--     availabilityzone,
--     lifeCyclestatus,
--     health,
--     servicestatus
-- )
-- VALUES (
--     gen_random_uuid(),         -- Generates a unique ID
--     'SDR1.DEN1',               -- The unique device name
--     'Juniper',                 -- Device vendor: VPN Aggregation Router
--     'MX10004',                 -- Device molde :  Router model
--     'SDR',                     -- Device Role: VPN Aggregation Router
--     'den1',                    -- The short gateway name
--     'Zone 0',                  -- Placeholder for Availability Zone
--     'Growth',                  -- Lifecycle Status
--     1,                         -- Health Status (1 = Green, 2 = Amber , 3 = Red)  
--     'Active'                   -- Service Status
-- ),
-- (
--     gen_random_uuid(),         -- Generates a unique ID
--     'SDR2.DEN1',               -- The unique device name
--     'Juniper',                 -- Device vendor: VPN Aggregation Router
--     'MX10004',                   -- Device molde :  Router model
--     'SDR',                     -- Device Role: VPN Aggregation Router
--     'den1',                    -- The short gateway name
--     'Zone 0',                  -- Placeholder for Availability Zone
--     'Growth',                  -- Lifecycle Status
--     2,                         -- Health Status (1 = Green, 2 = Amber , 3 = Red)  
--     'Active'                   -- Service Status
-- ),
-- (
--     gen_random_uuid(),         -- Generates a unique ID
--     'VAR3.DEN1',               -- The unique device name
--     'Juniper',                 -- Device vendor: VPN Aggregation Router
--     'MX960',                 -- Device molde :  Router model
--     'VAR',                     -- Device Role: VPN Aggregation Router
--     'den1',                    -- The short gateway name
--     'Zone 0',                  -- Placeholder for Availability Zone 0 = default , Zone 1 = primary, Zone 2 = secondary
--     'Growth',                  -- Lifecycle Status
--     1,                         -- Health Status (1 = Green, 2 = Amber , 3 = Red)  
--     'Active'                   -- Service Status
-- ),
-- (
--     gen_random_uuid(),         -- Generates a unique ID
--     'SDR1.ALB1',               -- The unique device name
--     'Juniper',                 -- Device vendor: VPN Aggregation Router
--     'MX10004',                   -- Device molde :  Router model
--     'SDR',                     -- Device Role: VPN Aggregation Router
--     'alb1',                    -- The short gateway name
--     'Zone 0',                  -- Placeholder for Availability Zone
--     'Growth',                  -- Lifecycle Status
--     1,                         -- Health Status (1 = Green, 2 = Amber , 3 = Red)  
--     'Active'                   -- Service Status
-- ),(
--     gen_random_uuid(),         -- Generates a unique ID
--     'SDR2.ALB1',               -- The unique device name
--     'Juniper',                 -- Device vendor: VPN Aggregation Router
--     'MX10004',                   -- Device molde :  Router model
--     'SDR',                     -- Device Role: VPN Aggregation Router
--     'alb1',                    -- The short gateway name
--     'Zone 0',                  -- Placeholder for Availability Zone
--     'Growth',                  -- Lifecycle Status
--     1,                         -- Health Status (1 = Green, 2 = Amber , 3 = Red)  
--     'Active'                   -- Service Status
-- ),
-- (
--     gen_random_uuid(),         -- Generates a unique ID
--     'VAR3.CHI1',               -- The unique device name
--     'Juniper',                 -- Device vendor: VPN Aggregation Router
--     'MX480',                   -- Device molde :  Router model
--     'VAR',                     -- Device Role: VPN Aggregation Router
--     'chi1',                    -- The short gateway name
--     'Zone 0',                  -- Placeholder for Availability Zone
--     'Growth',                  -- Lifecycle Status
--     1,                         -- Health Status (1 = Green, 2 = Amber , 3 = Red)  
--     'Active'                   -- Service Status
-- ),
-- (
--     gen_random_uuid(),         -- Generates a unique ID
--     'SDR1.CHI1',               -- The unique device name
--     'Juniper',                 -- Device vendor: VPN Aggregation Router
--     'MX480',                   -- Device molde :  Router model
--     'SDR',                     -- Device Role: VPN Aggregation Router
--     'chi1',                    -- The short gateway name
--     'Zone 0',                  -- Placeholder for Availability Zone
--     'Growth',                  -- Lifecycle Status
--     1,                         -- Health Status (1 = Green, 2 = Amber , 3 = Red)  
--     'Active'                   -- Service Status
-- ),
-- (
--     gen_random_uuid(),         -- Generates a unique ID
--     'SDR2.CHI1',               -- The unique device name
--     'Juniper',                 -- Device vendor: VPN Aggregation Router
--     'MX480',                   -- Device molde :  Router model
--     'SDR',                     -- Device Role: VPN Aggregation Router
--     'chi1',                    -- The short gateway name
--     'Zone 0',                  -- Placeholder for Availability Zone
--     'Growth',                  -- Lifecycle Status
--     1,                         -- Health Status (1 = Green, 2 = Amber , 3 = Red)  
--     'Active'                   -- Service Status
-- ) ,
-- (
--     gen_random_uuid(),         -- Generates a unique ID
--     'SDR1.NYC1',               -- The unique device name
--     'Juniper',                 -- Device vendor: VPN Aggregation Router
--     'MX10004',                 -- Device molde :  Router model
--     'SDR',                     -- Device Role: VPN Aggregation Router
--     'nyc1',                    -- The short gateway name
--     'Zone 0',                  -- Placeholder for Availability Zone
--     'Growth',                  -- Lifecycle Status
--     1,                         -- Health Status (1 = Green, 2 = Amber , 3 = Red)  
--     'Active'                   -- Service Status
-- )  ,
-- (
--     gen_random_uuid(),         -- Generates a unique ID
--     'ESP3.NYC1',               -- The unique device name
--     'Nokia',                 -- Device vendor: VPN Aggregation Router
--     '7750=SR12',                 -- Device molde :  Router model
--     'ESP',                     -- Device Role: VPN Aggregation Router
--     'nyc1',                    -- The short gateway name
--     'Zone 0',                  -- Placeholder for Availability Zone
--     'Growth',                  -- Lifecycle Status
--     1,                         -- Health Status (1 = Green, 2 = Amber , 3 = Red)  
--     'Active'                   -- Service Status
-- )   ,
-- (
--     gen_random_uuid(),         -- Generates a unique ID
--     'SDR1.SFO1',               -- The unique device name
--     'Juniper',                 -- Device vendor: VPN Aggregation Router
--     'MX480',                 -- Device molde :  Router model
--     'SDR',                     -- Device Role: VPN Aggregation Router
--     'sfo1',                    -- The short gateway name
--     'Zone 0',                  -- Placeholder for Availability Zone
--     'Growth',                  -- Lifecycle Status
--     3,                         -- Health Status (1 = Green, 2 = Amber , 3 = Red)  
--     'Active'                   -- Service Status
-- ),
-- (
--     gen_random_uuid(),         -- Generates a unique ID
--     'SDR2.SFO1',               -- The unique device name
--     'Juniper',                 -- Device vendor: VPN Aggregation Router
--     'MX480',                 -- Device molde :  Router model
--     'SDR',                     -- Device Role: VPN Aggregation Router
--     'sfo1',                    -- The short gateway name
--     'Zone 0',                  -- Placeholder for Availability Zone
--     'Growth',                  -- Lifecycle Status
--     3,                         -- Health Status (1 = Green, 2 = Amber , 3 = Red)  
--     'Active'                   -- Service Status
-- );

--  d7a3f1c0-9134-4a84-bce5-0346eab44f27 | VAR1.DEN1
--  1a3276f2-70f6-4698-a37e-a4fee2cfd673 | VAR2.DEN1
--  abcbfb3c-4b7c-4d64-aeff-c1ffaf231aec | VAR1.ALB1
--  b3191867-8ce7-4376-9f5b-d3e30dd2f2aa | VAR2.ALB1
--  3ad60f84-2f1e-4559-bcc1-15e151ea22c6 | VAR1.CHI1
--  34542fc9-840d-400c-9db6-dc816413aff7 | VAR2.CHI1
--  426b504b-37e9-443d-a117-47037c603e6a | VAR1.NYC1
--  dfc32a18-7303-4c49-b80d-4ea0cc874e42 | VAR2.NYC1
--  8a83d57f-0163-49f9-8e3c-2dc4054eb4ec | VAR1.SFO1
--  4da4eebe-6a28-4f49-8581-b17778ac45a6 | SDR1.DEN1
--  9a6d3f2c-4823-40d3-82f0-93ea9de6862e | SDR2.DEN1
--  69c7dbe8-d69c-4af2-a9f0-1120677f17db | VAR3.DEN1
--  10ef5517-4a04-4edd-bd98-5d7decd1f31b | SDR1.ALB1
--  303bfd7c-a585-402d-bf70-84e944c7e86b | SDR2.ALB1
--  b78f4f62-ef64-4459-90cc-b6ecd4f6461c | VAR3.CHI1
--  c9334db8-29f6-4e71-971b-caac18cb2d4b | SDR1.CHI1
--  ae089f37-4b00-4ea9-b3ba-792f89785a14 | SDR2.CHI1
--  66224338-6458-42b0-9cf3-dc0fbb64a6d1 | SDR1.NYC1
--  5381009f-6527-4adc-aa08-3467ff7a9871 | ESP3.NYC1
--  5d8c54b1-e1e8-4ee2-af24-c80e071c9569 | SDR1.SFO1
--  85d85608-e2ac-4345-bd62-67f264470562 | SDR2.SFO1


-- CREATE OR REPLACE VIEW v_ports AS
-- SELECT
--     fp.port_id,
--     fp.port_name,
--     fp.port_speed,
--     fp.port_optic,
--     fp.fabric_port_type,
--     fp.service_status,
--     fp.device_id,
--     d.deviceName,
--     d.deviceRole,
--     d.devicemodel,
--     d.devicevendor,
--     d.gw_shortname
-- FROM
--     ports fp
-- JOIN
--     devices d ON fp.device_id = d.deviceId
-- ORDER BY
--     d.deviceName, fp.port_name;

select devicename,port_name,port_id from v_ports where deviceName='SDR1.DEN1';

-- SELECT
--     deviceName,
--     port_name,
--     port_id
-- FROM
--     v_ports vp
-- WHERE
--     deviceName = 'VAR2.DEN1'
--     AND EXISTS (
--         SELECT 1
--         FROM port_links pl
--         WHERE pl.port_a_id = vp.port_id OR pl.port_b_id = vp.port_id
--     );

-- SELECT
--     d.deviceName,  
--     d.gw_shortname,
--     COUNT(fp.port_id) AS total_port_count
-- FROM
--     devices d
-- LEFT JOIN -- LEFT JOIN ensures devices with zero ports are still listed
--     fabric_port fp ON d.deviceId = fp.device_id
-- GROUP BY
--     d.deviceName
-- ORDER BY
--     total_port_count DESC, d.deviceName;

-- SELECT
--     d.deviceid,
--     d.deviceName,
--     d.gw_shortname,
--     COUNT(fp.port_id) AS total_port_count
-- FROM
--     devices d
-- LEFT JOIN -- LEFT JOIN ensures devices with zero ports are still listed
--     fabric_port fp ON d.deviceId = fp.device_id
-- GROUP BY
--     d.gw_shortname, d.deviceName, d.deviceid
-- ORDER BY
--     total_port_count DESC, d.gw_shortname, d.deviceName;
