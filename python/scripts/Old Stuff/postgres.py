"""
Script to generate a PostgreSQL INSERT VALUES block for multiple ports
across a list of defined device UUIDs.
"""

# The raw data list based on the user's input (UUID, Device Name)
device_inventory = [
    ('d7a3f1c0-9134-4a84-bce5-0346eab44f27', 'VAR1.DEN1'),
    ('1a3276f2-70f6-4698-a37e-a4fee2cfd673', 'VAR2.DEN1'),
    ('abcbfb3c-4b7c-4d64-aeff-c1ffaf231aec', 'VAR1.ALB1'),
    ('b3191867-8ce7-4376-9f5b-d3e30dd2f2aa', 'VAR2.ALB1'),
    ('3ad60f84-2f1e-4559-bcc1-15e151ea22c6', 'VAR1.CHI1'),
    ('34542fc9-840d-400c-9db6-dc816413aff7', 'VAR2.CHI1'),
    ('426b504b-37e9-443d-a117-47037c603e6a', 'VAR1.NYC1'),
    ('dfc32a18-7303-4c49-b80d-4ea0cc874e42', 'VAR2.NYC1'),
    ('8a83d57f-0163-49f9-8e3c-2dc4054eb4ec', 'VAR1.SFO1'),
    ('4da4eebe-6a28-4f49-8581-b17778ac45a6', 'SDR1.DEN1'),
    ('9a6d3f2c-4823-40d3-82f0-93ea9de6862e', 'SDR2.DEN1'),
    ('69c7dbe8-d69c-4af2-a9f0-1120677f17db', 'VAR3.DEN1'),
    ('10ef5517-4a04-4edd-bd98-5d7decd1f31b', 'SDR1.ALB1'),
    ('303bfd7c-a585-402d-bf70-84e944c7e86b', 'SDR2.ALB1'),
    ('b78f4f62-ef64-4459-90cc-b6ecd4f6461c', 'VAR3.CHI1'),
    ('c9334db8-29f6-4e71-971b-caac18cb2d4b', 'SDR1.CHI1'),
    ('ae089f37-4b00-4ea9-b3ba-792f89785a14', 'SDR2.CHI1'),
    ('66224338-6458-42b0-9cf3-dc0fbb64a6d1', 'SDR1.NYC1'),
    ('5381009f-6527-4adc-aa08-3467ff7a9871', 'ESP3.NYC1'),
    ('5d8c54b1-e1e8-4ee2-af24-c80e071c9569', 'SDR1.SFO1'),
    ('85d85608-e2ac-4345-bd62-67f264470562', 'SDR2.SFO1'),
]

# SQL template for 4 ports, with placeholders for UUID and Device Name
SQL_PORT_TEMPLATE = """
-- Ports for {device_name} (UUID: {uuid})
(
    uuid_generate_v4(), 
    'gig-2/1/0', 
    '400G'::port_speed_enum, 
    'Unknown'::port_optic_enum,     
    'Network'::fabric_port_type_enum, 
    'Untagged'::port_tagging_enum, 
    'Planned'::port_service_status_enum, 
    1,
    '{uuid}'
),
(
    uuid_generate_v4(), 
    'gig-2/1/1', 
    '400G'::port_speed_enum, 
    '400G - LR4'::port_optic_enum, 
    'Network'::fabric_port_type_enum, 
    'Tagged'::port_tagging_enum, 
    'Active'::port_service_status_enum, 
    1,
    '{uuid}'
),
(
    uuid_generate_v4(), 
    'gig-2/1/2', 
    '400G'::port_speed_enum, 
    '400G - LR4'::port_optic_enum, 
    'Network'::fabric_port_type_enum, 
    'Tagged'::port_tagging_enum, 
    'Planned'::port_service_status_enum, 
    1,
    '{uuid}'
),
(
    uuid_generate_v4(), 
    'gig-3/1/0', 
    '400G'::port_speed_enum, 
    '400G - LR4'::port_optic_enum, 
    'Network'::fabric_port_type_enum, 
    'Tagged'::port_tagging_enum, 
    'Active'::port_service_status_enum, 
    1,
    '{uuid}'
),
"""

def generate_sql_inserts(devices):
    """
    Generates the complete PostgreSQL VALUES block string.
    """
    sql_blocks = []
    
    for uuid, device_name in devices:
        # Fill the template using Python's format method
        block = SQL_PORT_TEMPLATE.format(uuid=uuid, device_name=device_name)
        sql_blocks.append(block.strip())

    # Join all blocks with a comma and a newline, then strip any trailing comma/whitespace 
    # from the entire block before adding the final semicolon.
    return ",\n".join(sql_blocks)


if __name__ == "__main__":
    generated_sql = generate_sql_inserts(device_inventory)
    
    # Print the header for clarity, followed by the generated VALUES block
    print("\n-- Generated PostgreSQL INSERT statement for all device ports --")
    print("INSERT INTO ports (port_id, port_name, port_speed, port_optic, fabric_port_type, port_tagging, service_status, health, device_id)\nVALUES")
    print(generated_sql + ";")