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
app_dir = os.path.dirname(current_dir) # app
project_root = os.path.dirname(app_dir) # loyihaofis-fastapi
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
    """Add published_date column to documents_items and analytical_documents_items tables."""
    logger.info(f"Running migration from: {__file__}")
    
    try:
        with engine.connect() as conn:
            with conn.begin():
                inspector = inspect(engine)
                
                # Add to documents_items table
                if "documents_items" in inspector.get_table_names():
                    columns_documents_items = [col['name'] for col in inspector.get_columns('documents_items')]
                    if 'published_date' not in columns_documents_items:
                        logger.info("Adding 'published_date' column to documents_items table...")
                        conn.execute(text("ALTER TABLE documents_items ADD COLUMN published_date TIMESTAMP"))
                        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_documents_items_published_date ON documents_items (published_date)"))
                        logger.info("Added 'published_date' column and index to documents_items table.")
                    else:
                        logger.info("'published_date' column already exists in documents_items table.")
                else:
                    logger.warning("documents_items table not found. Skipping.")

                # Add to analytical_documents_items table
                if "analytical_documents_items" in inspector.get_table_names():
                    columns_analytical_items = [col['name'] for col in inspector.get_columns('analytical_documents_items')]
                    if 'published_date' not in columns_analytical_items:
                        logger.info("Adding 'published_date' column to analytical_documents_items table...")
                        conn.execute(text("ALTER TABLE analytical_documents_items ADD COLUMN published_date TIMESTAMP"))
                        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_analytical_documents_items_published_date ON analytical_documents_items (published_date)"))
                        logger.info("Added 'published_date' column and index to analytical_documents_items table.")
                    else:
                        logger.info("'published_date' column already exists in analytical_documents_items table.")
                else:
                    logger.warning("analytical_documents_items table not found. Skipping.")
                    
        logger.info("Migration completed successfully.")
        return True
    
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
