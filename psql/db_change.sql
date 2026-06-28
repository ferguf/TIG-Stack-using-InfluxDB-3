CREATE OR REPLACE VIEW vw_capabilities_location AS
WITH deployed_profiles AS (
    -- Get all unique hardware profiles deployed at each location
    SELECT DISTINCT 
        d.location_id, 
        hp.profile_id,
        hp.device_role,
        hp.device_model
    FROM devices d
    JOIN capabilities_hardware_profiles hp 
        ON d.device_role = hp.device_role 
        AND d.device_model = hp.device_model
    WHERE d.location_id IS NOT NULL
),
location_hardware AS (
    -- Aggregate the deployed hardware array per location
    SELECT 
        location_id,
        ARRAY_AGG(DISTINCT device_role || ' ' || device_model) AS deployed_hardware
    FROM deployed_profiles
    GROUP BY location_id
),
location_ports AS (
    -- Aggregate all unique port speeds across those deployed profiles
    SELECT 
        dp.location_id,
        JSON_AGG(DISTINCT crs.speed_value) AS supported_ports
    FROM deployed_profiles dp
    JOIN capabilities_profile_ports cpp ON dp.profile_id = cpp.profile_id
    JOIN capabilities_ref_speeds crs ON cpp.speed_id = crs.speed_id
    GROUP BY dp.location_id
),
location_services AS (
    -- Aggregate all unique services across those deployed profiles
    SELECT 
        dp.location_id,
        JSON_AGG(DISTINCT crf.service_name) AS supported_services
    FROM deployed_profiles dp
    JOIN capabilities_profile_services cps ON dp.profile_id = cps.profile_id
    JOIN capabilities_ref_services crf ON cps.service_id = crf.service_id
    GROUP BY dp.location_id
)
-- Final Output Assembly
-- No GROUP BY required because all CTEs are already aggregated exactly 1-to-1 per location_id
SELECT 
    lh.location_id,
    lh.deployed_hardware,
    COALESCE(lp.supported_ports, '[]'::json) AS location_supported_ports,
    COALESCE(ls.supported_services, '[]'::json) AS location_supported_services
FROM location_hardware lh
LEFT JOIN location_ports lp ON lh.location_id = lp.location_id
LEFT JOIN location_services ls ON lh.location_id = ls.location_id;