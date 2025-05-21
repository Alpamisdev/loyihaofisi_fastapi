#!/usr/bin/env python3
import os
import sys
import logging
import traceback
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
    """Add is_img column to news_posts, blog_posts, and blog_items tables."""
    logger.info(f"Running migration from: {__file__}")
    logger.info(f"Current working directory: {os.getcwd()}")
    
    try:
        with engine.connect() as conn:
            # Start a transaction
            with conn.begin():
                inspector = inspect(engine)
                
                # 1. Add is_img column to news_posts table
                news_columns = [col['name'] for col in inspector.get_columns('news_posts')]
                if 'is_img' not in news_columns:
                    logger.info("Adding 'is_img' column to news_posts table...")
                    conn.execute(text("ALTER TABLE news_posts ADD COLUMN is_img BOOLEAN DEFAULT FALSE"))
                    logger.info("Added 'is_img' column to news_posts table")
                else:
                    logger.info("'is_img' column already exists in news_posts table")
                
                # 2. Add is_img column to blog_posts table (new multilingual system)
                blog_posts_columns = [col['name'] for col in inspector.get_columns('blog_posts')]
                if 'is_img' not in blog_posts_columns:
                    logger.info("Adding 'is_img' column to blog_posts table...")
                    conn.execute(text("ALTER TABLE blog_posts ADD COLUMN is_img BOOLEAN DEFAULT FALSE"))
                    logger.info("Added 'is_img' column to blog_posts table")
                else:
                    logger.info("'is_img' column already exists in blog_posts table")
                
                # 3. Add is_img column to blog_items table (legacy system)
                blog_items_columns = [col['name'] for col in inspector.get_columns('blog_items')]
                if 'is_img' not in blog_items_columns:
                    logger.info("Adding 'is_img' column to blog_items table...")
                    conn.execute(text("ALTER TABLE blog_items ADD COLUMN is_img BOOLEAN DEFAULT FALSE"))
                    logger.info("Added 'is_img' column to blog_items table")
                else:
                    logger.info("'is_img' column already exists in blog_items table")
                
                # Create indexes for the new columns for better query performance
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_news_posts_is_img ON news_posts (is_img)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_blog_posts_is_img ON blog_posts (is_img)"))
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_blog_items_is_img ON blog_items (is_img)"))
                logger.info("Created indexes for is_img columns")
                
        logger.info("Migration completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
