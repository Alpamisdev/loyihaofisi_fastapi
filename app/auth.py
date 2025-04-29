from datetime import datetime, timedelta
from typing import Optional, Tuple, List
import uuid
import hashlib
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from . import models, schemas
from .database import get_db
from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, REFRESH_TOKEN_SECRET_KEY

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(models.AdminUser).filter(models.AdminUser.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(models.AdminUser).filter(models.AdminUser.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    
    # Update last login time
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user

# Function to authenticate with hardcoded credentials
def authenticate_admin(username: str, password: str):
    if username == "admin" and password == "admin123":
        return True
    return False

# New functions for refresh tokens

def generate_refresh_token() -> str:
    """Generate a secure random refresh token."""
    return str(uuid.uuid4())

def hash_refresh_token(refresh_token: str) -> str:
    """Hash the refresh token for secure storage."""
    return hashlib.sha256(refresh_token.encode()).hexdigest()

def create_refresh_token(db: Session, user_id: int, request: Optional[Request] = None) -> Tuple[str, models.RefreshToken]:
    """Create a new refresh token and store its hash in the database."""
    # Generate a random token
    refresh_token = generate_refresh_token()
    
    # Hash the token for storage
    token_hash = hash_refresh_token(refresh_token)
    
    # Set expiration time
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Extract device info and IP from request
    device_info = None
    ip_address = None
    if request:
        user_agent = request.headers.get("user-agent", "")
        device_info = user_agent[:200] if user_agent else None  # Limit to 200 chars
        ip_address = request.client.host if request.client else None
    
    # Store in database
    db_refresh_token = models.RefreshToken(
        token_hash=token_hash,
        user_id=user_id,
        expires_at=expires_at,
        device_info=device_info,
        ip_address=ip_address
    )
    
    db.add(db_refresh_token)
    db.commit()
    db.refresh(db_refresh_token)
    
    return refresh_token, db_refresh_token

def verify_refresh_token(db: Session, refresh_token: str) -> Optional[models.RefreshToken]:
    """Verify a refresh token and return the token object if valid."""
    if not refresh_token:
        return None
    
    # Hash the token for comparison
    token_hash = hash_refresh_token(refresh_token)
    
    # Look up the token
    db_token = db.query(models.RefreshToken).filter(
        models.RefreshToken.token_hash == token_hash,
        models.RefreshToken.revoked == False,
        models.RefreshToken.expires_at > datetime.utcnow()
    ).first()
    
    return db_token

def revoke_refresh_token(db: Session, token_id: int) -> bool:
    """Revoke a specific refresh token."""
    db_token = db.query(models.RefreshToken).filter(models.RefreshToken.id == token_id).first()
    if not db_token:
        return False
    
    db_token.revoked = True
    db.commit()
    return True

def revoke_all_user_tokens(db: Session, user_id: int) -> int:
    """Revoke all refresh tokens for a user. Returns the number of tokens revoked."""
    result = db.query(models.RefreshToken).filter(
        models.RefreshToken.user_id == user_id,
        models.RefreshToken.revoked == False
    ).update({"revoked": True})
    
    db.commit()
    return result

def rotate_refresh_token(db: Session, old_token_id: int, user_id: int, request: Optional[Request] = None) -> Tuple[str, models.RefreshToken]:
    """
    Implement token rotation: revoke the old token and create a new one.
    This provides better security by making refresh tokens single-use.
    """
    # Revoke the old token
    revoke_refresh_token(db, old_token_id)
    
    # Create a new token
    return create_refresh_token(db, user_id, request)

def clean_expired_tokens(db: Session) -> int:
    """Remove expired tokens from the database. Returns the number of tokens removed."""
    result = db.query(models.RefreshToken).filter(
        models.RefreshToken.expires_at < datetime.utcnow()
    ).delete()
    
    db.commit()
    return result
