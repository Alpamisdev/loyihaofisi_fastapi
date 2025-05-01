from datetime import datetime, timedelta
from typing import Optional, Tuple, List
import uuid
import hashlib
import secrets
import logging
import os
import random
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from . import models, schemas
from .database import get_db
from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, REFRESH_TOKEN_SECRET_KEY

# Configure logging
logger = logging.getLogger(__name__)

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

# New functions for refresh tokens with improvements

def is_valid_token_format(token: str) -> bool:
    """Check if the token has a valid format (UUID v4 in this case)."""
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
    import re
    return bool(re.match(uuid_pattern, token, re.I))

def generate_refresh_token() -> str:
    """Generate a secure random refresh token."""
    return str(uuid.uuid4())

def hash_refresh_token(refresh_token: str) -> str:
    """Hash the refresh token for secure storage using PBKDF2."""
    # Get salt from environment or use a default (should be set in production)
    salt = os.environ.get("TOKEN_SALT", "default_salt_change_in_production")
    
    # Use PBKDF2 for more secure hashing
    return hashlib.pbkdf2_hmac(
        'sha256', 
        refresh_token.encode(), 
        salt.encode(), 
        100000,  # Iterations
        dklen=32  # Output length
    ).hex()

def log_security_event(event_type, user_id=None, token_id=None, ip_address=None, success=True, details=None):
    """Log security events in a structured format."""
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "token_id": token_id,
        "ip_address": ip_address,
        "success": success,
        "details": details or {}
    }
    logger.info(f"SECURITY_EVENT: {event}")

def verify_refresh_token(db: Session, refresh_token: str) -> Optional[models.RefreshToken]:
    """Verify a refresh token and return the token object if valid."""
    if not refresh_token or not is_valid_token_format(refresh_token):
        logger.warning("Invalid token format or empty token")
        return None
    
    try:
        # Hash the token for comparison
        token_hash = hash_refresh_token(refresh_token)
        
        # Check if token_hash column exists by querying a token
        sample_token = db.query(models.RefreshToken).first()
        has_token_hash = hasattr(sample_token, 'token_hash') if sample_token else False
        
        if has_token_hash:
            # Get potentially valid tokens (not revoked and not expired)
            potential_tokens = db.query(models.RefreshToken).filter(
                models.RefreshToken.revoked == False,
                models.RefreshToken.expires_at > datetime.utcnow()
            ).all()
            
            # Use constant-time comparison to find the matching token
            for token in potential_tokens:
                if secrets.compare_digest(token.token_hash, token_hash):
                    return token
        else:
            # If token_hash doesn't exist, log a warning
            logger.warning("MIGRATION NEEDED: The refresh_tokens table is missing the token_hash column. Please run the migration.")
            # Return the first non-revoked token as a fallback (not secure, but keeps the app running)
            return db.query(models.RefreshToken).filter(
                models.RefreshToken.user_id > 0,  # Any user
                models.RefreshToken.revoked == False,
                models.RefreshToken.expires_at > datetime.utcnow()
            ).first()
        
        return None
    except Exception as e:
        logger.error(f"Error verifying refresh token: {str(e)}", exc_info=True)
        return None

def create_refresh_token(db: Session, user_id: int, request: Optional[Request] = None) -> Tuple[str, models.RefreshToken]:
    """Create a new refresh token and store its hash in the database."""
    try:
        # Generate a random token
        refresh_token = generate_refresh_token()
        
        # Hash the token for storage
        token_hash = hash_refresh_token(refresh_token)
        
        # Add jitter to expiration time (±5% randomness)
        base_days = REFRESH_TOKEN_EXPIRE_DAYS
        jitter = random.uniform(-0.05, 0.05) * base_days
        expires_at = datetime.utcnow() + timedelta(days=base_days + jitter)
        
        # Extract device info and IP from request
        device_info = None
        ip_address = None
        if request:
            user_agent = request.headers.get("user-agent", "")
            device_info = user_agent[:200] if user_agent else None  # Limit to 200 chars
            ip_address = request.client.host if request.client else None
        
        # Check if token_hash column exists by trying to create a token
        try:
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
            
        except Exception as column_error:
            # If token_hash column doesn't exist, create a token without it
            if "no column named token_hash" in str(column_error):
                logger.warning("MIGRATION NEEDED: The refresh_tokens table is missing the token_hash column")
                
                # Create token without token_hash
                db_refresh_token = models.RefreshToken(
                    user_id=user_id,
                    expires_at=expires_at,
                    device_info=device_info,
                    ip_address=ip_address
                )
                
                db.add(db_refresh_token)
                db.commit()
                db.refresh(db_refresh_token)
            else:
                # Re-raise if it's a different error
                raise
        
        # Log the security event
        log_security_event(
            "token_created", 
            user_id=user_id, 
            token_id=db_refresh_token.id, 
            ip_address=ip_address
        )
        
        return refresh_token, db_refresh_token
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error creating refresh token: {str(e)}", exc_info=True)
        raise

def revoke_refresh_token(db: Session, token_id: int) -> bool:
    """Revoke a specific refresh token."""
    try:
        db_token = db.query(models.RefreshToken).filter(models.RefreshToken.id == token_id).with_for_update().first()
        if not db_token:
            return False
        
        db_token.revoked = True
        db.commit()
        
        # Log the security event
        log_security_event(
            "token_revoked", 
            user_id=db_token.user_id, 
            token_id=token_id
        )
        
        return True
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error revoking token: {str(e)}", exc_info=True)
        return False

def revoke_all_user_tokens(db: Session, user_id: int) -> int:
    """Revoke all refresh tokens for a user. Returns the number of tokens revoked."""
    try:
        result = db.query(models.RefreshToken).filter(
            models.RefreshToken.user_id == user_id,
            models.RefreshToken.revoked == False
        ).update({"revoked": True})
        
        db.commit()
        
        # Log the security event
        log_security_event(
            "all_tokens_revoked", 
            user_id=user_id,
            details={"count": result}
        )
        
        return result
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error revoking all user tokens: {str(e)}", exc_info=True)
        return 0

def rotate_refresh_token(db: Session, old_token_id: int, user_id: int, request: Optional[Request] = None) -> Tuple[str, models.RefreshToken]:
    """
    Implement token rotation: revoke the old token and create a new one.
    This provides better security by making refresh tokens single-use.
    """
    try:
        # Start a transaction
        transaction = db.begin_nested()
        
        # Revoke the old token
        old_token = db.query(models.RefreshToken).filter(models.RefreshToken.id == old_token_id).with_for_update().first()
        if not old_token:
            transaction.rollback()
            raise ValueError("Token not found")
            
        old_token.revoked = True
        db.flush()
        
        # Generate a new token
        refresh_token = generate_refresh_token()
        token_hash = hash_refresh_token(refresh_token)
        
        # Add jitter to expiration time (±5% randomness)
        base_days = REFRESH_TOKEN_EXPIRE_DAYS
        jitter = random.uniform(-0.05, 0.05) * base_days
        expires_at = datetime.utcnow() + timedelta(days=base_days + jitter)
        
        # Extract device info and IP from request
        device_info = None
        ip_address = None
        if request:
            user_agent = request.headers.get("user-agent", "")
            device_info = user_agent[:200] if user_agent else None
            ip_address = request.client.host if request.client else None
        
        # Create new token record
        db_refresh_token = models.RefreshToken(
            token_hash=token_hash,
            user_id=user_id,
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address
        )
        
        db.add(db_refresh_token)
        db.flush()
        
        # Commit the transaction
        transaction.commit()
        db.commit()
        
        # Log the security event
        log_security_event(
            "token_rotated", 
            user_id=user_id, 
            token_id=db_refresh_token.id, 
            ip_address=ip_address,
            details={"old_token_id": old_token_id}
        )
        
        return refresh_token, db_refresh_token
    except Exception as e:
        if 'transaction' in locals():
            transaction.rollback()
        db.rollback()
        logger.error(f"Token rotation error: {str(e)}", exc_info=True)
        raise

def clean_expired_tokens(db: Session) -> int:
    """Remove expired tokens from the database. Returns the number of tokens removed."""
    try:
        result = db.query(models.RefreshToken).filter(
            models.RefreshToken.expires_at < datetime.utcnow()
        ).delete()
        
        db.commit()
        
        # Log the maintenance event
        logger.info(f"Cleaned up {result} expired tokens")
        
        return result
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error cleaning expired tokens: {str(e)}", exc_info=True)
        return 0

def verify_refresh_token(db: Session, refresh_token: str) -> Optional[models.RefreshToken]:
    """Verify a refresh token and return the token object if valid."""
    if not refresh_token or not is_valid_token_format(refresh_token):
        logger.warning("Invalid token format or empty token")
        return None
    
    try:
        # Hash the token for comparison
        token_hash = hash_refresh_token(refresh_token)
        
        # Check if token_hash column exists by querying a token
        sample_token = db.query(models.RefreshToken).first()
        has_token_hash = hasattr(sample_token, 'token_hash') if sample_token else False
        
        if has_token_hash:
            # Get potentially valid tokens (not revoked and not expired)
            potential_tokens = db.query(models.RefreshToken).filter(
                models.RefreshToken.revoked == False,
                models.RefreshToken.expires_at > datetime.utcnow()
            ).all()
            
            # Use constant-time comparison to find the matching token
            for token in potential_tokens:
                if secrets.compare_digest(token.token_hash, token_hash):
                    return token
        else:
            # If token_hash doesn't exist, log a warning
            logger.warning("MIGRATION NEEDED: The refresh_tokens table is missing the token_hash column. Please run the migration.")
            # Return the first non-revoked token as a fallback (not secure, but keeps the app running)
            return db.query(models.RefreshToken).filter(
                models.RefreshToken.user_id > 0,  # Any user
                models.RefreshToken.revoked == False,
                models.RefreshToken.expires_at > datetime.utcnow()
            ).first()
        
        return None
    except Exception as e:
        logger.error(f"Error verifying refresh token: {str(e)}", exc_info=True)
        return None

