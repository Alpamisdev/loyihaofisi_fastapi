import os
import subprocess

def init_migrations():
    # Create initial migration
    subprocess.run(["alembic", "revision", "--autogenerate", "-m", "Initial migration"])
    
    # Apply migration
    subprocess.run(["alembic", "upgrade", "head"])
    
    print("Database migrations initialized successfully.")

if __name__ == "__main__":
    init_migrations()
