from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas, auth
from ..database import get_db
from ..utils.notifications import send_telegram_notification
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/feedback",
    tags=["feedback"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=schemas.Feedback)
async def create_feedback(
    feedback: schemas.FeedbackBase, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Create feedback record in database
    db_feedback = models.Feedback(**feedback.dict())
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    
    # Convert to dict for notification
    feedback_dict = {
        "id": db_feedback.id,
        "full_name": db_feedback.full_name,
        "phone_number": db_feedback.phone_number,
        "email": db_feedback.email,
        "text": db_feedback.text,
        "theme": db_feedback.theme,
        "created_at": db_feedback.created_at
    }
    
    # Send Telegram notification in the background
    background_tasks.add_task(send_telegram_notification, feedback_dict)
    
    return db_feedback

@router.get("/", response_model=List[schemas.Feedback])
def read_feedback(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    feedback = db.query(models.Feedback).offset(skip).limit(limit).all()
    return feedback

@router.get("/{feedback_id}", response_model=schemas.Feedback)
def read_feedback_item(
    feedback_id: int, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_feedback = db.query(models.Feedback).filter(models.Feedback.id == feedback_id).first()
    if db_feedback is None:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return db_feedback

@router.delete("/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_feedback(
    feedback_id: int, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_feedback = db.query(models.Feedback).filter(models.Feedback.id == feedback_id).first()
    if db_feedback is None:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    db.delete(db_feedback)
    db.commit()
    return None
