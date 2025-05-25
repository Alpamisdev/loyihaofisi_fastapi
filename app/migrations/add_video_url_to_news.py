#!/usr/bin/env python3
import os
import sys
import logging
from sqlalchemy import text, inspect

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_migration")

# Add the project root to sys.path to allow importing app modules
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(app_dir)
sys.path.insert(0, project_root)

try:
    from app.database import engine
    logger.info("Successfully imported app modules")
except ImportError as e:
    logger.error(f"Import error: {str(e)}")
    logger.error(f"Current sys.path: {sys.path}")
    logger.error(f"Project root: {project_root}")
    logger.error(f"Current directory: {os.getcwd()}")
    sys.exit(1)

def run_migration():
    """Add video_url column to news_posts table."""
    logger.info(f"Running migration from: {__file__}")
    logger.info(f"Current working directory: {os.getcwd()}")
    
    try:
        with engine.connect() as conn:
            # Start a transaction
            with conn.begin():
                inspector = inspect(engine)
                
                # Add video_url column to news_posts table
                news_posts_columns = [col['name'] for col in inspector.get_columns('news_posts')]
                if 'video_url' not in news_posts_columns:
                    logger.info("Adding 'video_url' column to news_posts table...")
                    conn.execute(text("ALTER TABLE news_posts ADD COLUMN video_url VARCHAR"))
                    logger.info("Added 'video_url' column to news_posts table")
                else:
                    logger.info("'video_url' column already exists in news_posts table")
                
                # Create index for the new column for better query performance
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_posts_video_url ON news_posts (video_url)"))
                logger.info("Created index for video_url column")
                
        logger.info("Migration completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
