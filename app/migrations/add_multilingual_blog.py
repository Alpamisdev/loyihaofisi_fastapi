#!/usr/bin/env python3
import sqlite3
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_migration")

def run_migration():
    """Add multilingual support to blog tables."""
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
        
        # 1. Create blog_posts table
        logger.info("Creating blog_posts table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS blog_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            img_or_video_link VARCHAR,
            date_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            views INTEGER DEFAULT 0,
            published BOOLEAN DEFAULT 1,
            FOREIGN KEY(category_id) REFERENCES blog_categories(id)
        )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_blog_posts_category_id ON blog_posts (category_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_blog_posts_published ON blog_posts (published)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_blog_posts_date_time ON blog_posts (date_time)")
        
        # 2. Create blog_translations table
        logger.info("Creating blog_translations table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS blog_translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            language VARCHAR NOT NULL,
            title VARCHAR NOT NULL,
            intro_text TEXT,
            text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(post_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
            UNIQUE(post_id, language)
        )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_blog_translations_post_id ON blog_translations (post_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_blog_translations_language ON blog_translations (language)")
        
        # 3. Create blog_category_translations table
        logger.info("Creating blog_category_translations table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS blog_category_translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            language VARCHAR NOT NULL,
            name VARCHAR NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(category_id) REFERENCES blog_categories(id) ON DELETE CASCADE,
            UNIQUE(category_id, language)
        )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_blog_category_translations_category_id ON blog_category_translations (category_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_blog_category_translations_language ON blog_category_translations (language)")
        
        # 4. Migrate data from old blog_items table if it exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='blog_items'")
        if cursor.fetchone():
            logger.info("Migrating data from old blog_items table...")
            
            # Get all blog items
            cursor.execute("""
            SELECT id, category_id, title, img_or_video_link, date_time, views, text, intro_text
            FROM blog_items
            """)
            
            blog_items = cursor.fetchall()
            
            for item_id, category_id, title, img_or_video_link, date_time, views, text, intro_text in blog_items:
                # Insert into blog_posts
                cursor.execute("""
                INSERT INTO blog_posts (id, category_id, img_or_video_link, date_time, views, published)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    item_id,
                    category_id,
                    img_or_video_link,
                    date_time,
                    views,
                    1  # Set published to true for all existing items
                ))
                
                # Insert into blog_translations for each language
                languages = ["en", "ru", "uz", "kk"]
                for lang in languages:
                    cursor.execute("""
                    INSERT INTO blog_translations (post_id, language, title, intro_text, text, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        item_id,
                        lang,
                        title,
                        intro_text,
                        text,
                        datetime.utcnow(),
                        datetime.utcnow()
                    ))
            
            logger.info(f"Migrated {len(blog_items)} blog items to the new structure")
        
        # 5. Migrate category data
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='blog_categories'")
        if cursor.fetchone():
            logger.info("Migrating blog category data...")
            
            # Get all blog categories
            cursor.execute("SELECT id, name FROM blog_categories")
            categories = cursor.fetchall()
            
            for category_id, name in categories:
                # Insert translations for each language
                languages = ["en", "ru", "uz", "kk"]
                for lang in languages:
                    # Check if translation already exists
                    cursor.execute("""
                    SELECT id FROM blog_category_translations 
                    WHERE category_id = ? AND language = ?
                    """, (category_id, lang))
                    
                    if not cursor.fetchone():
                        cursor.execute("""
                        INSERT INTO blog_category_translations (category_id, language, name, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                        """, (
                            category_id,
                            lang,
                            name,
                            datetime.utcnow(),
                            datetime.utcnow()
                        ))
            
            logger.info(f"Added translations for {len(categories)} blog categories")
        
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
