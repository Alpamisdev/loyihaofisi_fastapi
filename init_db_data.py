#!/usr/bin/env python3
import os
import sys
import logging
from sqlalchemy.exc import SQLAlchemyError
from app.database import SessionLocal, engine
from app.models import Base, AdminUser, Menu, YearName, Contacts, SocialNetwork
from app.auth import get_password_hash

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("db_init")

def init_database():
    """Initialize the database with tables and essential data."""
    try:
        # Create tables if they don't exist
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")
    except SQLAlchemyError as e:
        logger.error(f"Error creating database tables: {e}")
        sys.exit(1)

def create_admin_user():
    """Create admin user if it doesn't exist."""
    db = SessionLocal()
    try:
        # Check if admin user exists
        admin = db.query(AdminUser).filter(AdminUser.username == "admin").first()
        if not admin:
            # Create admin user with specified password
            logger.info("Creating admin user...")
            hashed_password = get_password_hash("admin123")
            admin_user = AdminUser(
                username="admin",
                password_hash=hashed_password,
                role="admin"
            )
            db.add(admin_user)
            db.commit()
            logger.info("Admin user created successfully.")
        else:
            logger.info("Admin user already exists.")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating admin user: {e}")
    finally:
        db.close()

def create_initial_menu():
    """Create initial menu items if they don't exist."""
    db = SessionLocal()
    try:
        # Check if any menu items exist
        menu_count = db.query(Menu).count()
        if menu_count == 0:
            logger.info("Creating initial menu items...")
            
            # Create main menu items
            main_menu = Menu(name="Main Menu", icon="menu")
            about_menu = Menu(name="About", icon="info-circle")
            blog_menu = Menu(name="Blog", icon="book")
            contacts_menu = Menu(name="Contacts", icon="phone")
            
            db.add_all([main_menu, about_menu, blog_menu, contacts_menu])
            db.commit()
            logger.info("Initial menu items created successfully.")
        else:
            logger.info("Menu items already exist.")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating menu items: {e}")
    finally:
        db.close()

def create_year_name():
    """Create year name if it doesn't exist."""
    db = SessionLocal()
    try:
        # Check if year name exists
        year_name = db.query(YearName).first()
        if not year_name:
            logger.info("Creating year name...")
            year_name = YearName(
                text="2023 - Year of Progress",
                img="/static/images/year_banner.jpg"
            )
            db.add(year_name)
            db.commit()
            logger.info("Year name created successfully.")
        else:
            logger.info("Year name already exists.")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating year name: {e}")
    finally:
        db.close()

def create_contacts():
    """Create contacts if they don't exist."""
    db = SessionLocal()
    try:
        # Check if contacts exist
        contacts = db.query(Contacts).first()
        if not contacts:
            logger.info("Creating contacts...")
            contacts = Contacts(
                address="123 Main Street, City, Country",
                phone_number="+1234567890",
                email="info@example.com"
            )
            db.add(contacts)
            db.commit()
            logger.info("Contacts created successfully.")
        else:
            logger.info("Contacts already exist.")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating contacts: {e}")
    finally:
        db.close()

def create_social_networks():
    """Create social network links if they don't exist."""
    db = SessionLocal()
    try:
        # Check if any social networks exist
        social_count = db.query(SocialNetwork).count()
        if social_count == 0:
            logger.info("Creating social network links...")
            
            # Create social network links
            facebook = SocialNetwork(name="Facebook", icon="facebook", link="https://facebook.com")
            twitter = SocialNetwork(name="Twitter", icon="twitter", link="https://twitter.com")
            instagram = SocialNetwork(name="Instagram", icon="instagram", link="https://instagram.com")
            
            db.add_all([facebook, twitter, instagram])
            db.commit()
            logger.info("Social network links created successfully.")
        else:
            logger.info("Social network links already exist.")
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating social network links: {e}")
    finally:
        db.close()

def create_uploads_directory():
    """Create uploads directory if it doesn't exist."""
    try:
        os.makedirs("static/uploads", exist_ok=True)
        logger.info("Uploads directory created or already exists.")
    except Exception as e:
        logger.error(f"Error creating uploads directory: {e}")

def main():
    """Main function to initialize the database with essential data."""
    logger.info("Starting database initialization...")
    
    # Initialize database structure
    init_database()
    
    # Create essential data
    create_admin_user()
    create_initial_menu()
    create_year_name()
    create_contacts()
    create_social_networks()
    create_uploads_directory()
    
    logger.info("Database initialization completed successfully.")

if __name__ == "__main__":
    main()
