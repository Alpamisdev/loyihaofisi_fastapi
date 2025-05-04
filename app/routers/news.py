from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
from datetime import datetime
import logging
from slugify import slugify
from .. import models, schemas, auth
from ..database import get_db

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/news",
    tags=["news"],
    responses={404: {"description": "Not found"}},
)

# Helper function to generate a unique slug
def generate_unique_slug(db: Session, title: str, language: str, model, existing_id: Optional[int] = None):
    base_slug = slugify(title)
    slug = base_slug
    counter = 1
    
    while True:
        # Check if slug exists for this language
        query = db.query(model).filter(
            model.slug == slug,
            model.language == language
        )
        
        # If we're updating an existing record, exclude it from the check
        if existing_id:
            query = query.filter(model.id != existing_id)
        
        if not query.first():
            return slug
        
        # Slug exists, append counter and try again
        slug = f"{base_slug}-{counter}"
        counter += 1

# News Categories
@router.post("/categories/", response_model=schemas.NewsCategory)
def create_news_category(
    category: schemas.NewsCategoryCreate, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    # Generate a unique slug if not provided
    if not category.slug:
        category.slug = generate_unique_slug(db, category.name, category.language, models.NewsCategory)
    
    # Check if category with same slug and language already exists
    db_category = db.query(models.NewsCategory).filter(
        models.NewsCategory.slug == category.slug,
        models.NewsCategory.language == category.language
    ).first()
    
    if db_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with slug '{category.slug}' already exists for language '{category.language}'"
        )
    
    # Create new category
    db_category = models.NewsCategory(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/categories/", response_model=List[schemas.NewsCategory])
def read_news_categories(
    language: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """Get all news categories with optional language filter"""
    query = db.query(models.NewsCategory)
    
    if language:
        query = query.filter(models.NewsCategory.language == language)
    
    categories = query.offset(skip).limit(limit).all()
    return categories

@router.get("/categories/{category_id}", response_model=schemas.NewsCategory)
def read_news_category(
    category_id: int = Path(..., gt=0), 
    db: Session = Depends(get_db)
):
    db_category = db.query(models.NewsCategory).filter(models.NewsCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="News category not found")
    return db_category

@router.put("/categories/{category_id}", response_model=schemas.NewsCategory)
def update_news_category(
    category_id: int = Path(..., gt=0), 
    category: schemas.NewsCategoryCreate = None, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_category = db.query(models.NewsCategory).filter(models.NewsCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="News category not found")
    
    # If slug is being changed, ensure it's unique
    if category.slug and category.slug != db_category.slug:
        category.slug = generate_unique_slug(
            db, 
            category.name, 
            category.language, 
            models.NewsCategory, 
            existing_id=category_id
        )
    
    # Update category fields
    for key, value in category.dict().items():
        setattr(db_category, key, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_news_category(
    category_id: int = Path(..., gt=0), 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_category = db.query(models.NewsCategory).filter(models.NewsCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="News category not found")
    
    db.delete(db_category)
    db.commit()
    return None

# News Tags
@router.post("/tags/", response_model=schemas.NewsTag)
def create_news_tag(
    tag: schemas.NewsTagCreate, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    # Generate a unique slug if not provided
    if not tag.slug:
        tag.slug = generate_unique_slug(db, tag.name, tag.language, models.NewsTag)
    
    # Check if tag with same slug and language already exists
    db_tag = db.query(models.NewsTag).filter(
        models.NewsTag.slug == tag.slug,
        models.NewsTag.language == tag.language
    ).first()
    
    if db_tag:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tag with slug '{tag.slug}' already exists for language '{tag.language}'"
        )
    
    # Create new tag
    db_tag = models.NewsTag(**tag.dict())
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    return db_tag

@router.get("/tags/", response_model=List[schemas.NewsTag])
def read_news_tags(
    language: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db)
):
    """Get all news tags with optional language filter"""
    query = db.query(models.NewsTag)
    
    if language:
        query = query.filter(models.NewsTag.language == language)
    
    tags = query.offset(skip).limit(limit).all()
    return tags

@router.get("/tags/{tag_id}", response_model=schemas.NewsTag)
def read_news_tag(
    tag_id: int = Path(..., gt=0), 
    db: Session = Depends(get_db)
):
    db_tag = db.query(models.NewsTag).filter(models.NewsTag.id == tag_id).first()
    if db_tag is None:
        raise HTTPException(status_code=404, detail="News tag not found")
    return db_tag

@router.put("/tags/{tag_id}", response_model=schemas.NewsTag)
def update_news_tag(
    tag_id: int = Path(..., gt=0), 
    tag: schemas.NewsTagCreate = None, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_tag = db.query(models.NewsTag).filter(models.NewsTag.id == tag_id).first()
    if db_tag is None:
        raise HTTPException(status_code=404, detail="News tag not found")
    
    # If slug is being changed, ensure it's unique
    if tag.slug and tag.slug != db_tag.slug:
        tag.slug = generate_unique_slug(
            db, 
            tag.name, 
            tag.language, 
            models.NewsTag, 
            existing_id=tag_id
        )
    
    # Update tag fields
    for key, value in tag.dict().items():
        setattr(db_tag, key, value)
    
    db.commit()
    db.refresh(db_tag)
    return db_tag

@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_news_tag(
    tag_id: int = Path(..., gt=0), 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_tag = db.query(models.NewsTag).filter(models.NewsTag.id == tag_id).first()
    if db_tag is None:
        raise HTTPException(status_code=404, detail="News tag not found")
    
    db.delete(db_tag)
    db.commit()
    return None

# News Items
@router.post("/", response_model=schemas.News)
def create_news_item(
    news: schemas.NewsCreate, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    # Generate a unique slug if not provided
    if not news.slug:
        news.slug = generate_unique_slug(db, news.title, news.language, models.News)
    
    # Check if news with same slug and language already exists
    db_news = db.query(models.News).filter(
        models.News.slug == news.slug,
        models.News.language == news.language
    ).first()
    
    if db_news:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"News with slug '{news.slug}' already exists for language '{news.language}'"
        )
    
    # Set publication date if published
    if news.published and not news.publication_date:
        news.publication_date = datetime.utcnow()
    
    # Extract tag_ids and remove from dict
    tag_ids = news.tag_ids if hasattr(news, 'tag_ids') else []
    news_data = news.dict(exclude={'tag_ids'})
    
    # Create new news item
    db_news = models.News(**news_data, author_id=current_user.id)
    db.add(db_news)
    db.flush()  # Flush to get the ID without committing
    
    # Add tags if provided
    if tag_ids:
        tags = db.query(models.NewsTag).filter(models.NewsTag.id.in_(tag_ids)).all()
        db_news.tags = tags
    
    db.commit()
    db.refresh(db_news)
    return db_news

@router.get("/", response_model=List[schemas.News])
def read_news_items(
    language: Optional[str] = None,
    category_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    published_only: bool = True,
    search: Optional[str] = None,
    skip: int = 0, 
    limit: int = 20, 
    db: Session = Depends(get_db)
):
    """Get news items with various filters"""
    query = db.query(models.News)
    
    # Apply filters
    if language:
        query = query.filter(models.News.language == language)
    
    if category_id:
        query = query.filter(models.News.category_id == category_id)
    
    if tag_id:
        query = query.join(models.News.tags).filter(models.NewsTag.id == tag_id)
    
    if published_only:
        query = query.filter(
            models.News.published == True,
            models.News.publication_date <= datetime.utcnow()
        )
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.News.title.ilike(search_term),
                models.News.content.ilike(search_term),
                models.News.summary.ilike(search_term)
            )
        )
    
    # Order by publication date (newest first)
    query = query.order_by(models.News.publication_date.desc())
    
    # Paginate results
    news_items = query.offset(skip).limit(limit).all()
    return news_items

@router.get("/{news_id}", response_model=schemas.NewsWithCategory)
def read_news_item(
    news_id: int = Path(..., gt=0), 
    db: Session = Depends(get_db)
):
    # Get news with category and author
    db_news = db.query(models.News).filter(models.News.id == news_id).first()
    
    if db_news is None:
        raise HTTPException(status_code=404, detail="News item not found")
    
    # Increment view count
    db_news.views += 1
    db.commit()
    
    return db_news

@router.get("/by-slug/{slug}", response_model=schemas.NewsWithCategory)
def read_news_by_slug(
    slug: str,
    language: str,
    db: Session = Depends(get_db)
):
    # Get news with category and author
    db_news = db.query(models.News).filter(
        models.News.slug == slug,
        models.News.language == language
    ).first()
    
    if db_news is None:
        raise HTTPException(status_code=404, detail="News item not found")
    
    # Increment view count
    db_news.views += 1
    db.commit()
    
    return db_news

@router.put("/{news_id}", response_model=schemas.News)
def update_news_item(
    news_id: int = Path(..., gt=0), 
    news: schemas.NewsUpdate = None, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_news = db.query(models.News).filter(models.News.id == news_id).first()
    if db_news is None:
        raise HTTPException(status_code=404, detail="News item not found")
    
    # Extract tag_ids and remove from dict
    tag_ids = news.tag_ids if hasattr(news, 'tag_ids') and news.tag_ids is not None else None
    news_data = news.dict(exclude={'tag_ids'}, exclude_unset=True)
    
    # Set publication date if published status changed to True
    if news_data.get('published') and not db_news.published and not db_news.publication_date:
        news_data['publication_date'] = datetime.utcnow()
    
    # Update news fields
    for key, value in news_data.items():
        setattr(db_news, key, value)
    
    # Update tags if provided
    if tag_ids is not None:
        tags = db.query(models.NewsTag).filter(models.NewsTag.id.in_(tag_ids)).all()
        db_news.tags = tags
    
    db.commit()
    db.refresh(db_news)
    return db_news

@router.delete("/{news_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_news_item(
    news_id: int = Path(..., gt=0), 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_news = db.query(models.News).filter(models.News.id == news_id).first()
    if db_news is None:
        raise HTTPException(status_code=404, detail="News item not found")
    
    db.delete(db_news)
    db.commit()
    return None

@router.post("/{news_id}/translations", response_model=schemas.News)
def add_news_translation(
    news_id: int = Path(..., gt=0),
    translation: schemas.NewsTranslation = None,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    # Get the original news item
    original_news = db.query(models.News).filter(models.News.id == news_id).first()
    if original_news is None:
        raise HTTPException(status_code=404, detail="News item not found")
    
    # Check if translation in this language already exists
    existing_translation = db.query(models.News).filter(
        models.News.slug == original_news.slug,
        models.News.language == translation.language
    ).first()
    
    if existing_translation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Translation in language '{translation.language}' already exists"
        )
    
    # Create new translation
    new_translation = models.News(
        slug=original_news.slug,
        language=translation.language,
        title=translation.title,
        content=translation.content,
        summary=translation.summary,
        image_url=original_news.image_url,
        published=original_news.published,
        publication_date=original_news.publication_date,
        category_id=original_news.category_id,
        author_id=current_user.id
    )
    
    db.add(new_translation)
    db.flush()
    
    # Copy tags from original news
    if original_news.tags:
        # Find equivalent tags in the target language
        for tag in original_news.tags:
            target_tag = db.query(models.NewsTag).filter(
                models.NewsTag.slug == tag.slug,
                models.NewsTag.language == translation.language
            ).first()
            
            if target_tag:
                new_translation.tags.append(target_tag)
    
    db.commit()
    db.refresh(new_translation)
    return new_translation

@router.get("/{news_id}/translations", response_model=List[schemas.News])
def get_news_translations(
    news_id: int = Path(..., gt=0),
    db: Session = Depends(get_db)
):
    # Get the original news item
    original_news = db.query(models.News).filter(models.News.id == news_id).first()
    if original_news is None:
        raise HTTPException(status_code=404, detail="News item not found")
    
    # Get all translations (all news items with the same slug but different languages)
    translations = db.query(models.News).filter(
        models.News.slug == original_news.slug,
        models.News.id != news_id
    ).all()
    
    return translations
