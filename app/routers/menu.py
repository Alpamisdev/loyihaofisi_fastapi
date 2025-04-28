from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(
    prefix="/menu",
    tags=["menu"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Menu)
def create_menu_item(
    menu: schemas.MenuBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_menu = models.Menu(**menu.dict())
    db.add(db_menu)
    db.commit()
    db.refresh(db_menu)
    return db_menu

@router.get("/", response_model=List[schemas.Menu])
def read_menu_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    menu_items = db.query(models.Menu).offset(skip).limit(limit).all()
    return menu_items

@router.get("/{menu_id}", response_model=schemas.Menu)
def read_menu_item(menu_id: int, db: Session = Depends(get_db)):
    db_menu = db.query(models.Menu).filter(models.Menu.id == menu_id).first()
    if db_menu is None:
        raise HTTPException(status_code=404, detail="Menu item not found")
    return db_menu

@router.put("/{menu_id}", response_model=schemas.Menu)
def update_menu_item(
    menu_id: int, 
    menu: schemas.MenuBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_menu = db.query(models.Menu).filter(models.Menu.id == menu_id).first()
    if db_menu is None:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    for key, value in menu.dict().items():
        setattr(db_menu, key, value)
    
    db.commit()
    db.refresh(db_menu)
    return db_menu

@router.delete("/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu_item(
    menu_id: int, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_menu = db.query(models.Menu).filter(models.Menu.id == menu_id).first()
    if db_menu is None:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    db.delete(db_menu)
    db.commit()
    return None
