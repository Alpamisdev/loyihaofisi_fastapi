#!/usr/bin/env python3
import sqlite3
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_migration")

def update_staff_address_nullable():
    """Update staff table to make address column nullable and set NULL for existing records."""
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
        
        # Check if the address column exists
        cursor.execute("PRAGMA table_info(staff)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if "address" not in column_names:
            logger.info("Adding 'address' column to staff table as nullable")
            cursor.execute("ALTER TABLE staff ADD COLUMN address VARCHAR")
            logger.info("Added 'address' column to staff table")
        else:
            logger.info("'address' column already exists in staff table")
        
        # Update any NULL values to ensure they're properly handled
        # SQLite doesn't support modifying column constraints directly,
        # but we can ensure all existing records have proper NULL values
        cursor.execute("UPDATE staff SET address = NULL WHERE address = '' OR address IS NULL")
        logger.info(f"Updated {cursor.rowcount} staff records to have NULL address")
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logger.info("Successfully updated staff table")
        return True
    
    except Exception as e:
        logger.error(f"Error updating staff table: {str(e)}")
        return False

if __name__ == "__main__":
    success = update_staff_address_nullable()
    print(f"Migration {'successful' if success else 'failed'}")
