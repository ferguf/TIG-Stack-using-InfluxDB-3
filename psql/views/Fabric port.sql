CREATE OR REPLACE VIEW v_assigned_ports AS
SELECT 
    d.device_name,
    p.port_name,
    p.port_service_status,
    p.port_type
FROM ports p
JOIN devices d 
    ON p.device_id = d.device_id
WHERE p.port_service_status = 'Assigned'
  AND p.port_type = 'Fabric Port';

CREATE OR REPLACE VIEW v_available_ports AS
SELECT 
    d.device_name,
    p.port_name,
    p.port_service_status,
    p.port_type
FROM ports p
JOIN devices d 
    ON p.device_id = d.device_id
WHERE p.port_service_status IN ('Available', 'Ready for use')
  AND p.port_type = 'Physical';


SELECT 
    d.device_name,
    p.port_name,
    p.port_service_status,
    p.port_type
from v_assigned_ports p
JOIN devices d
    ON p.device_name = d.device_name
WHERE d.device_role = 'VAR';

SELECT 
    d.device_name,
    p.port_name,
    p.port_service_status,
    p.port_type
from v_available_ports p
JOIN devices d
    ON p.device_name = d.device_name
WHERE d.device_role = 'VAR';