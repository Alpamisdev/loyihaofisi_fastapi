from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(
    prefix="/menu-links",
    tags=["menu links"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.MenuLink)
def create_menu_link(
    menu_link: schemas.MenuLinkBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_menu_link = models.MenuLink(**menu_link.dict())
    db.add(db_menu_link)
    db.commit()
    db.refresh(db_menu_link)
    return db_menu_link

@router.get("/", response_model=List[schemas.MenuLink])
def read_menu_links(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    menu_links = db.query(models.MenuLink).offset(skip).limit(limit).all()
    return menu_links

@router.get("/{menu_link_id}", response_model=schemas.MenuLink)
def read_menu_link(menu_link_id: int, db: Session = Depends(get_db)):
    db_menu_link = db.query(models.MenuLink).filter(models.MenuLink.id == menu_link_id).first()
    if db_menu_link is None:
        raise HTTPException(status_code=404, detail="Menu link not found")
    return db_menu_link

@router.put("/{menu_link_id}", response_model=schemas.MenuLink)
def update_menu_link(
    menu_link_id: int, 
    menu_link: schemas.MenuLinkBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_menu_link = db.query(models.MenuLink).filter(models.MenuLink.id == menu_link_id).first()
    if db_menu_link is None:
        raise HTTPException(status_code=404, detail="Menu link not found")
    
    for key, value in menu_link.dict().items():
        setattr(db_menu_link, key, value)
    
    db.commit()
    db.refresh(db_menu_link)
    return db_menu_link

@router.delete("/{menu_link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu_link(
    menu_link_id: int, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_menu_link = db.query(models.MenuLink).filter(models.MenuLink.id == menu_link_id).first()
    if db_menu_link is None:
        raise HTTPException(status_code=404, detail="Menu link not found")
    
    db.delete(db_menu_link)
    db.commit()
    return None

# Get menu links by menu
@router.get("/menu/{menu_id}", response_model=List[schemas.MenuLink])
def read_menu_links_by_menu(menu_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    menu_links = db.query(models.MenuLink).filter(models.MenuLink.menu_id == menu_id).offset(skip).limit(limit).all()
    return menu_links
