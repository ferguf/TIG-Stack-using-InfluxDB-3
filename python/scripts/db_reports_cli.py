""" File Name: 'db_reports_cli.py' date: '2025-12-01 10:55 MST' (CLI for running database reports) """
# db_reports_cli.py
"""
Contains functions for formatting, printing, and executing database reports.
"""
# UPDATED: Import the two new, separate functions
from db_operations import view_fabric_Connection_counts, view_fabric_Connection_ports
from cli_base import get_db, Engine
from click import 

# --- Printing Functions for New Reports ---

def print_connection_port_count_report(report_data):
    """
    Formats and prints the Connection and Port Count Report.
    """
    print("\n--- Connection and Port Count per Service ---")
    print("------------------------------------------------------------------")
    header = ["Customer Name", "Service Name", "Connection Count", "Port Count"]
    format_string = "{:<20} | {:<20} | {:<16} | {:<10}"
    
    print(format_string.format(*header))
    print("-" * 75)
    
    for row in report_data:
        print(format_string.format(
            row.customer_name,
            row.service_name,
            row.connection_count,
            row.port_count
        ))
    print("-" * 75)

def print_detailed_view_report(report_data):
    """
    Formats and prints the Detailed View Report (Service Endpoints).
    """
    print("\n--- Detailed Service/Connection Endpoints (v_fabric_connections) ---")
    print("----------------------------------------------------------------------------------")
    header = ["Customer Name", "Service Name", "Device Name", "Port Name", "Connection Name", "Connection Status"]
    format_string = "{:<20} | {:<20} | {:<15} | {:<10} | {:<15} | {:<18}"
    
    print(format_string.format(*header))
    print("-" * 107)
    
    for row in report_data:
        # Handle None values for display
        def safe_str(val):
            return str(val) if val is not None else ""

        print(format_string.format(
            safe_str(row.customer_name),
            safe_str(row.service_name),
            safe_str(row.device_name),
            safe_str(row.port_name),
            safe_str(row.connection_name),
            safe_str(row.connection_status)
        ))
    print("-" * 107)


# --- Main Application Execution Example ---

def run_report():
    """ 
    Runs all reports by retrieving data from db_operations and printing them.
    This function is the new entry point for report generation.
    """
    if not Engine:
        print("FATAL: Database engine not available. Cannot run report.")
        return

    # Use the database session manager
    try:
        db = next(get_db())
        
        # UPDATED: Run the two separate report functions
        count_data = view_fabric_Connection_counts(db)
        detail_data = view_fabric_Connection_ports(db)
        
        # Print the received data
        print_connection_port_count_report(count_data)
        print_detailed_view_report(detail_data)
        
    except Exception as e:
        print(f"ERROR: Failed to run the report due to: {e}")


def run_connection_port_count_report():
    """Runs only the Connection and Port Count Report."""
    if not Engine:
        print("FATAL: Database engine not available.")
        return
    try:
        db = next(get_db())
        count_data = view_fabric_Connection_counts(db)
        print_connection_port_count_report(count_data)
    except Exception as e:
        print(f"ERROR: Failed to run connection/port count report: {e}")


def run_detailed_view_report():
    """Runs only the Detailed Service/Connection Endpoints Report."""
    if not Engine:
        print("FATAL: Database engine not available.")
        return
    try:
        db = next(get_db())
        detail_data = view_fabric_Connection_ports(db)
        print_detailed_view_report(detail_data)
    except Exception as e:
        print(f"ERROR: Failed to run detailed view report: {e}")


# If this script is run directly, execute the report
if __name__ == "__main__":
    run_report()

@cli.command()
def connection_report():
    """Runs the Connection and Port Count Report."""
    from db_reports_cli import run_connection_port_count_report
    run_connection_port_count_report()


@cli.command()
def detailed_report():
    """Runs the Detailed Service/Connection Endpoints Report."""
    from db_reports_cli import run_detailed_view_report
    run_detailed_view_report()
