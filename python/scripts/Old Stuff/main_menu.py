import subprocess
import sys
import os

# --- Configuration ---
# Define the external scripts this menu will execute
DB_SCRIPT = 'db_man_cli.py'
CUSTOMER_SCRIPT = 'customer_cli.py'
APP_TITLE = 'DB and Inventory Management System'

def display_menu():
    """Displays the main CLI menu options."""
    print(f"\n--- Main Menu for {APP_TITLE} ---")
    print("--------------------------------------------------")
    
    print("\n--- Management Options ---")
    print(f" [1] DB Management (Calls: {DB_SCRIPT})")
    print(f" [2] Customer Management (Calls: {CUSTOMER_SCRIPT})")
    print("--------------------------------------------------")
    print(" [h] Show this help menu")
    print(" [q] Quit the application")
    print("--------------------------------------------------")

def run_command(script_name):
    """
    Executes an external script using the system's Python interpreter.
    
    Args:
        script_name (str): The name of the Python script to execute.
    """
    # Use sys.executable to ensure the script is run with the same Python environment
    command = [sys.executable, script_name]
    
    print(f"\n-> Executing command: {' '.join(command)}...")
    
    try:
        # Run the command and capture its output (stdout/stderr are passed through by default)
        result = subprocess.run(
            command, 
            check=False,  # Don't raise an exception for non-zero exit codes
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        
        if result.returncode == 0:
            print(f"\n<- Command '{script_name}' completed successfully.")
        else:
            print(f"\n<- WARNING: Command '{script_name}' failed with exit code {result.returncode}.")
            
    except FileNotFoundError:
        print(f"\n<- ERROR: Python interpreter not found or script '{script_name}' is missing.")
    except Exception as e:
        print(f"\n<- ERROR during execution of '{script_name}': {e}")
        
    input("\nPress Enter to return to main menu...") # Wait for user acknowledgment

def main():
    """The main loop for the application menu."""
    while True:
        display_menu()
        
        # Get user input
        choice = input("Enter choice (1, 2, h, q): ").strip().lower()
        
        if choice == '1':
            run_command(DB_SCRIPT)
        elif choice == '2':
            run_command(CUSTOMER_SCRIPT)
        elif choice == 'h':
            # 'h' just redisplays the menu, which happens automatically in the next loop iteration
            continue
        elif choice == 'q':
            print(f"\nExiting {APP_TITLE}. Goodbye!")
            sys.exit(0)
        else:
            print(f"\nInvalid choice: '{choice}'. Please enter '1', '2', 'h', or 'q'.")

if __name__ == "__main__":
    # Note: For this script to work, the files 'db_man_cli.py' and 'customer_cli.py' 
    # must be present in the same directory.
    main()