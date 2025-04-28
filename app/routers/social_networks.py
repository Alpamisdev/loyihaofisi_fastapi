from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, auth
from ..database import get_db

router = APIRouter(
    prefix="/social-networks",
    tags=["social networks"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.SocialNetwork)
def create_social_network(
    social_network: schemas.SocialNetworkBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_social_network = models.SocialNetwork(**social_network.dict())
    db.add(db_social_network)
    db.commit()
    db.refresh(db_social_network)
    return db_social_network

@router.get("/", response_model=List[schemas.SocialNetwork])
def read_social_networks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    social_networks = db.query(models.SocialNetwork).offset(skip).limit(limit).all()
    return social_networks

@router.get("/{social_network_id}", response_model=schemas.SocialNetwork)
def read_social_network(social_network_id: int, db: Session = Depends(get_db)):
    db_social_network = db.query(models.SocialNetwork).filter(models.SocialNetwork.id == social_network_id).first()
    if db_social_network is None:
        raise HTTPException(status_code=404, detail="Social network not found")
    return db_social_network

@router.put("/{social_network_id}", response_model=schemas.SocialNetwork)
def update_social_network(
    social_network_id: int, 
    social_network: schemas.SocialNetworkBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_social_network = db.query(models.SocialNetwork).filter(models.SocialNetwork.id == social_network_id).first()
    if db_social_network is None:
        raise HTTPException(status_code=404, detail="Social network not found")
    
    for key, value in social_network.dict().items():
        setattr(db_social_network, key, value)
    
    db.commit()
    db.refresh(db_social_network)
    return db_social_network

@router.delete("/{social_network_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_social_network(
    social_network_id: int, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_social_network = db.query(models.SocialNetwork).filter(models.SocialNetwork.id == social_network_id).first()
    if db_social_network is None:
        raise HTTPException(status_code=404, detail="Social network not found")
    
    db.delete(db_social_network)
    db.commit()
    return None
