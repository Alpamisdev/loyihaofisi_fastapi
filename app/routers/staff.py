from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(
    prefix="/staff",
    tags=["staff"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Staff)
def create_staff_member(
    staff: schemas.StaffBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_staff = models.Staff(**staff.dict())
    db.add(db_staff)
    db.commit()
    db.refresh(db_staff)
    return db_staff

@router.get("/", response_model=List[schemas.Staff])
def read_staff_members(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    staff = db.query(models.Staff).offset(skip).limit(limit).all()
    return staff

@router.get("/{staff_id}", response_model=schemas.Staff)
def read_staff_member(staff_id: int, db: Session = Depends(get_db)):
    db_staff = db.query(models.Staff).filter(models.Staff.id == staff_id).first()
    if db_staff is None:
        raise HTTPException(status_code=404, detail="Staff member not found")
    return db_staff

@router.put("/{staff_id}", response_model=schemas.Staff)
def update_staff_member(
    staff_id: int, 
    staff: schemas.StaffBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_staff = db.query(models.Staff).filter(models.Staff.id == staff_id).first()
    if db_staff is None:
        raise HTTPException(status_code=404, detail="Staff member not found")
    
    for key, value in staff.dict().items():
        setattr(db_staff, key, value)
    
    db.commit()
    db.refresh(db_staff)
    return db_staff

@router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_staff_member(
    staff_id: int, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_staff = db.query(models.Staff).filter(models.Staff.id == staff_id).first()
    if db_staff is None:
        raise HTTPException(status_code=404, detail="Staff member not found")
    
    db.delete(db_staff)
    db.commit()
    return None
