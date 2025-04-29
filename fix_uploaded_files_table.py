#!/usr/bin/env python3
import os
import sys
import logging
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.exc import SQLAlchemyError
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fix_uploaded_files_table")

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

def fix_uploaded_files_table():
    """Fix the uploaded_files table by recreating it without metadata columns."""
    try:
        # Create a connection
        conn = engine.connect()
        
        # Begin a transaction
        trans = conn.begin()
        
        try:
            # Check if the table exists
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='uploaded_files'"))
            if result.fetchone() is None:
                logger.info("uploaded_files table does not exist, nothing to fix")
                trans.commit()
                conn.close()
                return
            
            # Get the current data from the table
            result = conn.execute(text("SELECT id, filename, original_filename, file_path, file_url, file_size, mime_type, created_at, uploaded_by FROM uploaded_files"))
            rows = result.fetchall()
            
            # Drop the existing table
            conn.execute(text("DROP TABLE uploaded_files"))
            
            # Create a new table without the metadata columns
            conn.execute(text("""
                CREATE TABLE uploaded_files (
                    id INTEGER PRIMARY KEY,
                    filename VARCHAR NOT NULL,
                    original_filename VARCHAR NOT NULL,
                    file_path VARCHAR NOT NULL,
                    file_url VARCHAR NOT NULL,
                    file_size INTEGER,
                    mime_type VARCHAR,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    uploaded_by INTEGER,
                    FOREIGN KEY(uploaded_by) REFERENCES admin_users(id)
                )
            """))
            
            # Reinsert the data
            for row in rows:
                conn.execute(
                    text("""
                        INSERT INTO uploaded_files (id, filename, original_filename, file_path, file_url, file_size, mime_type, created_at, uploaded_by)
                        VALUES (:id, :filename, :original_filename, :file_path, :file_url, :file_size, :mime_type, :created_at, :uploaded_by)
                    """),
                    {
                        "id": row[0],
                        "filename": row[1],
                        "original_filename": row[2],
                        "file_path": row[3],
                        "file_url": row[4],
                        "file_size": row[5],
                        "mime_type": row[6],
                        "created_at": row[7],
                        "uploaded_by": row[8]
                    }
                )
            
            # Commit the transaction
            trans.commit()
            logger.info("uploaded_files table fixed successfully")
            
        except SQLAlchemyError as e:
            # Rollback the transaction if an error occurs
            trans.rollback()
            logger.error(f"Error fixing uploaded_files table: {e}")
            raise
        
        finally:
            conn.close()
        
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    fix_uploaded_files_table()
