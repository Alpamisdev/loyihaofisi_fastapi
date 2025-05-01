#!/usr/bin/env python3
import sqlite3
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_migration")

def update_refresh_tokens_schema():
    """Update the refresh_tokens table schema to match the model."""
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
        
        # Check if the refresh_tokens table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='refresh_tokens'")
        if not cursor.fetchone():
            logger.info("Creating refresh_tokens table")
            cursor.execute("""
            CREATE TABLE refresh_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token VARCHAR NOT NULL,
                token_hash VARCHAR,
                user_id INTEGER NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                revoked BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                device_info VARCHAR,
                ip_address VARCHAR,
                FOREIGN KEY(user_id) REFERENCES admin_users(id)
            )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX ix_refresh_tokens_user_id ON refresh_tokens (user_id)")
            cursor.execute("CREATE INDEX ix_refresh_tokens_token_hash ON refresh_tokens (token_hash)")
            cursor.execute("CREATE INDEX ix_refresh_tokens_expires_at ON refresh_tokens (expires_at)")
            cursor.execute("CREATE INDEX ix_refresh_tokens_revoked ON refresh_tokens (revoked)")
            cursor.execute("CREATE INDEX idx_token_active ON refresh_tokens (revoked, expires_at)")
            
            logger.info("Created refresh_tokens table with all required columns and indexes")
        else:
            # Check existing columns
            cursor.execute("PRAGMA table_info(refresh_tokens)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # Add token column if missing
            if "token" not in column_names:
                logger.info("Adding 'token' column to refresh_tokens table")
                cursor.execute("ALTER TABLE refresh_tokens ADD COLUMN token VARCHAR NOT NULL DEFAULT 'legacy_token'")
            
            # Add token_hash column if missing
            if "token_hash" not in column_names:
                logger.info("Adding 'token_hash' column to refresh_tokens table")
                cursor.execute("ALTER TABLE refresh_tokens ADD COLUMN token_hash VARCHAR")
                
                # Create index on token_hash
                logger.info("Creating index on 'token_hash' column")
                cursor.execute("CREATE INDEX ix_refresh_tokens_token_hash ON refresh_tokens (token_hash)")
            
            # Add device_info column if missing
            if "device_info" not in column_names:
                logger.info("Adding 'device_info' column to refresh_tokens table")
                cursor.execute("ALTER TABLE refresh_tokens ADD COLUMN device_info VARCHAR")
            
            # Add ip_address column if missing
            if "ip_address" not in column_names:
                logger.info("Adding 'ip_address' column to refresh_tokens table")
                cursor.execute("ALTER TABLE refresh_tokens ADD COLUMN ip_address VARCHAR")
            
            logger.info("Updated refresh_tokens table schema")
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logger.info("Successfully updated refresh_tokens table schema")
        return True
    
    except Exception as e:
        logger.error(f"Error updating schema: {str(e)}")
        return False

if __name__ == "__main__":
    success = update_refresh_tokens_schema()
    print(f"Migration {'successful' if success else 'failed'}")
