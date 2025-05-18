#!/usr/bin/env python3
import sqlite3
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_migration")

def run_migration():
    """Add video_url column to blog_posts and news_posts tables."""
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
        
        # Begin transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Check if the column already exists in blog_posts
        cursor.execute("PRAGMA table_info(blog_posts)")
        blog_columns = cursor.fetchall()
        blog_column_names = [col[1] for col in blog_columns]
        
        if "video_url" not in blog_column_names:
            logger.info("Adding 'video_url' column to blog_posts table...")
            cursor.execute("ALTER TABLE blog_posts ADD COLUMN video_url VARCHAR")
            # Verify the column was added
            cursor.execute("PRAGMA table_info(blog_posts)")
            updated_columns = cursor.fetchall()
            updated_column_names = [col[1] for col in updated_columns]
            logger.info(f"Updated blog_posts columns: {updated_column_names}")
            logger.info("Added 'video_url' column to blog_posts table")
        else:
            logger.info("'video_url' column already exists in blog_posts table")
        
        # Check if the column already exists in news_posts
        cursor.execute("PRAGMA table_info(news_posts)")
        news_columns = cursor.fetchall()
        news_column_names = [col[1] for col in news_columns]
        
        if "video_url" not in news_column_names:
            logger.info("Adding 'video_url' column to news_posts table...")
            cursor.execute("ALTER TABLE news_posts ADD COLUMN video_url VARCHAR")
            # Verify the column was added
            cursor.execute("PRAGMA table_info(news_posts)")
            updated_columns = cursor.fetchall()
            updated_column_names = [col[1] for col in updated_columns]
            logger.info(f"Updated news_posts columns: {updated_column_names}")
            logger.info("Added 'video_url' column to news_posts table")
        else:
            logger.info("'video_url' column already exists in news_posts table")
        
        # Commit changes
        conn.commit()
        logger.info("Migration completed successfully")
        
        # Close connection
        conn.close()
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
