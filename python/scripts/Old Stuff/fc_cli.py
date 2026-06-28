"""File Name: 'fc_cli.py' and version '1.1.6' date: 'November 30, 2025 12:10 PM MST' (Change: Fixed DetachedInstanceError in verification phase by using the scalar 'service_name' stored in scalar_data instead of the detached ORM object 'service_to_provision' for printing.) """

import sys
import uuid
import datetime
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker, joinedload, relationship # Added relationship
from sqlalchemy.sql.expression import not_

import db_config 

# Import models and utilities from their respective modules
from network_inventory_models import Base, Port, FabricConnection, Customer, FabricService, Interface
# IMPORTANT: Import the logic function and utilities from the new logic module
from network_service_logic import db_session_scope, configure_eline_epl, setup_mock_data, decommission_eline_epl # Decommission added

# Use an in-memory SQLite database for demonstration
DB_CONN_STRING = "sqlite:///:memory:" 
engine = create_engine(DB_CONN_STRING)

def main():
    """Main CLI execution function."""
    print("===================================================")
    print(" Fabric Connection CLI - E-Line EPL Configuration")
    print("===================================================")
    
    # 1. Initialize Database Schema
    Base.metadata.create_all(engine)
    
    # 2. Setup Mock Data and Retrieve Initial Objects
    # We will use this dictionary to store scalar IDs/names needed for subsequent steps
    scalar_data = {} 
    
    try:
        with db_session_scope(engine) as session:
            # orm_data_from_setup contains the ORM objects from the initial session
            orm_data_from_setup = setup_mock_data(session) 
            
            # Load only scalar, non-ORM attributes needed outside this session
            scalar_data['service_id'] = orm_data_from_setup['service'].service_id
            scalar_data['service_name'] = orm_data_from_setup['service'].service_name
            
            scalar_data['port1_id'] = orm_data_from_setup['port1'].port_id
            scalar_data['port1_name'] = orm_data_from_setup['port1'].port_name
            scalar_data['port2_id'] = orm_data_from_setup['port2'].port_id
            scalar_data['port2_name'] = orm_data_from_setup['port2'].port_name
            
            scalar_data['interface_id'] = orm_data_from_setup['interface'].interface_id
            scalar_data['customer_id'] = orm_data_from_setup['customer'].customer_id
            scalar_data['customer_name'] = orm_data_from_setup['customer'].name
            scalar_data['customer_account'] = orm_data_from_setup['customer'].account_id

            print("\n[INFO] Mock inventory created:")
            print(f"  Customer: {scalar_data['customer_name']} (Account: {scalar_data['customer_account']})")
            print(f"  Service: {scalar_data['service_name']}")
            print(f"  Ports: {scalar_data['port1_name']}, {scalar_data['port2_name']}")
            
    except Exception as e:
        print(f"\n[FATAL ERROR] Mock data setup failed. Error: {e}")
        sys.exit(1)

    # 3. User Selection (Service & Bandwidth)
    selected_service_id = scalar_data['service_id']
    selected_service_name = scalar_data['service_name']
    print(f"\n[SELECTION] Automatically selecting pre-existing service: {selected_service_name}")
    
    # Get User Input for Bandwidth
    while True:
        try:
            bw_input = input(f"Enter service bandwidth (Mbits, e.g., 500): ")
            service_bw = int(bw_input)
            if service_bw <= 0:
                raise ValueError
            break
        except ValueError:
            print("ERROR: Please enter a positive integer for bandwidth.")

    try:
        # 4. Execute Configuration within a Transactional Scope (CRITICAL STEP)
        new_fc_id = None # Variable to store the ID of the newly created connection
        with db_session_scope(engine) as session:
            # A. Re-fetch objects within the new session's scope using the stored IDs
            # Ensure all objects passed to logic function are attached to this session
            service_to_provision = session.get(FabricService, selected_service_id)
            port1 = session.get(Port, scalar_data['port1_id'])
            port2 = session.get(Port, scalar_data['port2_id'])
            interface_to_use = session.get(Interface, scalar_data['interface_id']) 
            
            # B. THE CALL: Call the core configuration logic function
            new_connection = configure_eline_epl( # Renamed fc to new_connection
                session=session,
                service=service_to_provision,
                port1=port1, 
                port2=port2, 
                service_bw_mbits=service_bw,
                interface=interface_to_use 
            )
            
            # C. Extract the scalar ID BEFORE the session closes
            new_fc_id = new_connection.connection_id 
            
        # 5. Verification (Open a new session to check committed data)
        print("\n--- Verifying Configuration ---")
        with db_session_scope(engine) as session:
            # Re-fetch objects for verification using the scalar ID
            fc_check = session.get(FabricConnection, new_fc_id)
            port1_check = session.get(Port, scalar_data['port1_id']) 
            customer_check = session.get(Customer, scalar_data['customer_id'])
            
            print("\n===================================================")
            print(" [SUCCESS] E-Line EPL Service Configuration Complete!")
            print("===================================================")
            
            print(f"Customer: {customer_check.name} (ID: {customer_check.account_id})")
            # FIX: Use the scalar name instead of the detached ORM object
            print(f"Service: {scalar_data['service_name']}")
            print(f"Connection Name: {fc_check.connection_name}")
            print(f"Bandwidth: {fc_check.bandwidth_mbits} Mbits")
            print(f"Connection Type: {fc_check.connection_type}")
            print(f"Endpoint 1 Status: {port1_check.port_name} -> {port1_check.port_service_status} ({port1_check.port_type})")


        # 6. Test Decommissioning Flow (Optional Cleanup Step)
        decomm_input = input("\nDo you want to run the decommissioning test? (y/N): ")
        if decomm_input.lower() == 'y':
            print("\n--- Starting Decommission Test ---")
            with db_session_scope(engine) as session:
                decommission_eline_epl(session, service_id=selected_service_id)
            
            # 7. Verification after Decommissioning
            with db_session_scope(engine) as session:
                fc_check_after = session.query(FabricConnection).filter(FabricConnection.service_id == selected_service_id).one_or_none()
                port1_check_after = session.get(Port, scalar_data['port1_id'])
                
                print("\n===================================================")
                print(" [SUCCESS] Decommission Verification Complete!")
                print("===================================================")
                if fc_check_after is None:
                    print(f"Fabric Connection record for {selected_service_name} was successfully deleted.")
                else:
                    print("ERROR: Fabric Connection record still exists.")
                
                print(f"Port 1 Status: {port1_check_after.port_name} -> {port1_check_after.port_service_status} ({port1_check_after.port_type})")
                
                if port1_check_after.port_service_status == 'AVAILABLE' and port1_check_after.port_type == 'NNI':
                    print("Port status correctly reset to inventory defaults.")
                else:
                    print("ERROR: Port status was not reset correctly.")


    except Exception as e:
        print(f"\n[FATAL ERROR] Configuration failed. Error: {type(e).__name__}: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()