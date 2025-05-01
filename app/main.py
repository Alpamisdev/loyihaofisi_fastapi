from fastapi import FastAPI, Depends, HTTPException, status, Body, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import os
import logging
from datetime import timedelta

from . import models, schemas, auth
from .database import engine, get_db
from .routers import menu, blog, staff, feedback, documents, about_company, contacts, social_networks, year_name, menu_links, uploads, token
from .config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000","http://localhost:3001","https://loyiha-qq.netlify.app/","https://loyihaofisi.uz","https://loyiha-qq.netlify.app"],  # List specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Length", "Content-Type"],
    max_age=600,
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
app.include_router(uploads.router)
app.include_router(token.router)  # Add the token router for refresh token operations

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
    background_tasks: BackgroundTasks,
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
        
        # Look up or create admin user in database for refresh token
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
            logger.info("Created admin user for refresh token")
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": form_data.username}, expires_delta=access_token_expires
        )
        
        # Generate refresh token
        refresh_token, db_refresh_token = auth.create_refresh_token(db, admin_user.id, request)
        
        # Log the event
        auth.log_security_event(
            "login_success_hardcoded", 
            user_id=admin_user.id,
            token_id=db_refresh_token.id,
            ip_address=request.client.host if request.client else None
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token,
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
        }
    
    # If all authentication methods fail, raise an error
    if not user:
        logger.warning(f"Authentication failed for username: {form_data.username}")
        
        # Log the failed attempt
        auth.log_security_event(
            "login_failed", 
            ip_address=request.client.host if request.client else None,
            details={"username": form_data.username}
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create and return access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Generate refresh token
    refresh_token, db_refresh_token = auth.create_refresh_token(db, user.id, request)
    
    # Log the successful login
    auth.log_security_event(
        "login_success", 
        user_id=user.id,
        token_id=db_refresh_token.id,
        ip_address=request.client.host if request.client else None
    )
    
    logger.info(f"Authentication successful for username: {form_data.username}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    }

# Login endpoint with JSON body
@app.post("/login", response_model=schemas.Token, tags=["authentication"])
async def login(
    request: Request,
    background_tasks: BackgroundTasks,
    username: str = Body(...),
    password: str = Body(...)
):
    # Log authentication attempt
    logger.info(f"Login attempt for username: {username}")
    
    # Log request details in the background
    async def log_request_details():
        client_ip = request.client.host if request.client else "unknown"
        logger.debug(f"Login request from IP: {client_ip}, User-Agent: {request.headers.get('user-agent', 'unknown')}")
    
    background_tasks.add_task(log_request_details)
    
    # Try to authenticate with database
    db = next(get_db())
    user = auth.authenticate_user(db, username, password)
    
    # If database authentication fails, try hardcoded credentials
    if not user and auth.authenticate_admin(username, password):
        logger.info(f"Login successful for username: {username} (hardcoded)")
        
        # Look up or create admin user in database for refresh token
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
            logger.info("Created admin user for refresh token")
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )
        
        # Generate refresh token
        refresh_token, db_refresh_token = auth.create_refresh_token(db, admin_user.id, request)
        
        # Log the event
        auth.log_security_event(
            "login_success_hardcoded", 
            user_id=admin_user.id,
            token_id=db_refresh_token.id,
            ip_address=request.client.host if request.client else None
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": refresh_token,
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
        }
    
    # If all authentication methods fail, raise an error
    if not user:
        logger.warning(f"Login failed for username: {username}")
        
        # Log the failed attempt
        auth.log_security_event(
            "login_failed", 
            ip_address=request.client.host if request.client else None,
            details={"username": username}
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Generate refresh token
    refresh_token, db_refresh_token = auth.create_refresh_token(db, user.id, request)
    
    # Log the successful login
    auth.log_security_event(
        "login_success", 
        user_id=user.id,
        token_id=db_refresh_token.id,
        ip_address=request.client.host if request.client else None
    )
    
    logger.info(f"Login successful for username: {username}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    }

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

# Maintenance endpoint to clean expired tokens
@app.post("/maintenance/clean-expired-tokens", tags=["maintenance"])
async def clean_expired_tokens(
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    # Only admin users can access this endpoint
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Clean expired tokens
    removed = auth.clean_expired_tokens(db)
    return {"message": f"Removed {removed} expired tokens"}

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
