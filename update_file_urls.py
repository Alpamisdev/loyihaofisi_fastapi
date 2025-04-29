#!/usr/bin/env python3
import logging
from sqlalchemy.exc import SQLAlchemyError
from app.database import SessionLocal
from app.models import UploadedFile
from app.config import BASE_URL

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("update_file_urls")

def update_file_urls():
    """Update file URLs in the database to use the configured BASE_URL."""
    if not BASE_URL:
        logger.warning("BASE_URL is not configured. Skipping URL updates.")
        return
    
    db = SessionLocal()
    try:
        # Get all uploaded files
        files = db.query(UploadedFile).all()
        
        updated_count = 0
        for file in files:
            if file.file_path.startswith("static/"):
                # Remove 'static/' from the beginning of the path
                url_path = file.file_path[7:]
                
                # Generate new URL with the configured BASE_URL
                if BASE_URL.endswith('/'):
                    new_url = f"{BASE_URL}static/{url_path}"
                else:
                    new_url = f"{BASE_URL}/static/{url_path}"
                
                # Update the file URL if it's different
                if file.file_url != new_url:
                    file.file_url = new_url
                    updated_count += 1
        
        if updated_count > 0:
            db.commit()
            logger.info(f"Updated {updated_count} file URLs.")
        else:
            logger.info("No file URLs needed updating.")
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_file_urls()
