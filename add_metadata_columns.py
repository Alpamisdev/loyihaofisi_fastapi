#!/usr/bin/env python3
import os
import sys
import logging
from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("add_metadata_columns")

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Add the script directory to the Python path
sys.path.insert(0, script_dir)

# Import the database connection
from app.database import engine

def add_metadata_columns():
    """Add metadata columns to the uploaded_files table."""
    try:
        # Create a connection
        conn = engine.connect()
        
        # Check if columns already exist
        inspector = sa.inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('uploaded_files')]
        
        # Add title column if it doesn't exist
        if 'title' not in columns:
            logger.info("Adding 'title' column to uploaded_files table...")
            conn.execute(sa.text("ALTER TABLE uploaded_files ADD COLUMN title VARCHAR;"))
        
        # Add language column if it doesn't exist
        if 'language' not in columns:
            logger.info("Adding 'language' column to uploaded_files table...")
            conn.execute(sa.text("ALTER TABLE uploaded_files ADD COLUMN language VARCHAR;"))
        
        # Add info column if it doesn't exist
        if 'info' not in columns:
            logger.info("Adding 'info' column to uploaded_files table...")
            conn.execute(sa.text("ALTER TABLE uploaded_files ADD COLUMN info TEXT;"))
        
        logger.info("Metadata columns added successfully.")
        conn.close()
        
    except SQLAlchemyError as e:
        logger.error(f"Error adding metadata columns: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sqlalchemy as sa
    add_metadata_columns()
