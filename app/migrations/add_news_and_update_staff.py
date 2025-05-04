#!/usr/bin/env python3
import sqlite3
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_migration")

def run_migration():
    """Update database schema to add news table and address column to staff."""
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
        
        # 1. Add address column to staff table
        logger.info("Adding 'address' column to staff table...")
        try:
            cursor.execute("PRAGMA table_info(staff)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            if "address" not in column_names:
                cursor.execute("ALTER TABLE staff ADD COLUMN address VARCHAR")
                logger.info("Added 'address' column to staff table")
            else:
                logger.info("'address' column already exists in staff table")
        except Exception as e:
            logger.error(f"Error adding address column: {str(e)}")
            conn.rollback()
            return False
        
        # 2. Create news table with multilingual support
        logger.info("Creating news table...")
        try:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug VARCHAR NOT NULL,
                language VARCHAR NOT NULL,
                title VARCHAR NOT NULL,
                content TEXT,
                summary TEXT,
                image_url VARCHAR,
                published BOOLEAN DEFAULT 0,
                publication_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                author_id INTEGER,
                category_id INTEGER,
                views INTEGER DEFAULT 0,
                FOREIGN KEY(author_id) REFERENCES admin_users(id),
                FOREIGN KEY(category_id) REFERENCES news_categories(id),
                UNIQUE(slug, language)
            )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_news_slug ON news (slug)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_news_language ON news (language)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_news_published ON news (published)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_news_publication_date ON news (publication_date)")
            
            logger.info("Created news table with indexes")
        except Exception as e:
            logger.error(f"Error creating news table: {str(e)}")
            conn.rollback()
            return False
        
        # 3. Create news categories table
        logger.info("Creating news categories table...")
        try:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug VARCHAR NOT NULL,
                language VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(slug, language)
            )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_news_categories_slug ON news_categories (slug)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_news_categories_language ON news_categories (language)")
            
            logger.info("Created news categories table with indexes")
        except Exception as e:
            logger.error(f"Error creating news categories table: {str(e)}")
            conn.rollback()
            return False
        
        # 4. Create news tags table
        logger.info("Creating news tags table...")
        try:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug VARCHAR NOT NULL,
                language VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(slug, language)
            )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_news_tags_slug ON news_tags (slug)")
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_news_tags_language ON news_tags (language)")
            
            logger.info("Created news tags table with indexes")
        except Exception as e:
            logger.error(f"Error creating news tags table: {str(e)}")
            conn.rollback()
            return False
        
        # 5. Create news_tags_association table (many-to-many relationship)
        logger.info("Creating news_tags_association table...")
        try:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_tags_association (
                news_id INTEGER,
                tag_id INTEGER,
                PRIMARY KEY (news_id, tag_id),
                FOREIGN KEY(news_id) REFERENCES news(id) ON DELETE CASCADE,
                FOREIGN KEY(tag_id) REFERENCES news_tags(id) ON DELETE CASCADE
            )
            """)
            
            logger.info("Created news_tags_association table")
        except Exception as e:
            logger.error(f"Error creating news_tags_association table: {str(e)}")
            conn.rollback()
            return False
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        logger.info("Migration completed successfully")
        return True
    
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_migration()
    print(f"Migration {'successful' if success else 'failed'}")
