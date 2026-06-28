-- SELECT
--     -- LAG (Parent) Details (Pulled from v_ports LP, representing the LAG interface)
    
--     -- lag_device: The name of the device hosting the LAG interface (e.g., 'SDR1.DEN1').
--     LP.devicename AS lag_device,
    
--     -- lag_interface: The name of the Link Aggregation Group (LAG) interface (e.g., 'ae0', 'bundle-ether1').
--     L.port_a AS lag_interface,
    
--     -- lag_configured_speed: The total configured bandwidth/speed of the LAG interface (e.g., '800G').
--     LP.port_speed AS lag_configured_speed,
    
--     -- lag_interface_status: The operational status of the LAG interface itself (e.g., 'Configured', 'Up').
--     LP.service_status AS lag_interface_status,

--     -- Member (Child) Details (Pulled from v_link_summary L and v_ports MP, representing the physical port)
    
--     -- member_port_name: The name of the physical port that is a member of the LAG (e.g., 'gig-2/1/0').
--     L.port_b AS member_port_name,
    
--     -- member_port_speed: The configured speed of the individual physical member port (e.g., '400G').
--     MP.port_speed AS member_port_speed,
    
--     -- member_port_status: The operational status of the individual physical member port (e.g., 'Configured', 'Active').
--     MP.service_status AS member_port_status,
    
--     -- member_optic: The type of transceiver/optic installed in the physical member port (e.g., '400G - LR4').
--     MP.port_optic AS member_optic
-- FROM
--     v_link_summary L
-- -- Join 1: Get LAG interface details (Parent)
-- INNER JOIN
--     v_ports LP
--         ON L.device_a_id = LP.device_id
--         AND L.port_a = LP.port_name
-- -- Join 2: Get Member port details (Child)
-- INNER JOIN
--     v_ports MP
--         ON L.device_b_id = MP.device_id
--         AND L.port_b = MP.port_name
-- WHERE
--     -- Filter for internal LAG membership links (LAG -> Member port on the same device)
--     L.type = 'LAG'
--     -- Ensure link is within the same device (LAG -> Member)
--     AND L.device_a_id = L.device_b_id
-- ORDER BY
--     LP.devicename, L.port_a, L.port_b;

-- select devicename,port_name,service_status,fabric_port_type  from v_ports 
-- where devicename='VAR1.DEN1';
-- -- ORDER BY port_name;

-- SELECT 
--     port_name, 
--     -- The next line is the one causing the 'column "port_type" does not exist' error:
--     port_service_status,
--     fabric_port_type
-- FROM ports 
-- WHERE service_id IS NULL
-- ORDER BY port_name;

SELECT 
    device_name,
    port_name, 
    port_service_status,
    fabric_port_type,
    port_speed
FROM ports 
join devices d on ports.device_id=d.device_id
WHERE service_id IS NOT NULL
  and d.device_name='VAR1.DEN1'
ORDER BY port_name;
