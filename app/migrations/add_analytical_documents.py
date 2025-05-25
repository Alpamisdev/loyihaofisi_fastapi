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
    """Add analytical documents tables to the database."""
    logger.info(f"Running migration from: {__file__}")
    logger.info(f"Current working directory: {os.getcwd()}")
    
    try:
        with engine.connect() as conn:
            # Start a transaction
            with conn.begin():
                inspector = inspect(engine)
                
                # Create analytical_documents_categories table if it doesn't exist
                if "analytical_documents_categories" not in inspector.get_table_names():
                    logger.info("Creating 'analytical_documents_categories' table...")
                    conn.execute(text("""
                        CREATE TABLE analytical_documents_categories (
                            id SERIAL PRIMARY KEY,
                            name VARCHAR NOT NULL
                        )
                    """))
                    logger.info("Created 'analytical_documents_categories' table")
                else:
                    logger.info("'analytical_documents_categories' table already exists")
                
                # Create analytical_documents_items table if it doesn't exist
                if "analytical_documents_items" not in inspector.get_table_names():
                    logger.info("Creating 'analytical_documents_items' table...")
                    conn.execute(text("""
                        CREATE TABLE analytical_documents_items (
                            id SERIAL PRIMARY KEY,
                            category_id INTEGER REFERENCES analytical_documents_categories(id),
                            title VARCHAR NOT NULL,
                            name VARCHAR,
                            link VARCHAR NOT NULL,
                            is_from_server BOOLEAN DEFAULT FALSE,
                            status VARCHAR DEFAULT 'active',
                            document_type VARCHAR,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    logger.info("Created 'analytical_documents_items' table")
                    
                    # Create indexes for better query performance
                    conn.execute(text("CREATE INDEX idx_analytical_documents_items_category_id ON analytical_documents_items (category_id)"))
                    conn.execute(text("CREATE INDEX idx_analytical_documents_items_is_from_server ON analytical_documents_items (is_from_server)"))
                    conn.execute(text("CREATE INDEX idx_analytical_documents_items_status ON analytical_documents_items (status)"))
                    conn.execute(text("CREATE INDEX idx_analytical_documents_items_document_type ON analytical_documents_items (document_type)"))
                    conn.execute(text("CREATE INDEX idx_analytical_documents_items_created_at ON analytical_documents_items (created_at)"))
                    logger.info("Created indexes for 'analytical_documents_items' table")
                else:
                    logger.info("'analytical_documents_items' table already exists")
                    
                    # Check if document_type column exists in analytical_documents_items table
                    columns = [col['name'] for col in inspector.get_columns('analytical_documents_items')]
                    if 'document_type' not in columns:
                        logger.info("Adding 'document_type' column to analytical_documents_items table...")
                        conn.execute(text("ALTER TABLE analytical_documents_items ADD COLUMN document_type VARCHAR"))
                        conn.execute(text("CREATE INDEX idx_analytical_documents_items_document_type ON analytical_documents_items (document_type)"))
                        logger.info("Added 'document_type' column to analytical_documents_items table")
                    else:
                        logger.info("'document_type' column already exists in analytical_documents_items table")
                
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
