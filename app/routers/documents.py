from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, auth
from ..database import get_db

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
def read_document_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    categories = db.query(models.DocumentCategory).offset(skip).limit(limit).all()
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
def create_document_item(
    document_item: schemas.DocumentItemBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_document_item = models.DocumentItem(**document_item.dict())
    db.add(db_document_item)
    db.commit()
    db.refresh(db_document_item)
    return db_document_item

@router.get("/items/", response_model=List[schemas.DocumentItem])
def read_document_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    document_items = db.query(models.DocumentItem).offset(skip).limit(limit).all()
    return document_items

@router.get("/items/{document_item_id}", response_model=schemas.DocumentItem)
def read_document_item(document_item_id: int, db: Session = Depends(get_db)):
    db_document_item = db.query(models.DocumentItem).filter(models.DocumentItem.id == document_item_id).first()
    if db_document_item is None:
        raise HTTPException(status_code=404, detail="Document item not found")
    return db_document_item

@router.put("/items/{document_item_id}", response_model=schemas.DocumentItem)
def update_document_item(
    document_item_id: int, 
    document_item: schemas.DocumentItemBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_document_item = db.query(models.DocumentItem).filter(models.DocumentItem.id == document_item_id).first()
    if db_document_item is None:
        raise HTTPException(status_code=404, detail="Document item not found")
    
    for key, value in document_item.dict().items():
        setattr(db_document_item, key, value)
    
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
    
    db.delete(db_document_item)
    db.commit()
    return None

# Get document items by category
@router.get("/categories/{category_id}/items", response_model=List[schemas.DocumentItem])
def read_document_items_by_category(category_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    document_items = db.query(models.DocumentItem).filter(models.DocumentItem.category_id == category_id).offset(skip).limit(limit).all()
    return document_items
