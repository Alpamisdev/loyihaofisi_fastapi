from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(
    prefix="/about-company",
    tags=["about company"],
    responses={404: {"description": "Not found"}},
)

# About Company
@router.post("/", response_model=schemas.AboutCompany)
def create_about_company(
    about_company: schemas.AboutCompanyBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_about_company = models.AboutCompany(**about_company.dict())
    db.add(db_about_company)
    db.commit()
    db.refresh(db_about_company)
    return db_about_company

@router.get("/", response_model=schemas.AboutCompany)
def read_about_company(db: Session = Depends(get_db)):
    db_about_company = db.query(models.AboutCompany).first()
    if db_about_company is None:
        raise HTTPException(status_code=404, detail="About company information not found")
    
    # Increment view count
    db_about_company.views += 1
    db.commit()
    
    return db_about_company

@router.put("/{about_company_id}", response_model=schemas.AboutCompany)
def update_about_company(
    about_company_id: int, 
    about_company: schemas.AboutCompanyBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_about_company = db.query(models.AboutCompany).filter(models.AboutCompany.id == about_company_id).first()
    if db_about_company is None:
        raise HTTPException(status_code=404, detail="About company information not found")
    
    for key, value in about_company.dict().items():
        setattr(db_about_company, key, value)
    
    db.commit()
    db.refresh(db_about_company)
    return db_about_company

# About Company Categories
@router.post("/categories/", response_model=schemas.AboutCompanyCategory)
def create_about_company_category(
    category: schemas.AboutCompanyCategoryBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_category = models.AboutCompanyCategory(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/categories/", response_model=List[schemas.AboutCompanyCategory])
def read_about_company_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    categories = db.query(models.AboutCompanyCategory).offset(skip).limit(limit).all()
    return categories

@router.get("/categories/{category_id}", response_model=schemas.AboutCompanyCategory)
def read_about_company_category(category_id: int, db: Session = Depends(get_db)):
    db_category = db.query(models.AboutCompanyCategory).filter(models.AboutCompanyCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="About company category not found")
    return db_category

@router.put("/categories/{category_id}", response_model=schemas.AboutCompanyCategory)
def update_about_company_category(
    category_id: int, 
    category: schemas.AboutCompanyCategoryBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_category = db.query(models.AboutCompanyCategory).filter(models.AboutCompanyCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="About company category not found")
    
    for key, value in category.dict().items():
        setattr(db_category, key, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_about_company_category(
    category_id: int, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_category = db.query(models.AboutCompanyCategory).filter(models.AboutCompanyCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="About company category not found")
    
    db.delete(db_category)
    db.commit()
    return None

# About Company Category Items
@router.post("/category-items/", response_model=schemas.AboutCompanyCategoryItem)
def create_about_company_category_item(
    item: schemas.AboutCompanyCategoryItemBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_item = models.AboutCompanyCategoryItem(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.get("/category-items/", response_model=List[schemas.AboutCompanyCategoryItem])
def read_about_company_category_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = db.query(models.AboutCompanyCategoryItem).offset(skip).limit(limit).all()
    return items

@router.get("/category-items/{item_id}", response_model=schemas.AboutCompanyCategoryItem)
def read_about_company_category_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.AboutCompanyCategoryItem).filter(models.AboutCompanyCategoryItem.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="About company category item not found")
    
    # Increment view count
    db_item.views += 1
    db.commit()
    
    return db_item

@router.put("/category-items/{item_id}", response_model=schemas.AboutCompanyCategoryItem)
def update_about_company_category_item(
    item_id: int, 
    item: schemas.AboutCompanyCategoryItemBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_item = db.query(models.AboutCompanyCategoryItem).filter(models.AboutCompanyCategoryItem.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="About company category item not found")
    
    for key, value in item.dict().items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/category-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_about_company_category_item(
    item_id: int, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_item = db.query(models.AboutCompanyCategoryItem).filter(models.AboutCompanyCategoryItem.id == item_id).first()
    if db_item is None:
        raise HTTPException(status_code=404, detail="About company category item not found")
    
    db.delete(db_item)
    db.commit()
    return None

# Get category items by category
@router.get("/categories/{category_id}/items", response_model=List[schemas.AboutCompanyCategoryItem])
def read_about_company_category_items_by_category(category_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = db.query(models.AboutCompanyCategoryItem).filter(models.AboutCompanyCategoryItem.category_id == category_id).offset(skip).limit(limit).all()
    return items
