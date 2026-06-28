--
-- PostgreSQL database dump
--

\restrict yrfuOibYaVec1Ah5Jogf3Mrmy8SG9TEHa8ZhjU3jWmaNtAirPefrmTVrnWPA8Eb

-- Dumped from database version 16.10
-- Dumped by pg_dump version 18.0

-- Started on 2026-03-02 11:47:08

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 2 (class 3079 OID 24585)
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- TOC entry 3774 (class 0 OID 0)
-- Dependencies: 2
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 250 (class 1259 OID 40991)
-- Name: bgp_neighbors; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.bgp_neighbors (
    bgp_neighbor_id uuid DEFAULT gen_random_uuid() NOT NULL,
    interface_id uuid,
    neighbor_ip inet NOT NULL,
    local_ip inet,
    remote_asn integer NOT NULL,
    local_asn integer,
    session_type character varying(50),
    session_state character varying(50),
    description character varying(200),
    community character varying(200),
    import_policy text[],
    export_policy text[],
    multihop integer,
    auth boolean DEFAULT false,
    auth_password character varying(200),
    bfd boolean DEFAULT false,
    bfd_interval integer DEFAULT 500,
    bfd_multiple integer DEFAULT 3,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.bgp_neighbors OWNER TO myuser;

--
-- TOC entry 256 (class 1259 OID 49199)
-- Name: cloud_connection_members; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.cloud_connection_members (
    member_id uuid DEFAULT gen_random_uuid() NOT NULL,
    cloud_connection_id uuid NOT NULL,
    interface_id uuid NOT NULL,
    role character varying(50),
    status character varying(50) DEFAULT 'Active'::character varying NOT NULL,
    notes text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT cloud_connection_members_status_check CHECK (((status)::text = ANY ((ARRAY['Active'::character varying, 'Planned'::character varying, 'Maintenance'::character varying, 'Down'::character varying])::text[])))
);


ALTER TABLE public.cloud_connection_members OWNER TO myuser;

--
-- TOC entry 255 (class 1259 OID 49183)
-- Name: cloud_connections; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.cloud_connections (
    cloud_connection_id uuid DEFAULT gen_random_uuid() NOT NULL,
    partner_id uuid NOT NULL,
    connection_name character varying(100) NOT NULL,
    service_type character varying(20) NOT NULL,
    service_status character varying(50) NOT NULL,
    region character varying(100) NOT NULL,
    service_bw integer,
    redundancy_model character varying(50),
    description text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT cloud_connections_service_status_check CHECK (((service_status)::text = ANY ((ARRAY['Active'::character varying, 'Planned'::character varying, 'Capped'::character varying])::text[])))
);


ALTER TABLE public.cloud_connections OWNER TO myuser;

--
-- TOC entry 257 (class 1259 OID 49221)
-- Name: cloud_partner_bandwidths; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.cloud_partner_bandwidths (
    partner_bw_id uuid DEFAULT gen_random_uuid() NOT NULL,
    partner_id uuid NOT NULL,
    service_bw integer NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.cloud_partner_bandwidths OWNER TO myuser;

--
-- TOC entry 254 (class 1259 OID 49168)
-- Name: cloud_partners; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.cloud_partners (
    partner_id uuid DEFAULT gen_random_uuid() NOT NULL,
    partner_key character varying(50) NOT NULL,
    partner_name character varying(100) NOT NULL,
    partner_code character varying(20) NOT NULL,
    partner_type character varying(50) NOT NULL,
    region character varying(100) NOT NULL,
    service_type character varying(20) NOT NULL,
    service_status character varying(50) NOT NULL,
    partnership_level character varying(50),
    notes text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT cloud_partners_service_status_check CHECK (((service_status)::text = ANY ((ARRAY['Active'::character varying, 'Planned'::character varying, 'Capped'::character varying])::text[])))
);


ALTER TABLE public.cloud_partners OWNER TO myuser;

--
-- TOC entry 217 (class 1259 OID 16394)
-- Name: cross_connects; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.cross_connects (
    connect_id uuid NOT NULL,
    internal_circuit_id character varying(100) NOT NULL,
    local_port_id uuid NOT NULL,
    remote_port_id uuid,
    connect_type character varying(50) NOT NULL,
    service_description character varying(255),
    loa_number character varying(100),
    mrc numeric(10,2),
    nrc numeric(10,2),
    status character varying(20) NOT NULL,
    activation_date date,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.cross_connects OWNER TO myuser;

--
-- TOC entry 220 (class 1259 OID 16421)
-- Name: customers; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.customers (
    customer_id uuid DEFAULT gen_random_uuid() NOT NULL,
    customer_name character varying(255) NOT NULL,
    account_id character varying(50),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.customers OWNER TO myuser;

--
-- TOC entry 219 (class 1259 OID 16412)
-- Name: devices; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.devices (
    device_id uuid NOT NULL,
    device_name character varying(100) NOT NULL,
    device_role character varying(50) NOT NULL,
    device_model character varying(100),
    device_vendor character varying(100) NOT NULL,
    availability_zone character varying(100),
    lifecycle_status character varying(50),
    planning_status character varying(50),
    health_status integer,
    network text,
    location text,
    floor text,
    aisle text,
    rack text,
    device_description text,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.devices OWNER TO myuser;

--
-- TOC entry 230 (class 1259 OID 16515)
-- Name: fabric_connections; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.fabric_connections (
    connection_id uuid DEFAULT gen_random_uuid() NOT NULL,
    connection_name character varying(100),
    service_id uuid NOT NULL,
    connector_a_id uuid,
    connector_b_id uuid,
    connector_a_table text,
    connector_b_table text,
    connection_status character varying(100),
    vrf_name character varying(50),
    service_bw integer,
    s_vlan integer,
    c_vlan_list character varying(100),
    health_status integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.fabric_connections OWNER TO myuser;

--
-- TOC entry 226 (class 1259 OID 16467)
-- Name: fabric_services; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.fabric_services (
    service_id uuid NOT NULL,
    customer_id uuid NOT NULL,
    service_name character varying(100),
    service_alias character varying(100),
    service_type character varying(50),
    service_description text,
    route_target character varying(50),
    health_status integer,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.fabric_services OWNER TO myuser;

--
-- TOC entry 231 (class 1259 OID 16530)
-- Name: hardware_documents; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.hardware_documents (
    document_id uuid NOT NULL,
    hardware_id uuid NOT NULL,
    document_name character varying(255) NOT NULL,
    storage_path character varying(512) NOT NULL
);


ALTER TABLE public.hardware_documents OWNER TO myuser;

--
-- TOC entry 229 (class 1259 OID 16505)
-- Name: hardware_specs; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.hardware_specs (
    hardware_id uuid NOT NULL,
    model_name character varying(100) NOT NULL,
    manufacturer character varying(100),
    power_source_id uuid NOT NULL,
    nebs_level character varying(50)
);


ALTER TABLE public.hardware_specs OWNER TO myuser;

--
-- TOC entry 221 (class 1259 OID 16426)
-- Name: interface; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.interface (
    interface_id uuid DEFAULT gen_random_uuid() NOT NULL,
    port_id uuid,
    ckt_id character varying(100),
    description text,
    interface_name character varying(100),
    interface_type character varying(50),
    svlan_id integer,
    cvlan_list character varying(100),
    dhcp_relay_enabled boolean DEFAULT true NOT NULL,
    service_bw_mbps bigint,
    status character varying(50) NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.interface OWNER TO myuser;

--
-- TOC entry 228 (class 1259 OID 16493)
-- Name: ip_interfaces; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.ip_interfaces (
    ip_address_id uuid DEFAULT gen_random_uuid() NOT NULL,
    interface_id uuid NOT NULL,
    lumen_ip_address inet NOT NULL,
    customer_ip_address inet NOT NULL,
    network_mask_cidr integer NOT NULL,
    bring_your_own_ip boolean NOT NULL,
    next_hop_address inet,
    metric integer
);


ALTER TABLE public.ip_interfaces OWNER TO myuser;

--
-- TOC entry 227 (class 1259 OID 16481)
-- Name: ipv4_interfaces; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.ipv4_interfaces (
    ipv4_address_id uuid NOT NULL,
    interface_id uuid NOT NULL,
    lumen_ip_address inet NOT NULL,
    customer_ip_address inet NOT NULL,
    network_mask_cidr integer NOT NULL,
    bring_your_own_ip boolean NOT NULL
);


ALTER TABLE public.ipv4_interfaces OWNER TO myuser;

--
-- TOC entry 218 (class 1259 OID 16405)
-- Name: location_info; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.location_info (
    location_id uuid NOT NULL,
    location_code character varying(20) NOT NULL,
    short_name character varying(50),
    location_name character varying(100) NOT NULL,
    address character varying(200),
    city character varying(100) NOT NULL,
    state character varying(100) NOT NULL,
    postal_code character varying(20),
    country character varying(50) NOT NULL,
    timezone_name character varying(50),
    timezone_offset integer,
    latitude numeric(9,6),
    longitude numeric(9,6),
    availability_zone character varying(50),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.location_info OWNER TO myuser;

--
-- TOC entry 223 (class 1259 OID 16442)
-- Name: lric_cost_model; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.lric_cost_model (
    cost_model_id uuid NOT NULL,
    base_cost numeric(15,4) NOT NULL,
    lric_fill integer,
    calculated_lric_cost numeric(15,4) GENERATED ALWAYS AS ((base_cost * ((lric_fill)::numeric / 100.0))) STORED
);


ALTER TABLE public.lric_cost_model OWNER TO myuser;

--
-- TOC entry 216 (class 1259 OID 16389)
-- Name: patch_panels; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.patch_panels (
    port_id uuid NOT NULL,
    device_id uuid,
    port_number integer,
    local_port uuid,
    remote_port uuid,
    description character varying(255),
    port_name character varying(50),
    connector_type character varying(50),
    fiber_mode character varying(50),
    status character varying(50),
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.patch_panels OWNER TO myuser;

--
-- TOC entry 225 (class 1259 OID 16455)
-- Name: ports; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.ports (
    port_id uuid DEFAULT gen_random_uuid() NOT NULL,
    mac_address character varying(17),
    port_name character varying(50) NOT NULL,
    port_speed character varying(50) NOT NULL,
    device_id uuid NOT NULL,
    port_description character varying(255),
    port_optic character varying(100),
    port_tagging character varying(100),
    port_cktid character varying(100),
    customer_id uuid,
    port_service_status character varying(50),
    port_type character varying(50) NOT NULL,
    port_health_status integer,
    lag_parent_id uuid,
    admin_status character varying(50) DEFAULT 'up'::character varying NOT NULL,
    oper_status character varying(50) DEFAULT 'down'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.ports OWNER TO myuser;

--
-- TOC entry 3775 (class 0 OID 0)
-- Dependencies: 225
-- Name: COLUMN ports.lag_parent_id; Type: COMMENT; Schema: public; Owner: myuser
--

COMMENT ON COLUMN public.ports.lag_parent_id IS 'ID of the parent LAG/Bundle for this member port';


--
-- TOC entry 222 (class 1259 OID 16437)
-- Name: power_options; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.power_options (
    power_source_id uuid NOT NULL,
    power_type character varying(50) NOT NULL,
    voltage character varying(50) NOT NULL,
    description character varying(255)
);


ALTER TABLE public.power_options OWNER TO myuser;

--
-- TOC entry 232 (class 1259 OID 16542)
-- Name: routeVision; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public."routeVision" (
    route_id uuid NOT NULL,
    fabric_service_id uuid NOT NULL,
    fabric_connection_id uuid,
    ip_prefix cidr NOT NULL,
    route_type character varying(20) NOT NULL,
    ip_next_hop character varying(200) NOT NULL,
    route_status character varying(20) DEFAULT 'Active'::character varying NOT NULL,
    bgp_asn integer,
    bgp_as_path character varying(200),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public."routeVision" OWNER TO myuser;

--
-- TOC entry 247 (class 1259 OID 24657)
-- Name: route_vision; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.route_vision (
    route_id uuid DEFAULT gen_random_uuid() NOT NULL,
    fabric_service_id uuid NOT NULL,
    fabric_connection_id uuid,
    ip_prefix inet NOT NULL,
    route_type character varying(20) NOT NULL,
    ip_next_hop character varying(200) NOT NULL,
    route_status character varying(20) DEFAULT 'Active'::character varying NOT NULL,
    route_target character varying(100),
    route_distinguisher character varying(200),
    bgp_asn integer,
    bgp_as_path character varying(200),
    bgp_community character varying(200),
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.route_vision OWNER TO myuser;

--
-- TOC entry 251 (class 1259 OID 41005)
-- Name: routing_policies; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.routing_policies (
    policy_id uuid DEFAULT gen_random_uuid() NOT NULL,
    fabric_service_id uuid,
    policy_name character varying(200) NOT NULL,
    policy_sequence integer NOT NULL,
    prefix_id uuid NOT NULL,
    prefix_id_name character varying(200) NOT NULL,
    ip_prefix inet NOT NULL,
    ip_mask inet NOT NULL,
    match character varying(50) NOT NULL,
    action character varying(50) NOT NULL,
    med text[],
    local_pref text[],
    communities text[],
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.routing_policies OWNER TO myuser;

--
-- TOC entry 249 (class 1259 OID 40981)
-- Name: static_routes; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.static_routes (
    route_id uuid DEFAULT gen_random_uuid() NOT NULL,
    interface_id uuid,
    ip_prefix inet NOT NULL,
    prefix_mask integer NOT NULL,
    next_hop_ip inet NOT NULL,
    metric integer,
    community character varying(200),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.static_routes OWNER TO myuser;

--
-- TOC entry 224 (class 1259 OID 16448)
-- Name: topology_links; Type: TABLE; Schema: public; Owner: myuser
--

CREATE TABLE public.topology_links (
    link_id uuid NOT NULL,
    endpoint_a uuid NOT NULL,
    endpoint_b uuid NOT NULL,
    link_type character varying(30) NOT NULL,
    description character varying(500),
    status text DEFAULT 'configured'::text NOT NULL
);


ALTER TABLE public.topology_links OWNER TO myuser;

--
-- TOC entry 260 (class 1259 OID 49263)
-- Name: v_cloud_partner_detail; Type: VIEW; Schema: public; Owner: myuser
--

CREATE VIEW public.v_cloud_partner_detail AS
 SELECT partner_id,
    partner_key,
    partner_name,
    partner_code,
    partner_type,
    region,
    service_type,
    service_status,
    partnership_level,
    notes,
    created_at,
    updated_at,
    ( SELECT COALESCE(jsonb_agg(cb.service_bw ORDER BY cb.service_bw), '[]'::jsonb) AS "coalesce"
           FROM public.cloud_partner_bandwidths cb
          WHERE (cb.partner_id = cp.partner_id)) AS bandwidth_tiers
   FROM public.cloud_partners cp;


ALTER VIEW public.v_cloud_partner_detail OWNER TO myuser;

--
-- TOC entry 252 (class 1259 OID 41020)
-- Name: v_customer_summary; Type: VIEW; Schema: public; Owner: myuser
--

CREATE VIEW public.v_customer_summary AS
 SELECT c.customer_id,
    c.customer_name,
    c.account_id,
    count(DISTINCT fs.service_id) AS service_count,
    count(DISTINCT fc.connection_id) AS fabric_connection_count,
    count(DISTINCT p.port_id) AS port_count,
    count(DISTINCT i.interface_id) AS interface_count
   FROM ((((public.customers c
     LEFT JOIN public.fabric_services fs ON ((c.customer_id = fs.customer_id)))
     LEFT JOIN public.fabric_connections fc ON ((fs.service_id = fc.service_id)))
     LEFT JOIN public.ports p ON ((c.customer_id = p.customer_id)))
     LEFT JOIN public.interface i ON ((p.port_id = i.port_id)))
  GROUP BY c.customer_id, c.customer_name, c.account_id;


ALTER VIEW public.v_customer_summary OWNER TO myuser;

--
-- TOC entry 253 (class 1259 OID 49157)
-- Name: v_device_port_location; Type: VIEW; Schema: public; Owner: myuser
--

CREATE VIEW public.v_device_port_location AS
 SELECT p.port_id,
    p.port_name,
    p.port_speed,
    p.port_type,
    p.port_description,
    p.port_optic,
    p.port_tagging,
    p.port_cktid,
    p.customer_id,
    p.port_service_status,
    p.port_health_status,
    p.admin_status,
    p.oper_status,
    p.created_at AS port_created_at,
    p.updated_at AS port_updated_at,
    d.device_id,
    d.device_name,
    d.device_role,
    d.device_model,
    d.device_vendor,
    d.availability_zone,
    d.lifecycle_status,
    d.planning_status,
    d.health_status AS device_health_status,
    d.network,
    d.location,
    d.floor,
    d.aisle,
    d.rack,
    d.device_description,
    d.created_at AS device_created_at,
    d.updated_at AS device_updated_at,
    l.location_id,
    l.location_code,
    l.short_name AS location_short_name,
    l.location_name,
    l.address,
    l.city,
    l.state,
    l.postal_code,
    l.country,
    l.timezone_name,
    l.timezone_offset,
    l.latitude,
    l.longitude,
    l.availability_zone AS location_availability_zone,
    l.created_at AS location_created_at,
    l.updated_at AS location_updated_at
   FROM ((public.ports p
     JOIN public.devices d ON ((p.device_id = d.device_id)))
     LEFT JOIN public.location_info l ON ((d.location = (l.short_name)::text)));


ALTER VIEW public.v_device_port_location OWNER TO myuser;

--
-- TOC entry 248 (class 1259 OID 32779)
-- Name: v_device_ports; Type: VIEW; Schema: public; Owner: myuser
--

CREATE VIEW public.v_device_ports AS
 SELECT d.device_id,
    d.device_name,
    d.health_status AS device_health_status,
    d.availability_zone,
    p.port_id,
    p.port_name,
    p.port_speed,
    p.port_type,
    p.port_service_status,
    p.port_health_status,
    p.mac_address,
    p.port_optic,
    p.port_tagging,
    p.port_cktid,
    (((d.device_name)::text || ' / '::text) || (p.port_name)::text) AS physical_structure,
    p.lag_parent_id,
    p.customer_id,
    p.created_at AS port_created_at,
    p.updated_at AS port_updated_at
   FROM (public.devices d
     JOIN public.ports p ON ((d.device_id = p.device_id)));


ALTER VIEW public.v_device_ports OWNER TO myuser;

--
-- TOC entry 258 (class 1259 OID 49251)
-- Name: v_fabric_service_detail; Type: VIEW; Schema: public; Owner: myuser
--

CREATE VIEW public.v_fabric_service_detail AS
SELECT
    NULL::uuid AS service_id,
    NULL::uuid AS customer_id,
    NULL::character varying(255) AS customer_name,
    NULL::character varying(50) AS account_id,
    NULL::character varying(100) AS service_name,
    NULL::character varying(100) AS service_alias,
    NULL::character varying(50) AS service_type,
    NULL::text AS service_description,
    NULL::character varying(50) AS route_target,
    NULL::integer AS health_status,
    NULL::timestamp with time zone AS created_at,
    NULL::timestamp with time zone AS updated_at,
    NULL::json AS fabric_connections;


ALTER VIEW public.v_fabric_service_detail OWNER TO myuser;

--
-- TOC entry 259 (class 1259 OID 49256)
-- Name: v_interface_detail; Type: VIEW; Schema: public; Owner: myuser
--

CREATE VIEW public.v_interface_detail AS
SELECT
    NULL::uuid AS interface_id,
    NULL::uuid AS port_id,
    NULL::character varying(100) AS ckt_id,
    NULL::text AS description,
    NULL::character varying(100) AS interface_name,
    NULL::character varying(50) AS interface_type,
    NULL::integer AS svlan_id,
    NULL::character varying(100) AS cvlan_list,
    NULL::boolean AS dhcp_relay_enabled,
    NULL::bigint AS service_bw_mbps,
    NULL::character varying(50) AS status,
    NULL::timestamp with time zone AS created_at,
    NULL::timestamp with time zone AS updated_at,
    NULL::jsonb AS port,
    NULL::json AS ip_addresses,
    NULL::json AS bgp_neighbors,
    NULL::json AS static_routes;


ALTER VIEW public.v_interface_detail OWNER TO myuser;

--
-- TOC entry 245 (class 1259 OID 16630)
-- Name: v_location_normalized_coords; Type: VIEW; Schema: public; Owner: myuser
--

CREATE VIEW public.v_location_normalized_coords AS
 WITH bounds AS (
         SELECT location_info.short_name,
            location_info.latitude AS lat,
            location_info.longitude AS lon,
            min(location_info.longitude) OVER () AS lon_min,
            max(location_info.longitude) OVER () AS lon_max,
            min(location_info.latitude) OVER () AS lat_min,
            max(location_info.latitude) OVER () AS lat_max
           FROM public.location_info
        )
 SELECT short_name,
    lat,
    lon,
        CASE
            WHEN (lon_max = lon_min) THEN (500)::numeric
            ELSE (((lon - lon_min) / (lon_max - lon_min)) * (1000)::numeric)
        END AS x_coord,
        CASE
            WHEN (lat_max = lat_min) THEN (500)::numeric
            ELSE (((lat - lat_min) / (lat_max - lat_min)) * (1000)::numeric)
        END AS y_coord
   FROM bounds;


ALTER VIEW public.v_location_normalized_coords OWNER TO myuser;

--
-- TOC entry 242 (class 1259 OID 16617)
-- Name: v_network_summary_master; Type: VIEW; Schema: public; Owner: myuser
--

CREATE VIEW public.v_network_summary_master AS
 WITH device_by_location AS (
         SELECT 'device_by_location'::text AS category,
            jsonb_build_object('location', devices.location) AS dimension,
            count(*) AS count_value
           FROM public.devices
          GROUP BY devices.location
        ), device_by_role AS (
         SELECT 'device_by_role'::text AS category,
            jsonb_build_object('device_role', devices.device_role) AS dimension,
            count(*) AS count_value
           FROM public.devices
          GROUP BY devices.device_role
        ), port_by_speed AS (
         SELECT 'port_by_speed'::text AS category,
            jsonb_build_object('port_speed', ports.port_speed) AS dimension,
            count(*) AS count_value
           FROM public.ports
          GROUP BY ports.port_speed
        ), port_by_type AS (
         SELECT 'port_by_type'::text AS category,
            jsonb_build_object('port_type', ports.port_type) AS dimension,
            count(*) AS count_value
           FROM public.ports
          GROUP BY ports.port_type
        ), link_by_type AS (
         SELECT 'link_by_type'::text AS category,
            jsonb_build_object('link_type', topology_links.link_type) AS dimension,
            count(*) AS count_value
           FROM public.topology_links
          GROUP BY topology_links.link_type
        ), link_by_status AS (
         SELECT 'link_by_status'::text AS category,
            jsonb_build_object('status', topology_links.status) AS dimension,
            count(*) AS count_value
           FROM public.topology_links
          GROUP BY topology_links.status
        ), customer_by_site AS (
         SELECT 'customer_by_location'::text AS category,
            jsonb_build_object('location', d.location) AS dimension,
            count(DISTINCT c.customer_id) AS count_value
           FROM ((public.customers c
             JOIN public.ports p ON ((c.customer_id = p.customer_id)))
             JOIN public.devices d ON ((p.device_id = d.device_id)))
          GROUP BY d.location
        ), combined AS (
         SELECT device_by_location.category,
            device_by_location.dimension,
            device_by_location.count_value
           FROM device_by_location
        UNION ALL
         SELECT device_by_role.category,
            device_by_role.dimension,
            device_by_role.count_value
           FROM device_by_role
        UNION ALL
         SELECT port_by_speed.category,
            port_by_speed.dimension,
            port_by_speed.count_value
           FROM port_by_speed
        UNION ALL
         SELECT port_by_type.category,
            port_by_type.dimension,
            port_by_type.count_value
           FROM port_by_type
        UNION ALL
         SELECT link_by_type.category,
            link_by_type.dimension,
            link_by_type.count_value
           FROM link_by_type
        UNION ALL
         SELECT link_by_status.category,
            link_by_status.dimension,
            link_by_status.count_value
           FROM link_by_status
        UNION ALL
         SELECT customer_by_site.category,
            customer_by_site.dimension,
            customer_by_site.count_value
           FROM customer_by_site
        )
 SELECT (row_number() OVER ())::text AS unique_id,
    category,
    dimension,
    (count_value)::integer AS count_value
   FROM combined;


ALTER VIEW public.v_network_summary_master OWNER TO myuser;

--
-- TOC entry 246 (class 1259 OID 16640)
-- Name: v_render_beck_links; Type: VIEW; Schema: public; Owner: myuser
--

CREATE VIEW public.v_render_beck_links AS
 WITH bounds AS (
         SELECT location_info.short_name,
            location_info.latitude,
            location_info.longitude,
            min(location_info.longitude) OVER () AS lon_min,
            max(location_info.longitude) OVER () AS lon_max,
            min(location_info.latitude) OVER () AS lat_min,
            max(location_info.latitude) OVER () AS lat_max
           FROM public.location_info
        ), loc_coords AS (
         SELECT bounds.short_name,
                CASE
                    WHEN (bounds.lon_max = bounds.lon_min) THEN (500)::numeric
                    ELSE (((bounds.longitude - bounds.lon_min) / NULLIF((bounds.lon_max - bounds.lon_min), (0)::numeric)) * (1000)::numeric)
                END AS x,
                CASE
                    WHEN (bounds.lat_max = bounds.lat_min) THEN (500)::numeric
                    ELSE (((bounds.latitude - bounds.lat_min) / NULLIF((bounds.lat_max - bounds.lat_min), (0)::numeric)) * (1000)::numeric)
                END AS y
           FROM bounds
        )
 SELECT tl.link_id,
    tl.link_type,
    tl.description,
    da.location AS a_device_location,
    tl.endpoint_a AS a_port_id,
    ca.x AS a_x,
    ca.y AS a_y,
    db.location AS b_device_location,
    tl.endpoint_b AS b_port_id,
    cb.x AS b_x,
    cb.y AS b_y,
    LEAST(COALESCE(pa.port_health_status, 4), COALESCE(pb.port_health_status, 4)) AS link_health
   FROM ((((((public.topology_links tl
     LEFT JOIN public.ports pa ON ((tl.endpoint_a = pa.port_id)))
     LEFT JOIN public.devices da ON ((pa.device_id = da.device_id)))
     LEFT JOIN loc_coords ca ON ((da.location = (ca.short_name)::text)))
     LEFT JOIN public.ports pb ON ((tl.endpoint_b = pb.port_id)))
     LEFT JOIN public.devices db ON ((pb.device_id = db.device_id)))
     LEFT JOIN loc_coords cb ON ((db.location = (cb.short_name)::text)));


ALTER VIEW public.v_render_beck_links OWNER TO myuser;

--
-- TOC entry 244 (class 1259 OID 16626)
-- Name: v_site_health_summary; Type: VIEW; Schema: public; Owner: myuser
--

CREATE VIEW public.v_site_health_summary AS
 SELECT location,
    min(health_status) AS worst_health,
    count(*) FILTER (WHERE (health_status < 3)) AS alert_count
   FROM public.devices
  GROUP BY location;


ALTER VIEW public.v_site_health_summary OWNER TO myuser;

--
-- TOC entry 243 (class 1259 OID 16622)
-- Name: v_summary_connections; Type: VIEW; Schema: public; Owner: myuser
--

CREATE VIEW public.v_summary_connections AS
 SELECT connection_status,
    service_bw,
    vrf_name,
    (count(*))::integer AS connection_count
   FROM public.fabric_connections
  GROUP BY connection_status, service_bw, vrf_name;


ALTER VIEW public.v_summary_connections OWNER TO myuser;

--
-- TOC entry 237 (class 1259 OID 16578)
-- Name: v_summary_customer_services; Type: VIEW; Schema: public; Owner: myuser
--

CREATE VIEW public.v_summary_customer_services AS
 SELECT c.customer_id,
    c.customer_name,
    c.account_id,
    (count(s.service_id))::integer AS service_count
   FROM (public.customers c
     LEFT JOIN public.fabric_services s ON ((c.customer_id = s.customer_id)))
  GROUP BY c.customer_id, c.customer_name, c.account_id;


ALTER VIEW public.v_summary_customer_services OWNER TO myuser;

--
-- TOC entry 238 (class 1259 OID 16583)
-- Name: v_summary_customers; Type: VIEW; Schema: public; Owner: myuser
--

CREATE VIEW public.v_summary_customers AS
 SELECT (count(*))::integer AS customer_count
   FROM public.customers;


ALTER VIEW public.v_summary_customers OWNER TO myuser;

--
-- TOC entry 233 (class 1259 OID 16562)
-- Name: v_summary_devices; Type: VIEW; Schema: public; Owner: myuser
--

CREATE VIEW public.v_summary_devices AS
 SELECT network,
    device_role AS role,
    device_model AS model,
    count(*) AS device_count
   FROM public.devices
  GROUP BY network, device_role, device_model;


ALTER VIEW public.v_summary_devices OWNER TO myuser;

--
-- TOC entry 239 (class 1259 OID 16587)
-- Name: v_summary_links; Type: VIEW; Schema: public; Owner: myuser
--

CREATE VIEW public.v_summary_links AS
 SELECT link_type,
    count(*) AS link_count
   FROM public.topology_links
  GROUP BY link_type;


ALTER VIEW public.v_summary_links OWNER TO myuser;

--
-- TOC entry 240 (class 1259 OID 16601)
-- Name: v_summary_links_by_location; Type: VIEW; Schema: public; Owner: myuser
--

CREATE VIEW public.v_summary_links_by_location AS
 SELECT loc.short_name AS location,
    l.link_type,
    count(*) AS link_endpoint_count
   FROM ((public.topology_links l
     JOIN public.devices d ON (((l.endpoint_a = d.device_id) OR (l.endpoint_b = d.device_id))))
     JOIN public.location_info loc ON ((d.location = (loc.short_name)::text)))
  GROUP BY loc.short_name, l.link_type;


ALTER VIEW public.v_summary_links_by_location OWNER TO myuser;

--
-- TOC entry 235 (class 1259 OID 16570)
-- Name: v_summary_port_health; Type: VIEW; Schema: public; Owner: myuser
--

CREATE VIEW public.v_summary_port_health AS
 SELECT port_type,
    port_speed,
    port_health_status AS health_status,
    count(*) AS port_count
   FROM public.ports
  GROUP BY port_type, port_speed, port_health_status;


ALTER VIEW public.v_summary_port_health OWNER TO myuser;

--
-- TOC entry 234 (class 1259 OID 16566)
-- Name: v_summary_ports; Type: VIEW; Schema: public; Owner: myuser
--

CREATE VIEW public.v_summary_ports AS
 SELECT port_type,
    port_speed,
    port_service_status AS service_status,
    count(*) AS port_count
   FROM public.ports
  GROUP BY port_type, port_speed, port_service_status;


ALTER VIEW public.v_summary_ports OWNER TO myuser;

--
-- TOC entry 236 (class 1259 OID 16574)
-- Name: v_summary_services; Type: VIEW; Schema: public; Owner: myuser
--

CREATE VIEW public.v_summary_services AS
 SELECT service_type,
    'Active'::text AS service_status,
    (count(*))::integer AS service_count
   FROM public.fabric_services
  GROUP BY service_type;


ALTER VIEW public.v_summary_services OWNER TO myuser;

--
-- TOC entry 241 (class 1259 OID 16612)
-- Name: v_telegraf_inventory; Type: VIEW; Schema: public; Owner: myuser
--

CREATE VIEW public.v_telegraf_inventory AS
 SELECT d.device_id,
    d.device_name,
    d.location,
    d.device_role,
    p.port_id,
    p.port_name,
    p.port_speed,
    p.port_cktid,
    p.port_optic,
    p.port_type,
    p.lag_parent_id,
    p.port_health_status,
    p.customer_id
   FROM (public.devices d
     JOIN public.ports p ON ((d.device_id = p.device_id)))
  WHERE ((d.lifecycle_status)::text = 'Active'::text)
  ORDER BY d.device_name, p.port_name;


ALTER VIEW public.v_telegraf_inventory OWNER TO myuser;

--
-- TOC entry 3577 (class 2606 OID 41004)
-- Name: bgp_neighbors bgp_neighbors_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.bgp_neighbors
    ADD CONSTRAINT bgp_neighbors_pkey PRIMARY KEY (bgp_neighbor_id);


--
-- TOC entry 3585 (class 2606 OID 49210)
-- Name: cloud_connection_members cloud_connection_members_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.cloud_connection_members
    ADD CONSTRAINT cloud_connection_members_pkey PRIMARY KEY (member_id);


--
-- TOC entry 3583 (class 2606 OID 49193)
-- Name: cloud_connections cloud_connections_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.cloud_connections
    ADD CONSTRAINT cloud_connections_pkey PRIMARY KEY (cloud_connection_id);


--
-- TOC entry 3587 (class 2606 OID 49229)
-- Name: cloud_partner_bandwidths cloud_partner_bandwidths_partner_id_service_bw_key; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.cloud_partner_bandwidths
    ADD CONSTRAINT cloud_partner_bandwidths_partner_id_service_bw_key UNIQUE (partner_id, service_bw);


--
-- TOC entry 3589 (class 2606 OID 49227)
-- Name: cloud_partner_bandwidths cloud_partner_bandwidths_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.cloud_partner_bandwidths
    ADD CONSTRAINT cloud_partner_bandwidths_pkey PRIMARY KEY (partner_bw_id);


--
-- TOC entry 3581 (class 2606 OID 49178)
-- Name: cloud_partners cloud_partners_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.cloud_partners
    ADD CONSTRAINT cloud_partners_pkey PRIMARY KEY (partner_id);


--
-- TOC entry 3533 (class 2606 OID 16404)
-- Name: cross_connects cross_connects_internal_circuit_id_key; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.cross_connects
    ADD CONSTRAINT cross_connects_internal_circuit_id_key UNIQUE (internal_circuit_id);


--
-- TOC entry 3535 (class 2606 OID 16400)
-- Name: cross_connects cross_connects_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.cross_connects
    ADD CONSTRAINT cross_connects_pkey PRIMARY KEY (connect_id);


--
-- TOC entry 3545 (class 2606 OID 16425)
-- Name: customers customers_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (customer_id);


--
-- TOC entry 3541 (class 2606 OID 16420)
-- Name: devices devices_device_name_key; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_device_name_key UNIQUE (device_name);


--
-- TOC entry 3543 (class 2606 OID 16418)
-- Name: devices devices_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.devices
    ADD CONSTRAINT devices_pkey PRIMARY KEY (device_id);


--
-- TOC entry 3567 (class 2606 OID 16524)
-- Name: fabric_connections fabric_connections_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.fabric_connections
    ADD CONSTRAINT fabric_connections_pkey PRIMARY KEY (connection_id);


--
-- TOC entry 3559 (class 2606 OID 16475)
-- Name: fabric_services fabric_services_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.fabric_services
    ADD CONSTRAINT fabric_services_pkey PRIMARY KEY (service_id);


--
-- TOC entry 3569 (class 2606 OID 16536)
-- Name: hardware_documents hardware_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.hardware_documents
    ADD CONSTRAINT hardware_documents_pkey PRIMARY KEY (document_id);


--
-- TOC entry 3565 (class 2606 OID 16509)
-- Name: hardware_specs hardware_specs_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.hardware_specs
    ADD CONSTRAINT hardware_specs_pkey PRIMARY KEY (hardware_id);


--
-- TOC entry 3547 (class 2606 OID 16432)
-- Name: interface interface_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.interface
    ADD CONSTRAINT interface_pkey PRIMARY KEY (interface_id);


--
-- TOC entry 3561 (class 2606 OID 16487)
-- Name: ipv4_interfaces ipv4_interfaces_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.ipv4_interfaces
    ADD CONSTRAINT ipv4_interfaces_pkey PRIMARY KEY (ipv4_address_id);


--
-- TOC entry 3563 (class 2606 OID 16499)
-- Name: ip_interfaces ipv6_interfaces_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.ip_interfaces
    ADD CONSTRAINT ipv6_interfaces_pkey PRIMARY KEY (ip_address_id);


--
-- TOC entry 3539 (class 2606 OID 16411)
-- Name: location_info location_info_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.location_info
    ADD CONSTRAINT location_info_pkey PRIMARY KEY (location_id);


--
-- TOC entry 3553 (class 2606 OID 16447)
-- Name: lric_cost_model lric_cost_model_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.lric_cost_model
    ADD CONSTRAINT lric_cost_model_pkey PRIMARY KEY (cost_model_id);


--
-- TOC entry 3531 (class 2606 OID 16393)
-- Name: patch_panels patch_panels_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.patch_panels
    ADD CONSTRAINT patch_panels_pkey PRIMARY KEY (port_id);


--
-- TOC entry 3557 (class 2606 OID 16461)
-- Name: ports ports_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.ports
    ADD CONSTRAINT ports_pkey PRIMARY KEY (port_id);


--
-- TOC entry 3551 (class 2606 OID 16441)
-- Name: power_options power_options_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.power_options
    ADD CONSTRAINT power_options_pkey PRIMARY KEY (power_source_id);


--
-- TOC entry 3571 (class 2606 OID 16550)
-- Name: routeVision routeVision_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public."routeVision"
    ADD CONSTRAINT "routeVision_pkey" PRIMARY KEY (route_id);


--
-- TOC entry 3573 (class 2606 OID 24667)
-- Name: route_vision route_vision_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.route_vision
    ADD CONSTRAINT route_vision_pkey PRIMARY KEY (route_id);


--
-- TOC entry 3579 (class 2606 OID 41014)
-- Name: routing_policies routing_policies_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.routing_policies
    ADD CONSTRAINT routing_policies_pkey PRIMARY KEY (policy_id);


--
-- TOC entry 3575 (class 2606 OID 40990)
-- Name: static_routes static_routes_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.static_routes
    ADD CONSTRAINT static_routes_pkey PRIMARY KEY (route_id);


--
-- TOC entry 3555 (class 2606 OID 16454)
-- Name: topology_links topology_links_pkey; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.topology_links
    ADD CONSTRAINT topology_links_pkey PRIMARY KEY (link_id);


--
-- TOC entry 3537 (class 2606 OID 16402)
-- Name: cross_connects uq_cross_connect_endpoints; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.cross_connects
    ADD CONSTRAINT uq_cross_connect_endpoints UNIQUE (local_port_id, remote_port_id);


--
-- TOC entry 3549 (class 2606 OID 16434)
-- Name: interface uq_interface_on_port; Type: CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.interface
    ADD CONSTRAINT uq_interface_on_port UNIQUE (port_id, interface_name);


--
-- TOC entry 3766 (class 2618 OID 49254)
-- Name: v_fabric_service_detail _RETURN; Type: RULE; Schema: public; Owner: myuser
--

CREATE OR REPLACE VIEW public.v_fabric_service_detail AS
 SELECT fs.service_id,
    fs.customer_id,
    c.customer_name,
    c.account_id,
    fs.service_name,
    fs.service_alias,
    fs.service_type,
    fs.service_description,
    fs.route_target,
    fs.health_status,
    fs.created_at,
    fs.updated_at,
    COALESCE(json_agg(DISTINCT jsonb_build_object('connection_id', fc.connection_id, 'service_id', fc.service_id, 'connection_name', fc.connection_name, 'connection_status', fc.connection_status, 'health_status', fc.health_status, 'c_vlan_list', fc.c_vlan_list, 'created_at', fc.created_at, 'updated_at', fc.updated_at)) FILTER (WHERE (fc.connection_id IS NOT NULL)), '[]'::json) AS fabric_connections
   FROM ((public.fabric_services fs
     LEFT JOIN public.customers c ON ((fs.customer_id = c.customer_id)))
     LEFT JOIN public.fabric_connections fc ON ((fs.service_id = fc.service_id)))
  GROUP BY fs.service_id, c.customer_name, c.account_id;


--
-- TOC entry 3767 (class 2618 OID 49259)
-- Name: v_interface_detail _RETURN; Type: RULE; Schema: public; Owner: myuser
--

CREATE OR REPLACE VIEW public.v_interface_detail AS
 SELECT i.interface_id,
    i.port_id,
    i.ckt_id,
    i.description,
    i.interface_name,
    i.interface_type,
    i.svlan_id,
    i.cvlan_list,
    i.dhcp_relay_enabled,
    i.service_bw_mbps,
    i.status,
    i.created_at,
    i.updated_at,
    jsonb_build_object('port_id', p.port_id, 'mac_address', p.mac_address, 'port_name', p.port_name, 'port_speed', p.port_speed, 'device_id', p.device_id, 'port_description', p.port_description, 'port_optic', p.port_optic, 'port_tagging', p.port_tagging, 'port_cktid', p.port_cktid, 'customer_id', p.customer_id, 'port_service_status', p.port_service_status, 'port_type', p.port_type, 'port_health_status', p.port_health_status, 'admin_status', p.admin_status, 'oper_status', p.oper_status, 'created_at', p.created_at, 'updated_at', p.updated_at) AS port,
    COALESCE(json_agg(DISTINCT jsonb_build_object('ip_address_id', ip.ip_address_id, 'interface_id', ip.interface_id, 'lumen_ip_address', ip.lumen_ip_address, 'customer_ip_address', ip.customer_ip_address, 'network_mask_cidr', ip.network_mask_cidr, 'bring_your_own_ip', ip.bring_your_own_ip)) FILTER (WHERE (ip.ip_address_id IS NOT NULL)), '[]'::json) AS ip_addresses,
    COALESCE(json_agg(DISTINCT jsonb_build_object('bgp_neighbor_id', b.bgp_neighbor_id, 'interface_id', b.interface_id, 'neighbor_ip', b.neighbor_ip, 'local_ip', b.local_ip, 'remote_asn', b.remote_asn, 'local_asn', b.local_asn, 'session_type', b.session_type, 'session_state', b.session_state, 'description', b.description, 'community', b.community, 'import_policy', b.import_policy, 'export_policy', b.export_policy, 'multihop', b.multihop, 'auth', b.auth, 'auth_password', b.auth_password, 'bfd', b.bfd, 'bfd_interval', b.bfd_interval, 'bfd_multiple', b.bfd_multiple, 'created_at', b.created_at, 'updated_at', b.updated_at)) FILTER (WHERE (b.bgp_neighbor_id IS NOT NULL)), '[]'::json) AS bgp_neighbors,
    COALESCE(json_agg(DISTINCT jsonb_build_object('route_id', sr.route_id, 'interface_id', sr.interface_id, 'ip_prefix', sr.ip_prefix, 'prefix_mask', sr.prefix_mask, 'next_hop_ip', sr.next_hop_ip, 'metric', sr.metric, 'community', sr.community, 'created_at', sr.created_at, 'updated_at', sr.updated_at)) FILTER (WHERE (sr.route_id IS NOT NULL)), '[]'::json) AS static_routes
   FROM ((((public.interface i
     LEFT JOIN public.ports p ON ((i.port_id = p.port_id)))
     LEFT JOIN public.ip_interfaces ip ON ((i.interface_id = ip.interface_id)))
     LEFT JOIN public.bgp_neighbors b ON ((i.interface_id = b.interface_id)))
     LEFT JOIN public.static_routes sr ON ((i.interface_id = sr.interface_id)))
  GROUP BY i.interface_id, p.port_id, p.mac_address, p.port_name, p.port_speed, p.device_id, p.port_description, p.port_optic, p.port_tagging, p.port_cktid, p.customer_id, p.port_service_status, p.port_type, p.port_health_status, p.admin_status, p.oper_status, p.created_at, p.updated_at;


--
-- TOC entry 3603 (class 2606 OID 49211)
-- Name: cloud_connection_members cloud_connection_members_cloud_connection_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.cloud_connection_members
    ADD CONSTRAINT cloud_connection_members_cloud_connection_id_fkey FOREIGN KEY (cloud_connection_id) REFERENCES public.cloud_connections(cloud_connection_id) ON DELETE CASCADE;


--
-- TOC entry 3604 (class 2606 OID 49216)
-- Name: cloud_connection_members cloud_connection_members_interface_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.cloud_connection_members
    ADD CONSTRAINT cloud_connection_members_interface_id_fkey FOREIGN KEY (interface_id) REFERENCES public.interface(interface_id);


--
-- TOC entry 3602 (class 2606 OID 49194)
-- Name: cloud_connections cloud_connections_partner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.cloud_connections
    ADD CONSTRAINT cloud_connections_partner_id_fkey FOREIGN KEY (partner_id) REFERENCES public.cloud_partners(partner_id) ON DELETE CASCADE;


--
-- TOC entry 3605 (class 2606 OID 49230)
-- Name: cloud_partner_bandwidths cloud_partner_bandwidths_partner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.cloud_partner_bandwidths
    ADD CONSTRAINT cloud_partner_bandwidths_partner_id_fkey FOREIGN KEY (partner_id) REFERENCES public.cloud_partners(partner_id) ON DELETE CASCADE;


--
-- TOC entry 3595 (class 2606 OID 16525)
-- Name: fabric_connections fabric_connections_service_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.fabric_connections
    ADD CONSTRAINT fabric_connections_service_id_fkey FOREIGN KEY (service_id) REFERENCES public.fabric_services(service_id) ON DELETE CASCADE;


--
-- TOC entry 3591 (class 2606 OID 16476)
-- Name: fabric_services fabric_services_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.fabric_services
    ADD CONSTRAINT fabric_services_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.customers(customer_id);


--
-- TOC entry 3596 (class 2606 OID 16537)
-- Name: hardware_documents hardware_documents_hardware_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.hardware_documents
    ADD CONSTRAINT hardware_documents_hardware_id_fkey FOREIGN KEY (hardware_id) REFERENCES public.hardware_specs(hardware_id);


--
-- TOC entry 3594 (class 2606 OID 16510)
-- Name: hardware_specs hardware_specs_power_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.hardware_specs
    ADD CONSTRAINT hardware_specs_power_source_id_fkey FOREIGN KEY (power_source_id) REFERENCES public.power_options(power_source_id);


--
-- TOC entry 3592 (class 2606 OID 16488)
-- Name: ipv4_interfaces ipv4_interfaces_interface_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.ipv4_interfaces
    ADD CONSTRAINT ipv4_interfaces_interface_id_fkey FOREIGN KEY (interface_id) REFERENCES public.interface(interface_id) ON DELETE CASCADE;


--
-- TOC entry 3593 (class 2606 OID 16500)
-- Name: ip_interfaces ipv6_interfaces_interface_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.ip_interfaces
    ADD CONSTRAINT ipv6_interfaces_interface_id_fkey FOREIGN KEY (interface_id) REFERENCES public.interface(interface_id) ON DELETE CASCADE;


--
-- TOC entry 3590 (class 2606 OID 16462)
-- Name: ports ports_device_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.ports
    ADD CONSTRAINT ports_device_id_fkey FOREIGN KEY (device_id) REFERENCES public.devices(device_id) ON DELETE CASCADE;


--
-- TOC entry 3597 (class 2606 OID 16556)
-- Name: routeVision routeVision_fabric_connection_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public."routeVision"
    ADD CONSTRAINT "routeVision_fabric_connection_id_fkey" FOREIGN KEY (fabric_connection_id) REFERENCES public.fabric_connections(connection_id);


--
-- TOC entry 3598 (class 2606 OID 16551)
-- Name: routeVision routeVision_fabric_service_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public."routeVision"
    ADD CONSTRAINT "routeVision_fabric_service_id_fkey" FOREIGN KEY (fabric_service_id) REFERENCES public.fabric_services(service_id);


--
-- TOC entry 3599 (class 2606 OID 24673)
-- Name: route_vision route_vision_fabric_connection_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.route_vision
    ADD CONSTRAINT route_vision_fabric_connection_id_fkey FOREIGN KEY (fabric_connection_id) REFERENCES public.fabric_connections(connection_id);


--
-- TOC entry 3600 (class 2606 OID 24668)
-- Name: route_vision route_vision_fabric_service_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.route_vision
    ADD CONSTRAINT route_vision_fabric_service_id_fkey FOREIGN KEY (fabric_service_id) REFERENCES public.fabric_services(service_id);


--
-- TOC entry 3601 (class 2606 OID 41015)
-- Name: routing_policies routing_policies_fabric_service_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: myuser
--

ALTER TABLE ONLY public.routing_policies
    ADD CONSTRAINT routing_policies_fabric_service_id_fkey FOREIGN KEY (fabric_service_id) REFERENCES public.fabric_services(service_id);


-- Completed on 2026-03-02 11:47:08

--
-- PostgreSQL database dump complete
--

\unrestrict yrfuOibYaVec1Ah5Jogf3Mrmy8SG9TEHa8ZhjU3jWmaNtAirPefrmTVrnWPA8Eb

