#!/usr/bin/env python3
import sqlite3
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_migration")

def add_token_hash_column():
    """Add token_hash column to refresh_tokens table using direct SQLite connection."""
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
        cursor.execute("PRAGMA table_info(refresh_tokens)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if "token_hash" in column_names:
            logger.info("Column 'token_hash' already exists in refresh_tokens table")
            conn.close()
            return True
        
        # Add the column
        logger.info("Adding 'token_hash' column to refresh_tokens table")
        cursor.execute("ALTER TABLE refresh_tokens ADD COLUMN token_hash VARCHAR")
        
        # Create index
        logger.info("Creating index on 'token_hash' column")
        cursor.execute("CREATE INDEX ix_refresh_tokens_token_hash ON refresh_tokens (token_hash)")
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logger.info("Successfully added 'token_hash' column to refresh_tokens table")
        return True
    
    except Exception as e:
        logger.error(f"Error adding column: {str(e)}")
        return False

if __name__ == "__main__":
    success = add_token_hash_column()
    print(f"Migration {'successful' if success else 'failed'}")
