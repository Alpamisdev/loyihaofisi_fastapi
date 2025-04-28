from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(
    prefix="/contacts",
    tags=["contacts"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Contacts)
def create_contacts(
    contacts: schemas.ContactsBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_contacts = models.Contacts(**contacts.dict())
    db.add(db_contacts)
    db.commit()
    db.refresh(db_contacts)
    return db_contacts

@router.get("/", response_model=schemas.Contacts)
def read_contacts(db: Session = Depends(get_db)):
    db_contacts = db.query(models.Contacts).first()
    if db_contacts is None:
        raise HTTPException(status_code=404, detail="Contacts not found")
    return db_contacts

@router.put("/{contacts_id}", response_model=schemas.Contacts)
def update_contacts(
    contacts_id: int, 
    contacts: schemas.ContactsBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_contacts = db.query(models.Contacts).filter(models.Contacts.id == contacts_id).first()
    if db_contacts is None:
        raise HTTPException(status_code=404, detail="Contacts not found")
    
    for key, value in contacts.dict().items():
        setattr(db_contacts, key, value)
    
    db.commit()
    db.refresh(db_contacts)
    return db_contacts
