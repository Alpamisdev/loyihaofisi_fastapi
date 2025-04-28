from sqlalchemy.orm import Session
from . import models, auth
from .database import SessionLocal

def init_db():
    db = SessionLocal()
    try:
        # Check if admin user exists
        admin = db.query(models.AdminUser).filter(models.AdminUser.username == "admin").first()
        if not admin:
            # Create admin user
            hashed_password = auth.get_password_hash("admin")
            admin_user = models.AdminUser(
                username="admin",
                password_hash=hashed_password,
                role="admin"
            )
            db.add(admin_user)
            db.commit()
            print("Admin user created successfully.")
        else:
            print("Admin user already exists.")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
