from fastapi import FastAPI, Depends, HTTPException, status, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import os
import logging
from datetime import datetime, timedelta

from . import models, schemas, auth
from .database import engine, get_db
from .routers import menu, blog, staff, feedback, documents, about_company, contacts, social_networks, year_name, menu_links, uploads
from .config import ACCESS_TOKEN_EXPIRE_MINUTES, ACCESS_TOKEN_EXPIRE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    allow_origins=["http://localhost:3000", "https://loyihaofisi.uz"],  # List each origin separately
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
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
app.include_router(uploads.router)  # Add the uploads router

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
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Log authentication attempt
    logger.info(f"Authentication attempt for username: {form_data.username}")
    
    # Try to authenticate with database
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    
    # If database authentication fails, try hardcoded admin credentials
    if not user and form_data.username == "admin" and form_data.password == "admin123":
        logger.info("Using hardcoded admin credentials")
        
        # Check if admin user exists in database
        admin_user = db.query(models.AdminUser).filter(models.AdminUser.username == "admin").first()
        
        if not admin_user:
            # Create admin user if it doesn't exist
            hashed_password = auth.get_password_hash("admin123")
            admin_user = models.AdminUser(
                username="admin",
                password_hash=hashed_password,
                role="admin"
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            logger.info("Created admin user in database")
        
        # Create tokens
        access_token, refresh_token, expires_in = auth.create_tokens(db, admin_user.id, admin_user.username)
        
        logger.info(f"Authentication successful for username: {form_data.username}")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token,
            "expires_in": expires_in
        }
    
    # If all authentication methods fail, raise an error
    if not user:
        logger.warning(f"Authentication failed for username: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create tokens
    access_token, refresh_token, expires_in = auth.create_tokens(db, user.id, user.username)
    
    logger.info(f"Authentication successful for username: {form_data.username}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "expires_in": expires_in
    }

# Login endpoint with hardcoded credentials
@app.post("/login", response_model=schemas.Token, tags=["authentication"])
async def login(
    username: str = Body(...),
    password: str = Body(...),
    db: Session = Depends(get_db)
):
    # Log authentication attempt
    logger.info(f"Login attempt for username: {username}")
    
    if auth.authenticate_admin(username, password):
        logger.info(f"Login successful for username: {username}")
        
        # Check if admin user exists in database
        admin_user = db.query(models.AdminUser).filter(models.AdminUser.username == "admin").first()
        
        if not admin_user:
            # Create admin user if it doesn't exist
            hashed_password = auth.get_password_hash("admin123")
            admin_user = models.AdminUser(
                username="admin",
                password_hash=hashed_password,
                role="admin"
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)
            logger.info("Created admin user in database")
        
        # Create tokens
        access_token, refresh_token, expires_in = auth.create_tokens(db, admin_user.id, admin_user.username)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token,
            "expires_in": expires_in
        }
    else:
        logger.warning(f"Login failed for username: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

@app.post("/refresh-token", response_model=schemas.Token, tags=["authentication"])
async def refresh_access_token(
    refresh_request: schemas.TokenRefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Get a new access token using a refresh token.
    
    Args:
        refresh_request: The refresh token request
        db: The database session
        
    Returns:
        A new access token and refresh token
    """
    # Get the refresh token from the database
    db_token = auth.get_refresh_token(db, refresh_request.refresh_token)
    
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get the user
    user = db.query(models.AdminUser).filter(models.AdminUser.id == db_token.user_id).first()
    
    if not user:
        # Revoke the token if the user doesn't exist
        auth.revoke_refresh_token(db, refresh_request.refresh_token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Revoke the old refresh token
    auth.revoke_refresh_token(db, refresh_request.refresh_token)
    
    # Create new tokens
    access_token, refresh_token, expires_in = auth.create_tokens(db, user.id, user.username)
    
    logger.info(f"Token refreshed for user: {user.username}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "expires_in": expires_in
    }

@app.post("/logout", status_code=status.HTTP_204_NO_CONTENT, tags=["authentication"])
async def logout(
    refresh_token: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    """
    Logout a user by revoking their refresh token.
    
    Args:
        refresh_token: The refresh token to revoke
        db: The database session
        current_user: The current user
        
    Returns:
        204 No Content
    """
    # Revoke the refresh token
    auth.revoke_refresh_token(db, refresh_token)
    
    logger.info(f"User logged out: {current_user.username}")
    
    return None

@app.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT, tags=["authentication"])
async def logout_all(
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    """
    Logout a user from all devices by revoking all their refresh tokens.
    
    Args:
        db: The database session
        current_user: The current user
        
    Returns:
        204 No Content
    """
    # Revoke all refresh tokens for the user
    count = auth.revoke_all_user_refresh_tokens(db, current_user.id)
    
    logger.info(f"User logged out from all devices: {current_user.username} (revoked {count} tokens)")
    
    return None

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
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    # Check if the current user has admin role
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    users = db.query(models.AdminUser).all()
    return users

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# Create directories for static files if they don't exist
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("static/images", exist_ok=True)
os.makedirs("static/files", exist_ok=True)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
