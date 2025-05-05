#!/usr/bin/env python3
import sqlite3
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_migration")

def run_migration():
    """Add theme column to feedback table if it doesn't exist."""
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
        cursor.execute("PRAGMA table_info(feedback)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if "theme" not in column_names:
            logger.info("Adding 'theme' column to feedback table...")
            cursor.execute("ALTER TABLE feedback ADD COLUMN theme VARCHAR")
            logger.info("Added 'theme' column to feedback table")
        else:
            logger.info("'theme' column already exists in feedback table")
        
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
