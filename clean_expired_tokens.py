#!/usr/bin/env python3
import logging
from sqlalchemy.exc import SQLAlchemyError
from app.database import SessionLocal
from app.auth import clean_expired_tokens

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("token_cleanup")

def cleanup_tokens():
    """Remove expired refresh tokens from the database."""
    db = SessionLocal()
    try:
        # Clean up expired tokens
        removed_count = clean_expired_tokens(db)
        logger.info(f"Removed {removed_count} expired refresh tokens.")
    except SQLAlchemyError as e:
        logger.error(f"Database error during token cleanup: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_tokens()
