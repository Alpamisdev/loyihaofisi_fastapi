#!/usr/bin/env python3
import os
import sys
import logging
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, create_engine, MetaData, Table, inspect
from sqlalchemy.exc import SQLAlchemyError
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("create_refresh_tokens")

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

def create_refresh_tokens_table():
    """Create the refresh_tokens table if it doesn't exist."""
    try:
        # Create a connection
        conn = engine.connect()
        
        # Create metadata object
        metadata = MetaData()
        
        # Check if table already exists
        inspector = inspect(engine)
        if 'refresh_tokens' in inspector.get_table_names():
            logger.info("refresh_tokens table already exists")
            conn.close()
            return
        
        # Define the refresh_tokens table
        refresh_tokens = Table(
            'refresh_tokens',
            metadata,
            Column('id', Integer, primary_key=True),
            Column('token', String, nullable=False, unique=True, index=True),
            Column('user_id', Integer, ForeignKey('admin_users.id'), nullable=False),
            Column('expires_at', DateTime, nullable=False),
            Column('created_at', DateTime, default=datetime.datetime.utcnow),
            Column('revoked', Boolean, default=False),
            Column('revoked_at', DateTime, nullable=True)
        )
        
        # Create the table
        logger.info("Creating refresh_tokens table...")
        refresh_tokens.create(engine)
        logger.info("refresh_tokens table created successfully")
        
        conn.close()
        
    except SQLAlchemyError as e:
        logger.error(f"Error creating refresh_tokens table: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_refresh_tokens_table()
