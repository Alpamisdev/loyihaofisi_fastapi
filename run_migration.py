#!/usr/bin/env python3
import os
import sys
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration")

def run_migration():
    """Run the Alembic migration to add the token_hash column."""
    try:
        logger.info("Running Alembic migration...")
        result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Migration successful!")
            logger.info(result.stdout)
            return True
        else:
            logger.error(f"Migration failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error running migration: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
