#!/usr/bin/env python3
import sqlite3
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_migration")

def run_migration():
    """Refactor news tables to use the new structure with NewsPost and NewsTranslation."""
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
        
        # 1. Create new tables
        logger.info("Creating new news_posts table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_url VARCHAR,
            published BOOLEAN DEFAULT 0,
            publication_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            author_id INTEGER,
            views INTEGER DEFAULT 0,
            FOREIGN KEY(author_id) REFERENCES admin_users(id)
        )
        """)
        
        logger.info("Creating new news_translations table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_translations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            language VARCHAR NOT NULL,
            title VARCHAR NOT NULL,
            content TEXT,
            summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(post_id) REFERENCES news_posts(id) ON DELETE CASCADE,
            UNIQUE(post_id, language)
        )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_news_posts_published ON news_posts (published)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_news_posts_publication_date ON news_posts (publication_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_news_translations_post_id ON news_translations (post_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_news_translations_language ON news_translations (language)")
        
        # 2. Migrate data from old tables if they exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='news'")
        if cursor.fetchone():
            logger.info("Migrating data from old news table...")
            
            # Get all news items grouped by slug
            cursor.execute("""
            SELECT slug, image_url, published, publication_date, author_id, MAX(views) as views
            FROM news
            GROUP BY slug
            """)
            
            news_groups = cursor.fetchall()
            
            for slug, image_url, published, publication_date, author_id, views in news_groups:
                # Insert into news_posts
                cursor.execute("""
                INSERT INTO news_posts (image_url, published, publication_date, author_id, views, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    image_url, 
                    published, 
                    publication_date, 
                    author_id, 
                    views, 
                    datetime.utcnow(), 
                    datetime.utcnow()
                ))
                
                post_id = cursor.lastrowid
                
                # Get all translations for this slug
                cursor.execute("""
                SELECT language, title, content, summary, created_at, updated_at
                FROM news
                WHERE slug = ?
                """, (slug,))
                
                translations = cursor.fetchall()
                
                for lang, title, content, summary, created_at, updated_at in translations:
                    # Insert into news_translations
                    cursor.execute("""
                    INSERT INTO news_translations (post_id, language, title, content, summary, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        post_id,
                        lang,
                        title,
                        content,
                        summary,
                        created_at or datetime.utcnow(),
                        updated_at or datetime.utcnow()
                    ))
        
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
