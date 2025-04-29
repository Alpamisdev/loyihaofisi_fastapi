#!/usr/bin/env python3
import logging
from sqlalchemy.exc import SQLAlchemyError
from app.database import SessionLocal
from app.models import AdminUser
from app.auth import get_password_hash, verify_password

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("check_admin")

def check_admin_user():
    """Check if admin user exists and has the correct password."""
    db = SessionLocal()
    try:
        # Check if admin user exists
        admin = db.query(AdminUser).filter(AdminUser.username == "admin").first()
        
        if not admin:
            logger.info("Admin user does not exist. Creating...")
            # Create admin user
            hashed_password = get_password_hash("admin123")
            admin_user = AdminUser(
                username="admin",
                password_hash=hashed_password,
                role="admin"
            )
            db.add(admin_user)
            db.commit()
            logger.info("Admin user created successfully.")
            return
        
        # Check if password is correct
        if not verify_password("admin123", admin.password_hash):
            logger.info("Admin password is incorrect. Updating...")
            # Update admin password
            admin.password_hash = get_password_hash("admin123")
            db.commit()
            logger.info("Admin password updated successfully.")
        else:
            logger.info("Admin user exists with correct password.")
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_admin_user()
