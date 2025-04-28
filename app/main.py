from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import os
from datetime import timedelta

from . import models, schemas, auth
from .database import engine, get_db
from .routers import menu, blog, staff, feedback, documents, about_company, contacts, social_networks, year_name, menu_links

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Website Backend API",
    description="Backend API for managing website content",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(menu.router)
app.include_router(blog.router)
app.include_router(staff.router)
app.include_router(feedback.router)
app.include_router(documents.router)
app.include_router(about_company.router)
app.include_router(contacts.router)
app.include_router(social_networks.router)
app.include_router(year_name.router)
app.include_router(menu_links.router)

# Root endpoint
@app.get("/", tags=["root"])
def read_root():
    return {"message": "Welcome to the Website Backend API", "version": "1.0.0"}

# Health check endpoint
@app.get("/health", tags=["health"])
def health_check():
    return {"status": "healthy"}

# Authentication endpoints
@app.post("/token", response_model=schemas.Token, tags=["authentication"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=schemas.AdminUser, tags=["users"])
async def read_users_me(current_user: models.AdminUser = Depends(auth.get_current_user)):
    return current_user

@app.post("/users/", response_model=schemas.AdminUser, tags=["users"])
async def create_user(
    user: schemas.AdminUserCreate, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    # Check if the current user has admin role
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Check if username already exists
    db_user = db.query(models.AdminUser).filter(models.AdminUser.username == user.username).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create new user
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.AdminUser(
        username=user.username,
        password_hash=hashed_password,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/", response_model=list[schemas.AdminUser], tags=["users"])
async def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    # Check if the current user has admin role
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    users = db.query(models.AdminUser).offset(skip).limit(limit).all()
    return users

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# Initialize database with admin user if it doesn't exist
@app.on_event("startup")
async def startup_db_client():
    db = next(get_db())
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

# Create a directory for static files if it doesn't exist
os.makedirs("static/uploads", exist_ok=True)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
