from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(
    prefix="/blog",
    tags=["blog"],
    responses={404: {"description": "Not found"}},
)

# Blog Categories
@router.post("/categories/", response_model=schemas.BlogCategory)
def create_blog_category(
    category: schemas.BlogCategoryBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_category = models.BlogCategory(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/categories/", response_model=List[schemas.BlogCategory])
def read_blog_categories(db: Session = Depends(get_db)):
    """Get all blog categories without pagination"""
    categories = db.query(models.BlogCategory).all()
    return categories

@router.get("/categories/{category_id}", response_model=schemas.BlogCategory)
def read_blog_category(category_id: int, db: Session = Depends(get_db)):
    db_category = db.query(models.BlogCategory).filter(models.BlogCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Blog category not found")
    return db_category

@router.put("/categories/{category_id}", response_model=schemas.BlogCategory)
def update_blog_category(
    category_id: int, 
    category: schemas.BlogCategoryBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_category = db.query(models.BlogCategory).filter(models.BlogCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Blog category not found")
    
    for key, value in category.dict().items():
        setattr(db_category, key, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog_category(
    category_id: int, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_category = db.query(models.BlogCategory).filter(models.BlogCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Blog category not found")
    
    db.delete(db_category)
    db.commit()
    return None

# Blog Items
@router.post("/items/", response_model=schemas.BlogItem)
def create_blog_item(
    blog_item: schemas.BlogItemBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_blog_item = models.BlogItem(**blog_item.dict())
    db.add(db_blog_item)
    db.commit()
    db.refresh(db_blog_item)
    return db_blog_item

@router.get("/items/", response_model=List[schemas.BlogItem])
def read_blog_items(db: Session = Depends(get_db)):
    """Get all blog items without pagination"""
    blog_items = db.query(models.BlogItem).all()
    return blog_items

@router.get("/items/{blog_item_id}", response_model=schemas.BlogItem)
def read_blog_item(blog_item_id: int, db: Session = Depends(get_db)):
    db_blog_item = db.query(models.BlogItem).filter(models.BlogItem.id == blog_item_id).first()
    if db_blog_item is None:
        raise HTTPException(status_code=404, detail="Blog item not found")
    
    # Increment view count
    db_blog_item.views += 1
    db.commit()
    
    return db_blog_item

@router.put("/items/{blog_item_id}", response_model=schemas.BlogItem)
def update_blog_item(
    blog_item_id: int, 
    blog_item: schemas.BlogItemBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_blog_item = db.query(models.BlogItem).filter(models.BlogItem.id == blog_item_id).first()
    if db_blog_item is None:
        raise HTTPException(status_code=404, detail="Blog item not found")
    
    for key, value in blog_item.dict().items():
        setattr(db_blog_item, key, value)
    
    db.commit()
    db.refresh(db_blog_item)
    return db_blog_item

@router.delete("/items/{blog_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog_item(
    blog_item_id: int, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_blog_item = db.query(models.BlogItem).filter(models.BlogItem.id == blog_item_id).first()
    if db_blog_item is None:
        raise HTTPException(status_code=404, detail="Blog item not found")
    
    db.delete(db_blog_item)
    db.commit()
    return None

# Get blog items by category
@router.get("/categories/{category_id}/items", response_model=List[schemas.BlogItem])
def read_blog_items_by_category(category_id: int, db: Session = Depends(get_db)):
    """Get all blog items for a specific category without pagination"""
    blog_items = db.query(models.BlogItem).filter(models.BlogItem.category_id == category_id).all()
    return blog_items
