import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List, Dict, Any
from .. import models, schemas, auth
from ..database import get_db
from ..config import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["token"],
    responses={401: {"description": "Unauthorized"}},
)

# Helper function to log request details
async def log_request_details(request: Request) -> Dict[str, Any]:
    headers = dict(request.headers)
    # Remove sensitive headers
    if "authorization" in headers:
        headers["authorization"] = "REDACTED"
    
    client_ip = request.client.host if request.client else "unknown"
    
    details = {
        "method": request.method,
        "url": str(request.url),
        "client_ip": client_ip,
        "user_agent": headers.get("user-agent", "unknown")
    }
    
    logger.debug(f"Token request details: {details}")
    return details

@router.post("/refresh", response_model=schemas.Token)
async def refresh_access_token(
    request: Request,
    background_tasks: BackgroundTasks,
    token_data: schemas.TokenRefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Get a new access token using a refresh token.
    The old refresh token will be revoked and a new one will be issued (token rotation).
    """
    # Log request details in the background
    background_tasks.add_task(log_request_details, request)
    
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        # Validate token format
        if not auth.is_valid_token_format(token_data.refresh_token):
            auth.log_security_event(
                "token_refresh_failed", 
                ip_address=client_ip, 
                success=False, 
                details={"reason": "invalid_token_format"}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "invalid_token_format",
                    "message": "The refresh token format is invalid"
                }
            )
        
        # Verify the refresh token
        db_token = auth.verify_refresh_token(db, token_data.refresh_token)
        if not db_token:
            auth.log_security_event(
                "token_refresh_failed", 
                ip_address=client_ip, 
                success=False, 
                details={"reason": "invalid_or_expired_token"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "invalid_token",
                    "message": "Invalid or expired refresh token"
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from the token
        user = db.query(models.AdminUser).filter(models.AdminUser.id == db_token.user_id).first()
        if not user:
            auth.log_security_event(
                "token_refresh_failed", 
                token_id=db_token.id,
                ip_address=client_ip, 
                success=False, 
                details={"reason": "user_not_found"}
            )
            # Revoke the token since the user doesn't exist
            auth.revoke_refresh_token(db, db_token.id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "user_not_found",
                    "message": "User associated with token not found"
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Rotate the refresh token (revoke old one and create new one)
        try:
            new_refresh_token, db_refresh_token = auth.rotate_refresh_token(
                db, db_token.id, user.id, request
            )
        except Exception as e:
            logger.error(f"Token rotation error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "token_rotation_error",
                    "message": "Failed to rotate refresh token"
                }
            )
        
        # Create a new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        auth.log_security_event(
            "token_refresh_success", 
            user_id=user.id, 
            token_id=db_refresh_token.id, 
            ip_address=client_ip
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "refresh_token": new_refresh_token,
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Convert to seconds
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {str(e)}", exc_info=True)
        auth.log_security_event(
            "token_refresh_error", 
            ip_address=client_ip, 
            success=False, 
            details={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "server_error",
                "message": "An unexpected error occurred"
            }
        )

@router.post("/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_refresh_token(
    request: Request,
    background_tasks: BackgroundTasks,
    token_data: schemas.TokenRevokeRequest,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    """
    Revoke a specific refresh token. 
    This is useful for logging out from a specific device.
    """
    # Log request details in the background
    background_tasks.add_task(log_request_details, request)
    
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        # Validate token format
        if not auth.is_valid_token_format(token_data.refresh_token):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "invalid_token_format",
                    "message": "The refresh token format is invalid"
                }
            )
        
        # Verify the refresh token
        db_token = auth.verify_refresh_token(db, token_data.refresh_token)
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "invalid_token",
                    "message": "Invalid or expired refresh token"
                }
            )
        
        # Only allow revoking own tokens unless admin
        if db_token.user_id != current_user.id and current_user.role != "admin":
            auth.log_security_event(
                "token_revoke_unauthorized", 
                user_id=current_user.id,
                token_id=db_token.id,
                ip_address=client_ip, 
                success=False
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "insufficient_permissions",
                    "message": "Not enough permissions to revoke this token"
                }
            )
        
        # Revoke the token
        success = auth.revoke_refresh_token(db, db_token.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "revocation_failed",
                    "message": "Failed to revoke token"
                }
            )
        
        auth.log_security_event(
            "token_revoked_manually", 
            user_id=current_user.id,
            token_id=db_token.id,
            ip_address=client_ip
        )
        
        return None
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token revocation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "server_error",
                "message": "An unexpected error occurred"
            }
        )

@router.post("/revoke-all", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_all_refresh_tokens(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    """
    Revoke all refresh tokens for the current user.
    This is useful for logging out from all devices.
    """
    # Log request details in the background
    background_tasks.add_task(log_request_details, request)
    
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        count = auth.revoke_all_user_tokens(db, current_user.id)
        
        auth.log_security_event(
            "all_tokens_revoked_manually", 
            user_id=current_user.id,
            ip_address=client_ip,
            details={"count": count}
        )
        
        return None
    except Exception as e:
        logger.error(f"Unexpected error during all token revocation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "server_error",
                "message": "An unexpected error occurred"
            }
        )

@router.get("/sessions", response_model=List[schemas.RefreshToken])
async def get_active_sessions(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    """
    Get all active refresh tokens (sessions) for the current user.
    """
    # Log request details in the background
    background_tasks.add_task(log_request_details, request)
    
    try:
        active_tokens = db.query(models.RefreshToken).filter(
            models.RefreshToken.user_id == current_user.id,
            models.RefreshToken.revoked == False,
            models.RefreshToken.expires_at > timedelta(days=0)
        ).all()
        
        return active_tokens
    except Exception as e:
        logger.error(f"Error retrieving active sessions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "server_error",
                "message": "Failed to retrieve active sessions"
            }
        )

@router.delete("/sessions/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_session_by_id(
    token_id: int,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    """
    Revoke a specific session by its ID.
    """
    # Log request details in the background
    background_tasks.add_task(log_request_details, request)
    
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        db_token = db.query(models.RefreshToken).filter(models.RefreshToken.id == token_id).first()
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "token_not_found",
                    "message": "Token not found"
                }
            )
        
        # Only allow revoking own tokens unless admin
        if db_token.user_id != current_user.id and current_user.role != "admin":
            auth.log_security_event(
                "session_revoke_unauthorized", 
                user_id=current_user.id,
                token_id=token_id,
                ip_address=client_ip, 
                success=False
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "insufficient_permissions",
                    "message": "Not enough permissions to revoke this session"
                }
            )
        
        # Revoke the token
        success = auth.revoke_refresh_token(db, token_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "revocation_failed",
                    "message": "Failed to revoke session"
                }
            )
        
        auth.log_security_event(
            "session_revoked", 
            user_id=current_user.id,
            token_id=token_id,
            ip_address=client_ip
        )
        
        return None
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error during session revocation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "server_error",
                "message": "An unexpected error occurred"
            }
        )
