from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List
from .. import models, schemas, auth
from ..database import get_db
from ..config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS

router = APIRouter(
    tags=["token"],
    responses={401: {"description": "Unauthorized"}},
)

@router.post("/refresh", response_model=schemas.Token)
async def refresh_access_token(
    request: Request,
    token_data: schemas.TokenRefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Get a new access token using a refresh token.
    The old refresh token will be revoked and a new one will be issued (token rotation).
    """
    # Verify the refresh token
    db_token = auth.verify_refresh_token(db, token_data.refresh_token)
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from the token
    user = db.query(models.AdminUser).filter(models.AdminUser.id == db_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Rotate the refresh token (revoke old one and create new one)
    new_refresh_token, db_refresh_token = auth.rotate_refresh_token(
        db, db_token.id, user.id, request
    )
    
    # Create a new access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": new_refresh_token,
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
    }

@router.post("/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_refresh_token(
    token_data: schemas.TokenRevokeRequest,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    """
    Revoke a specific refresh token. 
    This is useful for logging out from a specific device.
    """
    # Verify the refresh token
    db_token = auth.verify_refresh_token(db, token_data.refresh_token)
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired refresh token"
        )
    
    # Only allow revoking own tokens unless admin
    if db_token.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to revoke this token"
        )
    
    # Revoke the token
    auth.revoke_refresh_token(db, db_token.id)
    return None

@router.post("/revoke-all", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_all_refresh_tokens(
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    """
    Revoke all refresh tokens for the current user.
    This is useful for logging out from all devices.
    """
    auth.revoke_all_user_tokens(db, current_user.id)
    return None

@router.get("/sessions", response_model=List[schemas.RefreshToken])
async def get_active_sessions(
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    """
    Get all active refresh tokens (sessions) for the current user.
    """
    active_tokens = db.query(models.RefreshToken).filter(
        models.RefreshToken.user_id == current_user.id,
        models.RefreshToken.revoked == False,
        models.RefreshToken.expires_at > timedelta(days=0)
    ).all()
    
    return active_tokens

@router.delete("/sessions/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session_by_id(
    token_id: int,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    """
    Revoke a specific session by its ID.
    """
    db_token = db.query(models.RefreshToken).filter(models.RefreshToken.id == token_id).first()
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found"
        )
    
    # Only allow revoking own tokens unless admin
    if db_token.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to revoke this token"
        )
    
    # Revoke the token
    auth.revoke_refresh_token(db, token_id)
    return None
