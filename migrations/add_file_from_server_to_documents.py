#!/usr/bin/env python3
import sqlite3
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_migration")

def run_migration():
    """Add file_from_server column to documents_items table."""
    try:
        # Get the database file path
        db_path = "website.db"
        
        # Check if the database file exists
        if not os.path.exists(db_path):
            logger.error(f"Database file not found: {db_path}")
            return False
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(documents_items)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if "file_from_server" not in column_names:
            logger.info("Adding 'file_from_server' column to documents_items table...")
            cursor.execute("ALTER TABLE documents_items ADD COLUMN file_from_server BOOLEAN DEFAULT 1")
            
            # Update existing records based on link
            logger.info("Updating existing records...")
            cursor.execute("""
            UPDATE documents_items 
            SET file_from_server = CASE
                WHEN link LIKE '%/static/%' OR link LIKE 'static/%' THEN 1
                ELSE 0
            END
            """)
            
            logger.info(f"Updated {cursor.rowcount} document items")
            logger.info("Added 'file_from_server' column to documents_items table")
        else:
            logger.info("'file_from_server' column already exists in documents_items table")
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logger.info("Migration completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    success = run_migration()
    print(f"Migration {'successful' if success else 'failed'}")
