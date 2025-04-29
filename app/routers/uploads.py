import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import json
from .. import models, schemas, auth
from ..database import get_db
from ..utils.file_utils import save_upload_file, get_file_url, is_valid_image
from ..config import BASE_URL, MAX_UPLOAD_SIZE

router = APIRouter(
    prefix="/uploads",
    tags=["uploads"],
    responses={404: {"description": "Not found"}},
)

@router.post("/images/", response_model=schemas.UploadedFile)
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    folder: str = Form("images"),
    db: Session = Depends(get_db),
    current_user: Optional[models.AdminUser] = Depends(auth.get_current_user)
):
    """
    Upload an image file, convert it to WebP format, and save it to the server.
    
    Args:
        request: The request object
        file: The uploaded file
        folder: The folder to save the file in (default: "images")
        db: The database session
        current_user: The current user
        
    Returns:
        The uploaded file information
    """
    # Check if the file is an image
    if not is_valid_image(file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is not a valid image. Supported formats: JPEG, PNG, GIF, WebP, SVG, BMP, TIFF"
        )
    
    try:
        # Save the file
        success, error_msg, file_path, file_size, mime_type = await save_upload_file(
            file, folder=folder, convert_to_webp=True, max_size=MAX_UPLOAD_SIZE
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {error_msg}"
            )
        
        # Generate the file URL using the configured BASE_URL
        file_url = get_file_url(file_path)
        
        # Create a database record for the uploaded file WITHOUT metadata fields
        db_file = models.UploadedFile(
            filename=file_path.split("/")[-1],
            original_filename=file.filename,
            file_path=file_path,
            file_url=file_url,
            file_size=file_size,
            mime_type=mime_type,
            uploaded_by=current_user.id if current_user else None
        )
        
        # Remove any metadata attributes that might be set by the model
        if hasattr(db_file, 'title'):
            delattr(db_file, 'title')
        if hasattr(db_file, 'language'):
            delattr(db_file, 'language')
        if hasattr(db_file, 'info'):
            delattr(db_file, 'info')
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        return db_file
    except ValueError as e:
        if "File too large" in str(e):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum allowed size is {MAX_UPLOAD_SIZE/(1024*1024):.1f}MB"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/files/", response_model=schemas.UploadedFile)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    folder: str = Form("files"),
    db: Session = Depends(get_db),
    current_user: Optional[models.AdminUser] = Depends(auth.get_current_user)
):
    """
    Upload any file and save it to the server.
    
    Args:
        request: The request object
        file: The uploaded file
        folder: The folder to save the file in (default: "files")
        db: The database session
        current_user: The current user
        
    Returns:
        The uploaded file information
    """
    try:
        # Save the file without conversion
        success, error_msg, file_path, file_size, mime_type = await save_upload_file(
            file, folder=folder, convert_to_webp=False, max_size=MAX_UPLOAD_SIZE
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {error_msg}"
            )
        
        # Generate the file URL using the configured BASE_URL
        file_url = get_file_url(file_path)
        
        # Create a database record for the uploaded file
        db_file = models.UploadedFile(
            filename=file_path.split("/")[-1],
            original_filename=file.filename,
            file_path=file_path,
            file_url=file_url,
            file_size=file_size,
            mime_type=mime_type,
            uploaded_by=current_user.id if current_user else None
        )
        
        # Remove any metadata attributes that might be set by the model
        if hasattr(db_file, 'title'):
            delattr(db_file, 'title')
        if hasattr(db_file, 'language'):
            delattr(db_file, 'language')
        if hasattr(db_file, 'info'):
            delattr(db_file, 'info')
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        return db_file
    except ValueError as e:
        if "File too large" in str(e):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum allowed size is {MAX_UPLOAD_SIZE/(1024*1024):.1f}MB"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/", response_model=List[schemas.UploadedFile])
def get_uploaded_files(
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    """
    Get all uploaded files.
    
    Args:
        db: The database session
        current_user: The current user
        
    Returns:
        A list of uploaded files
    """
    files = db.query(models.UploadedFile).all()
    return files

@router.get("/{file_id}", response_model=schemas.UploadedFile)
def get_uploaded_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    Get an uploaded file by ID.
    
    Args:
        file_id: The file ID
        db: The database session
        
    Returns:
        The uploaded file information
    """
    db_file = db.query(models.UploadedFile).filter(models.UploadedFile.id == file_id).first()
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    return db_file

@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_uploaded_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    """
    Delete an uploaded file.
    
    Args:
        file_id: The file ID
        db: The database session
        current_user: The current user
    """
    db_file = db.query(models.UploadedFile).filter(models.UploadedFile.id == file_id).first()
    if db_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Delete the file from the server
    try:
        if os.path.exists(db_file.file_path):
            os.remove(db_file.file_path)
    except Exception as e:
        # Log the error but continue with database deletion
        print(f"Error deleting file {db_file.file_path}: {str(e)}")
    
    # Delete the database record
    db.delete(db_file)
    db.commit()
    
    return None
