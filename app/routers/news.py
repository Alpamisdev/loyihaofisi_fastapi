from fastapi import APIRouter, Depends, HTTPException, status, Path, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional, Dict
from datetime import datetime
import logging
from .. import models, schemas, auth
from ..database import get_db
from slugify import slugify

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/news",
    tags=["news"],
    responses={404: {"description": "Not found"}},
)

# Helper function to validate language
def validate_language(language: str) -> str:
    valid_languages = ["en", "ru", "uz", "kk"]
    if language not in valid_languages:
        raise ValueError(f"Invalid language: {language}. Must be one of {valid_languages}")
    return language

# Single endpoint for creating multilingual news posts
@router.post("/", response_model=schemas.NewsPostDetail)
async def create_news(
    news: schemas.MultilingualNewsCreate,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    """
    Create a news post with content in all supported languages (English, Russian, Uzbek, and Karakalpak).
    """
    # Set publication date if published and not provided
    if news.published and not news.publication_date:
        news.publication_date = datetime.utcnow()
        
    # Create the news post
    db_news_post = models.NewsPost(
        image_url=news.image_url,
        published=news.published,
        publication_date=news.publication_date,
        author_id=current_user.id
    )
    db.add(db_news_post)
    db.flush()  # Get ID without committing
    
    # Create translations for each language
    translations = []
    
    # English translation
    en_translation = models.NewsTranslation(
        post_id=db_news_post.id,
        language="en",
        title=news.en.title,
        content=news.en.content,
        summary=news.en.summary
    )
    db.add(en_translation)
    translations.append(en_translation)
    
    # Russian translation
    ru_translation = models.NewsTranslation(
        post_id=db_news_post.id,
        language="ru",
        title=news.ru.title,
        content=news.ru.content,
        summary=news.ru.summary
    )
    db.add(ru_translation)
    translations.append(ru_translation)
    
    # Uzbek translation
    uz_translation = models.NewsTranslation(
        post_id=db_news_post.id,
        language="uz",
        title=news.uz.title,
        content=news.uz.content,
        summary=news.uz.summary
    )
    db.add(uz_translation)
    translations.append(uz_translation)
    
    # Karakalpak translation
    kk_translation = models.NewsTranslation(
        post_id=db_news_post.id,
        language="kk",
        title=news.kk.title,
        content=news.kk.content,
        summary=news.kk.summary
    )
    db.add(kk_translation)
    translations.append(kk_translation)
    
    db.commit()
    db.refresh(db_news_post)
    
    return db_news_post

# Get all news posts without pagination parameters
@router.get("/", response_model=List[schemas.NewsPostSummary])
async def get_news_posts(
    language: Optional[str] = None,
    published_only: bool = True,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all news posts with optional filtering by language and search term.
    Returns a simplified summary of each post.
    """
    query = db.query(models.NewsPost)
    
    # Filter by published status
    if published_only:
        query = query.filter(
            models.NewsPost.published == True,
            models.NewsPost.publication_date <= datetime.utcnow()
        )
    
    # Apply search if provided
    if search:
        search_term = f"%{search}%"
        query = query.join(models.NewsTranslation).filter(
            or_(
                models.NewsTranslation.title.ilike(search_term),
                models.NewsTranslation.content.ilike(search_term),
                models.NewsTranslation.summary.ilike(search_term)
            )
        )
        
        # If language is specified, filter translations by language
        if language:
            try:
                language = validate_language(language)
                query = query.filter(models.NewsTranslation.language == language)
            except ValueError:
                # If invalid language, just ignore the language filter
                pass
    
    # Order by publication date (newest first)
    query = query.order_by(models.NewsPost.publication_date.desc())
    
    # Make query distinct to avoid duplicates from the join
    query = query.distinct()
    
    # Get all results without pagination
    news_posts = query.all()
    
    # For each post, get the translation in the requested language or default to English
    result = []
    for post in news_posts:
        post_data = {
            "id": post.id,
            "image_url": post.image_url,
            "published": post.published,
            "publication_date": post.publication_date,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "views": post.views,
            "translations": []
        }
        
        # Get translations
        translations = db.query(models.NewsTranslation).filter(
            models.NewsTranslation.post_id == post.id
        )
        
        # If language is specified, prioritize that language
        if language:
            try:
                lang = validate_language(language)
                translation = translations.filter(models.NewsTranslation.language == lang).first()
                if translation:
                    post_data["translations"].append({
                        "language": translation.language,
                        "title": translation.title,
                        "summary": translation.summary
                    })
            except ValueError:
                pass
        
        # If no language specified or translation not found, include all translations
        if not language or not post_data["translations"]:
            for translation in translations.all():
                post_data["translations"].append({
                    "language": translation.language,
                    "title": translation.title,
                    "summary": translation.summary
                })
        
        result.append(post_data)
    
    return result

# Get a specific news post by ID with all translations
@router.get("/{post_id}", response_model=schemas.NewsPostDetail)
async def get_news_post(
    post_id: int = Path(..., gt=0),
    db: Session = Depends(get_db)
):
    """
    Get a specific news post by ID with all translations.
    """
    db_news_post = db.query(models.NewsPost).filter(models.NewsPost.id == post_id).first()
    
    if db_news_post is None:
        raise HTTPException(status_code=404, detail="News post not found")
    
    # Increment view count
    db_news_post.views += 1
    db.commit()
    
    return db_news_post

# Get a specific news post by ID with a specific language
@router.get("/{post_id}/{language}", response_model=Dict)
async def get_news_post_by_language(
    post_id: int = Path(..., gt=0),
    language: str = Path(...),
    db: Session = Depends(get_db)
):
    """
    Get a specific news post by ID with a specific language.
    """
    try:
        language = validate_language(language)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid language: {language}")
    
    db_news_post = db.query(models.NewsPost).filter(models.NewsPost.id == post_id).first()
    
    if db_news_post is None:
        raise HTTPException(status_code=404, detail="News post not found")
    
    # Get the translation for the specified language
    translation = db.query(models.NewsTranslation).filter(
        models.NewsTranslation.post_id == post_id,
        models.NewsTranslation.language == language
    ).first()
    
    if translation is None:
        raise HTTPException(status_code=404, detail=f"Translation not found for language: {language}")
    
    # Increment view count
    db_news_post.views += 1
    db.commit()
    
    # Combine post and translation data
    result = {
        "id": db_news_post.id,
        "image_url": db_news_post.image_url,
        "published": db_news_post.published,
        "publication_date": db_news_post.publication_date,
        "created_at": db_news_post.created_at,
        "updated_at": db_news_post.updated_at,
        "views": db_news_post.views,
        "language": language,
        "title": translation.title,
        "content": translation.content,
        "summary": translation.summary
    }
    
    return result

# Update a news post
@router.put("/{post_id}", response_model=schemas.NewsPostDetail)
async def update_news_post(
    post_id: int = Path(..., gt=0),
    news: schemas.MultilingualNewsUpdate = None,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    """
    Update a news post with multilingual content.
    """
    db_news_post = db.query(models.NewsPost).filter(models.NewsPost.id == post_id).first()
    
    if db_news_post is None:
        raise HTTPException(status_code=404, detail="News post not found")
    
    if news is None:
        raise HTTPException(status_code=400, detail="Request body is required")
    
    # Update post fields
    if news.image_url is not None:
        db_news_post.image_url = news.image_url
    
    if news.published is not None:
        db_news_post.published = news.published
        # Set publication date if published status changed to True
        if news.published and not db_news_post.publication_date:
            db_news_post.publication_date = datetime.utcnow()
    
    if news.publication_date is not None:
        db_news_post.publication_date = news.publication_date
    
    # Update translations
    languages = ["en", "ru", "uz", "kk"]
    for lang in languages:
        if hasattr(news, lang) and getattr(news, lang) is not None:
            lang_data = getattr(news, lang)
            
            # Check if translation exists
            db_translation = db.query(models.NewsTranslation).filter(
                models.NewsTranslation.post_id == post_id,
                models.NewsTranslation.language == lang
            ).first()
            
            if db_translation:
                # Update existing translation
                if hasattr(lang_data, "title") and lang_data.title is not None:
                    db_translation.title = lang_data.title
                if hasattr(lang_data, "content") and lang_data.content is not None:
                    db_translation.content = lang_data.content
                if hasattr(lang_data, "summary") and lang_data.summary is not None:
                    db_translation.summary = lang_data.summary
                db_translation.updated_at = datetime.utcnow()
            else:
                # Create new translation
                db_translation = models.NewsTranslation(
                    post_id=post_id,
                    language=lang,
                    title=lang_data.title,
                    content=lang_data.content,
                    summary=lang_data.summary
                )
                db.add(db_translation)
    
    db_news_post.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_news_post)
    
    return db_news_post

# Delete a news post
@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_news_post(
    post_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    """
    Delete a news post and all its translations.
    """
    db_news_post = db.query(models.NewsPost).filter(models.NewsPost.id == post_id).first()
    
    if db_news_post is None:
        raise HTTPException(status_code=404, detail="News post not found")
    
    # Delete the post (translations will be deleted automatically due to cascade)
    db.delete(db_news_post)
    db.commit()
    
    return None
