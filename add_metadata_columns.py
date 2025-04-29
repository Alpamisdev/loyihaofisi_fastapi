#!/usr/bin/env python3
import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("add_metadata_columns")

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Add the script directory to the Python path
sys.path.insert(0, script_dir)

# Import the database connection
try:
    from app.database import engine
    logger.info("Using imported engine from app.database")
except ImportError:
    # If import fails, create a new engine
    logger.info("Creating new engine")
    engine = create_engine("sqlite:///./website.db", connect_args={"check_same_thread": False})

def add_metadata_columns():
    """Add metadata columns to the uploaded_files table."""
    try:
        # Create a connection
        conn = engine.connect()
        
        # Check if columns already exist
        try:
            # Try to select from the columns to check if they exist
            conn.execute(text("SELECT title FROM uploaded_files LIMIT 1"))
            logger.info("Column 'title' already exists")
            title_exists = True
        except SQLAlchemyError:
            logger.info("Column 'title' does not exist")
            title_exists = False
            
        try:
            conn.execute(text("SELECT language FROM uploaded_files LIMIT 1"))
            logger.info("Column 'language' already exists")
            language_exists = True
        except SQLAlchemyError:
            logger.info("Column 'language' does not exist")
            language_exists = False
            
        try:
            conn.execute(text("SELECT info FROM uploaded_files LIMIT 1"))
            logger.info("Column 'info' already exists")
            info_exists = True
        except SQLAlchemyError:
            logger.info("Column 'info' does not exist")
            info_exists = False
        
        # Add title column if it doesn't exist
        if not title_exists:
            logger.info("Adding 'title' column to uploaded_files table...")
            conn.execute(text("ALTER TABLE uploaded_files ADD COLUMN title VARCHAR"))
        
        # Add language column if it doesn't exist
        if not language_exists:
            logger.info("Adding 'language' column to uploaded_files table...")
            conn.execute(text("ALTER TABLE uploaded_files ADD COLUMN language VARCHAR"))
        
        # Add info column if it doesn't exist
        if not info_exists:
            logger.info("Adding 'info' column to uploaded_files table...")
            conn.execute(text("ALTER TABLE uploaded_files ADD COLUMN info TEXT"))
        
        # Commit the transaction
        conn.commit()
        
        logger.info("Metadata columns added successfully.")
        conn.close()
        
    except SQLAlchemyError as e:
        logger.error(f"Error adding metadata columns: {e}")
        sys.exit(1)

if __name__ == "__main__":
    add_metadata_columns()
