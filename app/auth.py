from datetime import datetime, timedelta
import uuid
from typing import Optional, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from . import models, schemas
from .database import get_db
from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

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

def create_refresh_token(db: Session, user_id: int) -> str:
    """
    Create a refresh token for a user.
    
    Args:
        db: The database session
        user_id: The user ID
        
    Returns:
        The refresh token string
    """
    # Generate a unique token
    token = str(uuid.uuid4())
    
    # Calculate expiration date (30 days)
    expires_at = datetime.utcnow() + timedelta(days=30)
    
    # Create refresh token in database
    db_token = models.RefreshToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at
    )
    
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    
    return token

def get_refresh_token(db: Session, token: str):
    """
    Get a refresh token from the database.
    
    Args:
        db: The database session
        token: The refresh token string
        
    Returns:
        The refresh token object or None if not found
    """
    return db.query(models.RefreshToken).filter(
        models.RefreshToken.token == token,
        models.RefreshToken.revoked == False,
        models.RefreshToken.expires_at > datetime.utcnow()
    ).first()

def revoke_refresh_token(db: Session, token: str):
    """
    Revoke a refresh token.
    
    Args:
        db: The database session
        token: The refresh token string
        
    Returns:
        True if the token was revoked, False otherwise
    """
    db_token = db.query(models.RefreshToken).filter(
        models.RefreshToken.token == token,
        models.RefreshToken.revoked == False
    ).first()
    
    if db_token:
        db_token.revoked = True
        db_token.revoked_at = datetime.utcnow()
        db.commit()
        return True
    
    return False

def revoke_all_user_refresh_tokens(db: Session, user_id: int):
    """
    Revoke all refresh tokens for a user.
    
    Args:
        db: The database session
        user_id: The user ID
        
    Returns:
        The number of tokens revoked
    """
    tokens = db.query(models.RefreshToken).filter(
        models.RefreshToken.user_id == user_id,
        models.RefreshToken.revoked == False
    ).all()
    
    count = 0
    for token in tokens:
        token.revoked = True
        token.revoked_at = datetime.utcnow()
        count += 1
    
    db.commit()
    return count

def create_tokens(db: Session, user_id: int, username: str) -> Tuple[str, str, int]:
    """
    Create access and refresh tokens for a user.
    
    Args:
        db: The database session
        user_id: The user ID
        username: The username
        
    Returns:
        A tuple containing the access token, refresh token, and access token expiry in seconds
    """
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token = create_refresh_token(db, user_id)
    
    # Return both tokens and expiry
    return access_token, refresh_token, int(access_token_expires.total_seconds())

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
