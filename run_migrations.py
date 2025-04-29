#!/usr/bin/env python3
import os
import sys
import subprocess

def run_migrations():
    """Run Alembic migrations."""
    print("Running database migrations...")
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the script directory
    os.chdir(script_dir)
    
    # Run the migration
    result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Migrations completed successfully.")
        print(result.stdout)
    else:
        print("Error running migrations:")
        print(result.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_migrations()
