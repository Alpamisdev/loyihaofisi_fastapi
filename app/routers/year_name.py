from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(
    prefix="/year-name",
    tags=["year name"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.YearName)
def create_year_name(
    year_name: schemas.YearNameBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_year_name = models.YearName(**year_name.dict())
    db.add(db_year_name)
    db.commit()
    db.refresh(db_year_name)
    return db_year_name

@router.get("/", response_model=schemas.YearName)
def read_year_name(db: Session = Depends(get_db)):
    db_year_name = db.query(models.YearName).first()
    if db_year_name is None:
        raise HTTPException(status_code=404, detail="Year name not found")
    return db_year_name

@router.put("/{year_name_id}", response_model=schemas.YearName)
def update_year_name(
    year_name_id: int, 
    year_name: schemas.YearNameBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_year_name = db.query(models.YearName).filter(models.YearName.id == year_name_id).first()
    if db_year_name is None:
        raise HTTPException(status_code=404, detail="Year name not found")
    
    for key, value in year_name.dict().items():
        setattr(db_year_name, key, value)
    
    db.commit()
    db.refresh(db_year_name)
    return db_year_name
