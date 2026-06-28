from influxdb_client_3 import InfluxDBClient3
import pandas as pd

# Hardcoded Truth
client = InfluxDBClient3(
    host="influxdb3-core",
    port=8181,
    token="apiv3_aAcM9fWA-xBEv3DJhD3Zvx-PCjrLFSvbP_s0ArjY8qf8aS1Ac55VKBVssyKvy8mB445W7ryAX-g0zsOiHsaiJg",
    database="network_inventory",
    enable_tls=False
)

try:
    print("Checking connection...")
    table = client.query(query="SELECT * FROM mpls_ldp_fec LIMIT 1")
    print("SUCCESS: Data retrieved!")
    print(table.to_pandas())
except Exception as e:
    print(f"FAILED: {e}")