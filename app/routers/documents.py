from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import shutil
from datetime import datetime
import httpx
from urllib.parse import urlparse
import logging
from .. import models, schemas, auth
from ..database import get_db
from ..utils.file_utils import save_upload_file, get_file_url

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={404: {"description": "Not found"}},
)

# Document Categories
@router.post("/categories/", response_model=schemas.DocumentCategory)
def create_document_category(
    category: schemas.DocumentCategoryBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_category = models.DocumentCategory(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/categories/", response_model=List[schemas.DocumentCategory])
def read_document_categories(db: Session = Depends(get_db)):
    """Get all document categories without pagination"""
    categories = db.query(models.DocumentCategory).all()
    return categories

@router.get("/categories/{category_id}", response_model=schemas.DocumentCategory)
def read_document_category(category_id: int, db: Session = Depends(get_db)):
    db_category = db.query(models.DocumentCategory).filter(models.DocumentCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Document category not found")
    return db_category

@router.put("/categories/{category_id}", response_model=schemas.DocumentCategory)
def update_document_category(
    category_id: int, 
    category: schemas.DocumentCategoryBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_category = db.query(models.DocumentCategory).filter(models.DocumentCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Document category not found")
    
    for key, value in category.dict().items():
        setattr(db_category, key, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_category(
    category_id: int, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_category = db.query(models.DocumentCategory).filter(models.DocumentCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Document category not found")
    
    db.delete(db_category)
    db.commit()
    return None

# Document Items
@router.post("/items/", response_model=schemas.DocumentItem)
async def create_document_item(
    background_tasks: BackgroundTasks,
    category_id: int = Form(...),
    title: str = Form(...),
    name: Optional[str] = Form(None),
    link: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    file_url: Optional[str] = Form(None),  # New parameter for already uploaded file URL
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    """
    Create a document item. You can provide one of the following:
    - A link to an external document
    - Upload a file directly
    - Provide a URL to an already uploaded file
    """
    # Check if category exists
    db_category = db.query(models.DocumentCategory).filter(models.DocumentCategory.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Document category not found")
    
    # Check if at least one of link, file, or file_url is provided
    if not link and not file and not file_url:
        raise HTTPException(status_code=400, detail="Either link, file, or file_url must be provided")
    
    # If multiple options are provided, prioritize in this order: file, file_url, link
    final_link = None
    
    # If file is uploaded, save it and generate a link
    if file:
        # Create documents directory if it doesn't exist
        os.makedirs("static/documents", exist_ok=True)
        
        # Save the file
        success, error_msg, file_path, file_size, mime_type = await save_upload_file(
            file, folder="documents", convert_to_webp=False
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {error_msg}")
        
        # Generate file URL
        file_url = get_file_url(file_path)
        
        # Use the original filename if name is not provided
        if not name:
            name = file.filename
        
        # Set the link to the file URL
        final_link = file_url
        
        # Create uploaded file record
        db_file = models.UploadedFile(
            filename=os.path.basename(file_path),
            original_filename=file.filename,
            file_path=file_path,
            file_url=file_url,
            file_size=file_size,
            mime_type=mime_type,
            uploaded_by=current_user.id
        )
        db.add(db_file)
    
    # If file_url is provided (URL to already uploaded file)
    elif file_url:
        # Validate the URL
        try:
            parsed_url = urlparse(file_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise HTTPException(status_code=400, detail="Invalid file URL format")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid file URL")
        
        # Use the provided URL directly
        final_link = file_url
        
        # Extract filename from URL for name if not provided
        if not name:
            name = os.path.basename(parsed_url.path)
    
    # If link is provided (external link)
    elif link:
        # Validate the URL
        try:
            parsed_url = urlparse(link)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise HTTPException(status_code=400, detail="Invalid link format")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid link")
        
        # Use the provided link directly
        final_link = link
        
        # Extract filename from URL for name if not provided
        if not name:
            name = os.path.basename(parsed_url.path)
    
    # Create document item
    db_document_item = models.DocumentItem(
        category_id=category_id,
        title=title,
        name=name,
        link=final_link
    )
    db.add(db_document_item)
    db.commit()
    db.refresh(db_document_item)
    
    return db_document_item

@router.get("/items/", response_model=List[schemas.DocumentItem])
def read_document_items(db: Session = Depends(get_db)):
    """Get all document items without pagination"""
    document_items = db.query(models.DocumentItem).all()
    return document_items

@router.get("/items/{document_item_id}", response_model=schemas.DocumentItem)
def read_document_item(document_item_id: int, db: Session = Depends(get_db)):
    db_document_item = db.query(models.DocumentItem).filter(models.DocumentItem.id == document_item_id).first()
    if db_document_item is None:
        raise HTTPException(status_code=404, detail="Document item not found")
    return db_document_item

@router.get("/download/{document_item_id}")
async def download_document(document_item_id: int, db: Session = Depends(get_db)):
    """Download a document file or return information about external URL"""
    db_document_item = db.query(models.DocumentItem).filter(models.DocumentItem.id == document_item_id).first()
    if db_document_item is None:
        raise HTTPException(status_code=404, detail="Document item not found")
    
    if not db_document_item.link:
        raise HTTPException(status_code=404, detail="Document has no associated file or link")
    
    # Check if the document is a local file
    if db_document_item.link and (db_document_item.link.startswith(("/static/", "static/")) or 
                                  "/static/" in db_document_item.link):
        # Convert to local file path
        file_path = db_document_item.link
        if file_path.startswith("/static/"):
            file_path = file_path[1:]  # Remove leading slash
        elif "/static/" in file_path:
            # Handle full URLs to static files on the same server
            file_path = file_path.split("/static/")[1]
            file_path = f"static/{file_path}"
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Document file not found")
        
        # Ensure filename has an extension
        filename = db_document_item.name or os.path.basename(file_path)
        
        # If the document name doesn't have an extension, extract it from the file path
        if '.' not in filename and '.' in file_path:
            file_extension = os.path.splitext(file_path)[1]  # Get extension with dot
            if file_extension:
                # If filename already has extension, use it as is
                if not filename.endswith(file_extension):
                    filename = f"{filename}{file_extension}"
        
        logger.info(f"Serving file: {file_path} with filename: {filename}")
        
        # Return file for download with proper filename including extension
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream"
        )
    else:
        # For external links, return the URL instead of redirecting
        # This avoids CORS issues
        return {
            "document_id": db_document_item.id,
            "title": db_document_item.title,
            "name": db_document_item.name,
            "is_external": True,
            "url": db_document_item.link,
            "message": "This is an external document. Use the URL to access it."
        }

@router.put("/items/{document_item_id}", response_model=schemas.DocumentItem)
async def update_document_item(
    document_item_id: int,
    background_tasks: BackgroundTasks,
    category_id: Optional[int] = Form(None),
    title: Optional[str] = Form(None),
    name: Optional[str] = Form(None),
    link: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    file_url: Optional[str] = Form(None),  # New parameter for already uploaded file URL
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_document_item = db.query(models.DocumentItem).filter(models.DocumentItem.id == document_item_id).first()
    if db_document_item is None:
        raise HTTPException(status_code=404, detail="Document item not found")
    
    # Update category if provided
    if category_id is not None:
        db_category = db.query(models.DocumentCategory).filter(models.DocumentCategory.id == category_id).first()
        if not db_category:
            raise HTTPException(status_code=404, detail="Document category not found")
        db_document_item.category_id = category_id
    
    # Update title if provided
    if title is not None:
        db_document_item.title = title
    
    # Update name if provided
    if name is not None:
        db_document_item.name = name
    
    # If file is uploaded, save it and update the link
    if file:
        # Create documents directory if it doesn't exist
        os.makedirs("static/documents", exist_ok=True)
        
        # Save the file
        success, error_msg, file_path, file_size, mime_type = await save_upload_file(
            file, folder="documents", convert_to_webp=False
        )
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to save file: {error_msg}")
        
        # Generate file URL
        file_url = get_file_url(file_path)
        
        # Update the link to the file URL
        db_document_item.link = file_url
        
        # Create uploaded file record
        db_file = models.UploadedFile(
            filename=os.path.basename(file_path),
            original_filename=file.filename,
            file_path=file_path,
            file_url=file_url,
            file_size=file_size,
            mime_type=mime_type,
            uploaded_by=current_user.id
        )
        db.add(db_file)
    
    # If file_url is provided (URL to already uploaded file)
    elif file_url:
        # Validate the URL
        try:
            parsed_url = urlparse(file_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise HTTPException(status_code=400, detail="Invalid file URL format")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid file URL")
        
        # Update the link to the provided URL
        db_document_item.link = file_url
    
    # Update link if provided and no file is uploaded
    elif link is not None:
        db_document_item.link = link
    
    db.commit()
    db.refresh(db_document_item)
    
    return db_document_item

@router.delete("/items/{document_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document_item(
    document_item_id: int, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_document_item = db.query(models.DocumentItem).filter(models.DocumentItem.id == document_item_id).first()
    if db_document_item is None:
        raise HTTPException(status_code=404, detail="Document item not found")
    
    # If the document is a local file, delete it
    if db_document_item.link and db_document_item.link.startswith(("/static/", "static/")):
        file_path = db_document_item.link
        if file_path.startswith("/static/"):
            file_path = file_path[1:]  # Remove leading slash
        
        # Try to delete the file, but don't fail if it doesn't exist
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            # Log the error but continue with database deletion
            logger.error(f"Error deleting file {file_path}: {str(e)}")
    
    db.delete(db_document_item)
    db.commit()
    return None

# Get document items by category
@router.get("/categories/{category_id}/items", response_model=List[schemas.DocumentItem])
def read_document_items_by_category(category_id: int, db: Session = Depends(get_db)):
    """Get all document items for a specific category without pagination"""
    document_items = db.query(models.DocumentItem).filter(models.DocumentItem.category_id == category_id).all()
    return document_items
