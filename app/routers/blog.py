from fastapi import APIRouter, Depends, HTTPException, status, Path, BackgroundTasks, Query
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
    prefix="/blog",
    tags=["blog"],
    responses={404: {"description": "Not found"}},
)

# Helper function to validate language
def validate_language(language: str) -> str:
    valid_languages = ["en", "ru", "uz", "kk"]
    if language not in valid_languages:
        raise ValueError(f"Invalid language: {language}. Must be one of {valid_languages}")
    return language

# Legacy Blog Categories endpoints for backward compatibility
@router.post("/categories/", response_model=schemas.BlogCategory)
def create_blog_category(
    category: schemas.BlogCategoryBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_category = models.BlogCategory(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/categories/", response_model=List[schemas.BlogCategory])
def read_blog_categories(
    language: Optional[str] = Query(None, description="Filter by language (en, ru, uz, kk)"),
    db: Session = Depends(get_db)
):
    """Get all blog categories with optional language filtering"""
    categories = db.query(models.BlogCategory).all()
    
    # If language is specified, include translations for that language
    if language:
        try:
            language = validate_language(language)
            for category in categories:
                # Filter translations by language
                category.translations = [
                    t for t in category.translations 
                    if t.language == language
                ]
        except ValueError:
            # If invalid language, just ignore the language filter
            pass
    
    return categories

@router.get("/categories/{category_id}", response_model=schemas.BlogCategory)
def read_blog_category(
    category_id: int, 
    language: Optional[str] = Query(None, description="Filter by language (en, ru, uz, kk)"),
    db: Session = Depends(get_db)
):
    db_category = db.query(models.BlogCategory).filter(models.BlogCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Blog category not found")
    
    # If language is specified, include only translations for that language
    if language:
        try:
            language = validate_language(language)
            db_category.translations = [
                t for t in db_category.translations 
                if t.language == language
            ]
        except ValueError:
            # If invalid language, just ignore the language filter
            pass
    
    return db_category

@router.put("/categories/{category_id}", response_model=schemas.BlogCategory)
def update_blog_category(
    category_id: int, 
    category: schemas.BlogCategoryBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_category = db.query(models.BlogCategory).filter(models.BlogCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Blog category not found")
    
    for key, value in category.dict().items():
        setattr(db_category, key, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog_category(
    category_id: int, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_category = db.query(models.BlogCategory).filter(models.BlogCategory.id == category_id).first()
    if db_category is None:
        raise HTTPException(status_code=404, detail="Blog category not found")
    
    db.delete(db_category)
    db.commit()
    return None

# New multilingual blog category endpoints

# Create a multilingual blog category
@router.post("/categories/multilingual/", response_model=schemas.BlogCategoryDetail)
async def create_multilingual_blog_category(
    category: schemas.MultilingualBlogCategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    """
    Create a blog category with names in all supported languages.
    """
    # Create the base category with English name as default
    db_category = models.BlogCategory(name=category.en.name)
    db.add(db_category)
    db.flush()  # Get ID without committing
    
    # Create translations for each language
    translations = []
    
    # English translation
    en_translation = models.BlogCategoryTranslation(
        category_id=db_category.id,
        language="en",
        name=category.en.name
    )
    db.add(en_translation)
    translations.append(en_translation)
    
    # Russian translation
    ru_translation = models.BlogCategoryTranslation(
        category_id=db_category.id,
        language="ru",
        name=category.ru.name
    )
    db.add(ru_translation)
    translations.append(ru_translation)
    
    # Uzbek translation
    uz_translation = models.BlogCategoryTranslation(
        category_id=db_category.id,
        language="uz",
        name=category.uz.name
    )
    db.add(uz_translation)
    translations.append(uz_translation)
    
    # Karakalpak translation
    kk_translation = models.BlogCategoryTranslation(
        category_id=db_category.id,
        language="kk",
        name=category.kk.name
    )
    db.add(kk_translation)
    translations.append(kk_translation)
    
    db.commit()
    db.refresh(db_category)
    
    return db_category

# Get all multilingual blog categories
@router.get("/categories/multilingual/", response_model=List[schemas.BlogCategoryDetail])
async def get_multilingual_blog_categories(
    language: Optional[str] = Query(None, description="Filter by language (en, ru, uz, kk)"),
    db: Session = Depends(get_db)
):
    """
    Get all blog categories with translations.
    If language is specified, only include translations for that language.
    """
    categories = db.query(models.BlogCategory).all()
    
    # If language is specified, filter translations by language
    if language:
        try:
            language = validate_language(language)
            for category in categories:
                category.translations = [
                    t for t in category.translations 
                    if t.language == language
                ]
        except ValueError:
            # If invalid language, just ignore the language filter
            pass
    
    return categories

# Get a specific multilingual blog category
@router.get("/categories/multilingual/{category_id}", response_model=schemas.BlogCategoryDetail)
async def get_multilingual_blog_category(
    category_id: int = Path(..., gt=0),
    language: Optional[str] = Query(None, description="Filter by language (en, ru, uz, kk)"),
    db: Session = Depends(get_db)
):
    """
    Get a specific blog category with translations.
    If language is specified, only include translations for that language.
    """
    db_category = db.query(models.BlogCategory).filter(models.BlogCategory.id == category_id).first()
    
    if db_category is None:
        raise HTTPException(status_code=404, detail="Blog category not found")
    
    # If language is specified, filter translations by language
    if language:
        try:
            language = validate_language(language)
            db_category.translations = [
                t for t in db_category.translations 
                if t.language == language
            ]
        except ValueError:
            # If invalid language, just ignore the language filter
            pass
    
    return db_category

# Get a specific blog category in a specific language
@router.get("/categories/multilingual/{category_id}/{language}", response_model=Dict)
async def get_blog_category_by_language(
    category_id: int = Path(..., gt=0),
    language: str = Path(...),
    db: Session = Depends(get_db)
):
    """
    Get a specific blog category in a specific language.
    """
    try:
        language = validate_language(language)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid language: {language}")
    
    db_category = db.query(models.BlogCategory).filter(models.BlogCategory.id == category_id).first()
    
    if db_category is None:
        raise HTTPException(status_code=404, detail="Blog category not found")
    
    # Get the translation for the specified language
    translation = db.query(models.BlogCategoryTranslation).filter(
        models.BlogCategoryTranslation.category_id == category_id,
        models.BlogCategoryTranslation.language == language
    ).first()
    
    if translation is None:
        raise HTTPException(status_code=404, detail=f"Translation not found for language: {language}")
    
    # Combine category and translation data
    result = {
        "id": db_category.id,
        "language": language,
        "name": translation.name,
        "created_at": translation.created_at,
        "updated_at": translation.updated_at
    }
    
    return result

# Update a multilingual blog category
@router.put("/categories/multilingual/{category_id}", response_model=schemas.BlogCategoryDetail)
async def update_multilingual_blog_category(
    category_id: int = Path(..., gt=0),
    category: schemas.MultilingualBlogCategoryUpdate = None,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    """
    Update a blog category with multilingual names.
    """
    db_category = db.query(models.BlogCategory).filter(models.BlogCategory.id == category_id).first()
    
    if db_category is None:
        raise HTTPException(status_code=404, detail="Blog category not found")
    
    if category is None:
        raise HTTPException(status_code=400, detail="Request body is required")
    
    # Update base category name if English name is provided
    if hasattr(category, "en") and category.en is not None and hasattr(category.en, "name"):
        db_category.name = category.en.name
    
    # Update translations
    languages = ["en", "ru", "uz", "kk"]
    for lang in languages:
        if hasattr(category, lang) and getattr(category, lang) is not None:
            lang_data = getattr(category, lang)
            
            # Check if translation exists
            db_translation = db.query(models.BlogCategoryTranslation).filter(
                models.BlogCategoryTranslation.category_id == category_id,
                models.BlogCategoryTranslation.language == lang
            ).first()
            
            if db_translation:
                # Update existing translation
                if hasattr(lang_data, "name") and lang_data.name is not None:
                    db_translation.name = lang_data.name
                db_translation.updated_at = datetime.utcnow()
            else:
                # Create new translation
                db_translation = models.BlogCategoryTranslation(
                    category_id=category_id,
                    language=lang,
                    name=lang_data.name
                )
                db.add(db_translation)
    
    db.commit()
    db.refresh(db_category)
    
    return db_category

# Legacy Blog Items endpoints for backward compatibility
@router.post("/items/", response_model=schemas.BlogItem)
def create_blog_item(
    blog_item: schemas.BlogItemBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_blog_item = models.BlogItem(**blog_item.dict())
    db.add(db_blog_item)
    db.commit()
    db.refresh(db_blog_item)
    return db_blog_item

@router.get("/items/", response_model=List[schemas.BlogItem])
def read_blog_items(db: Session = Depends(get_db)):
    """Get all blog items without pagination"""
    blog_items = db.query(models.BlogItem).all()
    return blog_items

@router.get("/items/{blog_item_id}", response_model=schemas.BlogItem)
def read_blog_item(blog_item_id: int, db: Session = Depends(get_db)):
    db_blog_item = db.query(models.BlogItem).filter(models.BlogItem.id == blog_item_id).first()
    if db_blog_item is None:
        raise HTTPException(status_code=404, detail="Blog item not found")
    
    # Increment view count
    db_blog_item.views += 1
    db.commit()
    
    return db_blog_item

@router.put("/items/{blog_item_id}", response_model=schemas.BlogItem)
def update_blog_item(
    blog_item_id: int, 
    blog_item: schemas.BlogItemBase, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_blog_item = db.query(models.BlogItem).filter(models.BlogItem.id == blog_item_id).first()
    if db_blog_item is None:
        raise HTTPException(status_code=404, detail="Blog item not found")
    
    for key, value in blog_item.dict().items():
        setattr(db_blog_item, key, value)
    
    db.commit()
    db.refresh(db_blog_item)
    return db_blog_item

@router.delete("/items/{blog_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_blog_item(
    blog_item_id: int, 
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    db_blog_item = db.query(models.BlogItem).filter(models.BlogItem.id == blog_item_id).first()
    if db_blog_item is None:
        raise HTTPException(status_code=404, detail="Blog item not found")
    
    db.delete(db_blog_item)
    db.commit()
    return None

# Get blog items by category (legacy)
@router.get("/categories/{category_id}/items", response_model=List[schemas.BlogItem])
def read_blog_items_by_category(category_id: int, db: Session = Depends(get_db)):
    """Get all blog items for a specific category without pagination"""
    blog_items = db.query(models.BlogItem).filter(models.BlogItem.category_id == category_id).all()
    return blog_items

# New multilingual blog endpoints

# Single endpoint for creating multilingual blog posts
@router.post("/posts/", response_model=schemas.BlogPostDetail)
async def create_blog_post(
    blog: schemas.MultilingualBlogCreate,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    """
    Create a blog post with content in all supported languages (English, Russian, Uzbek, and Karakalpak).
    """
    # Check if category exists
    db_category = db.query(models.BlogCategory).filter(models.BlogCategory.id == blog.category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail=f"Category with ID {blog.category_id} not found")
        
    # Create the blog post
    db_blog_post = models.BlogPost(
        category_id=blog.category_id,
        img_or_video_link=blog.img_or_video_link,
        published=blog.published,
        date_time=datetime.utcnow()
    )
    db.add(db_blog_post)
    db.flush()  # Get ID without committing
    
    # Create translations for each language
    translations = []
    
    # English translation
    en_translation = models.BlogTranslation(
        post_id=db_blog_post.id,
        language="en",
        title=blog.en.title,
        intro_text=blog.en.intro_text,
        text=blog.en.text
    )
    db.add(en_translation)
    translations.append(en_translation)
    
    # Russian translation
    ru_translation = models.BlogTranslation(
        post_id=db_blog_post.id,
        language="ru",
        title=blog.ru.title,
        intro_text=blog.ru.intro_text,
        text=blog.ru.text
    )
    db.add(ru_translation)
    translations.append(ru_translation)
    
    # Uzbek translation
    uz_translation = models.BlogTranslation(
        post_id=db_blog_post.id,
        language="uz",
        title=blog.uz.title,
        intro_text=blog.uz.intro_text,
        text=blog.uz.text
    )
    db.add(uz_translation)
    translations.append(uz_translation)
    
    # Karakalpak translation
    kk_translation = models.BlogTranslation(
        post_id=db_blog_post.id,
        language="kk",
        title=blog.kk.title,
        intro_text=blog.kk.intro_text,
        text=blog.kk.text
    )
    db.add(kk_translation)
    translations.append(kk_translation)
    
    db.commit()
    db.refresh(db_blog_post)
    
    return db_blog_post

# Get all blog posts with language filtering
@router.get("/posts/", response_model=List[schemas.BlogPostSummary])
async def get_blog_posts(
    language: Optional[str] = Query(None, description="Filter by language (en, ru, uz, kk)"),
    published_only: bool = Query(True, description="Show only published posts"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    db: Session = Depends(get_db)
):
    """
    Get all blog posts with optional filtering by language, category, and search term.
    Returns a simplified summary of each post.
    """
    try:
        logger.info(f"Fetching blog posts with params: language={language}, published_only={published_only}, category_id={category_id}, search={search}")
        
        # Start with a base query
        query = db.query(models.BlogPost)
        
        # Filter by published status
        if published_only:
            query = query.filter(models.BlogPost.published == True)
        
        # Filter by category if provided
        if category_id is not None:
            query = query.filter(models.BlogPost.category_id == category_id)
        
        # Apply search if provided
        if search:
            search_term = f"%{search}%"
            # Use outerjoin instead of join to avoid filtering out posts without translations
            query = query.outerjoin(models.BlogTranslation).filter(
                or_(
                    models.BlogTranslation.title.ilike(search_term),
                    models.BlogTranslation.text.ilike(search_term),
                    models.BlogTranslation.intro_text.ilike(search_term)
                )
            )
            
            # If language is specified, filter translations by language
            if language:
                try:
                    language = validate_language(language)
                    query = query.filter(models.BlogTranslation.language == language)
                except ValueError as e:
                    logger.warning(f"Invalid language parameter: {e}")
                    # If invalid language, just ignore the language filter
                    pass
        
        # Order by date (newest first)
        query = query.order_by(models.BlogPost.date_time.desc())
        
        # Make query distinct to avoid duplicates from the join
        query = query.distinct()
        
        # Execute the query and handle potential database errors
        try:
            blog_posts = query.all()
            logger.info(f"Found {len(blog_posts)} blog posts")
        except Exception as db_error:
            logger.error(f"Database error when fetching blog posts: {str(db_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred while fetching blog posts"
            )
        
        # For each post, get the translation in the requested language or default to English
        result = []
        for post in blog_posts:
            post_data = {
                "id": post.id,
                "category_id": post.category_id,
                "img_or_video_link": post.img_or_video_link,
                "date_time": post.date_time,
                "views": post.views,
                "published": post.published,
                "translations": []
            }
            
            # Get translations safely
            try:
                # Get translations
                translations = db.query(models.BlogTranslation).filter(
                    models.BlogTranslation.post_id == post.id
                )
                
                # If language is specified, prioritize that language
                if language:
                    try:
                        lang = validate_language(language)
                        translation = translations.filter(models.BlogTranslation.language == lang).first()
                        if translation:
                            post_data["translations"].append({
                                "language": translation.language,
                                "title": translation.title,
                                "intro_text": translation.intro_text
                            })
                    except ValueError:
                        pass
                
                # If no language specified or translation not found, include all translations
                if not language or not post_data["translations"]:
                    for translation in translations.all():
                        post_data["translations"].append({
                            "language": translation.language,
                            "title": translation.title,
                            "intro_text": translation.intro_text
                        })
                
                # Only add posts that have at least one translation
                if post_data["translations"]:
                    result.append(post_data)
                else:
                    logger.warning(f"Skipping post ID {post.id} as it has no translations")
                    
            except Exception as e:
                logger.error(f"Error processing translations for post {post.id}: {str(e)}")
                # Continue with next post instead of failing the entire request
                continue
        
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error in get_blog_posts: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while fetching blog posts"
        )

# Get a specific blog post by ID with all translations
@router.get("/posts/{post_id}", response_model=schemas.BlogPostDetail)
async def get_blog_post(
    post_id: int = Path(..., gt=0),
    db: Session = Depends(get_db)
):
    """
    Get a specific blog post by ID with all translations.
    """
    db_blog_post = db.query(models.BlogPost).filter(models.BlogPost.id == post_id).first()
    
    if db_blog_post is None:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    # Increment view count
    db_blog_post.views += 1
    db.commit()
    
    return db_blog_post

# Get a specific blog post by ID with a specific language
@router.get("/posts/{post_id}/{language}", response_model=Dict)
async def get_blog_post_by_language(
    post_id: int = Path(..., gt=0),
    language: str = Path(...),
    db: Session = Depends(get_db)
):
    """
    Get a specific blog post by ID with a specific language.
    """
    try:
        language = validate_language(language)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid language: {language}")
    
    db_blog_post = db.query(models.BlogPost).filter(models.BlogPost.id == post_id).first()
    
    if db_blog_post is None:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    # Get the translation for the specified language
    translation = db.query(models.BlogTranslation).filter(
        models.BlogTranslation.post_id == post_id,
        models.BlogTranslation.language == language
    ).first()
    
    if translation is None:
        raise HTTPException(status_code=404, detail=f"Translation not found for language: {language}")
    
    # Increment view count
    db_blog_post.views += 1
    db.commit()
    
    # Combine post and translation data
    result = {
        "id": db_blog_post.id,
        "category_id": db_blog_post.category_id,
        "img_or_video_link": db_blog_post.img_or_video_link,
        "date_time": db_blog_post.date_time,
        "views": db_blog_post.views,
        "published": db_blog_post.published,
        "language": language,
        "title": translation.title,
        "intro_text": translation.intro_text,
        "text": translation.text
    }
    
    return result

# Update a blog post
@router.put("/posts/{post_id}", response_model=schemas.BlogPostDetail)
async def update_blog_post(
    post_id: int = Path(..., gt=0),
    blog: schemas.MultilingualBlogUpdate = None,
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    """
    Update a blog post with multilingual content.
    """
    db_blog_post = db.query(models.BlogPost).filter(models.BlogPost.id == post_id).first()
    
    if db_blog_post is None:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    if blog is None:
        raise HTTPException(status_code=400, detail="Request body is required")
    
    # Update post fields
    if blog.category_id is not None:
        # Check if category exists
        db_category = db.query(models.BlogCategory).filter(models.BlogCategory.id == blog.category_id).first()
        if not db_category:
            raise HTTPException(status_code=404, detail=f"Category with ID {blog.category_id} not found")
        db_blog_post.category_id = blog.category_id
    
    if blog.img_or_video_link is not None:
        db_blog_post.img_or_video_link = blog.img_or_video_link
    
    if blog.published is not None:
        db_blog_post.published = blog.published
    
    # Update translations
    languages = ["en", "ru", "uz", "kk"]
    for lang in languages:
        if hasattr(blog, lang) and getattr(blog, lang) is not None:
            lang_data = getattr(blog, lang)
            
            # Check if translation exists
            db_translation = db.query(models.BlogTranslation).filter(
                models.BlogTranslation.post_id == post_id,
                models.BlogTranslation.language == lang
            ).first()
            
            if db_translation:
                # Update existing translation
                if hasattr(lang_data, "title") and lang_data.title is not None:
                    db_translation.title = lang_data.title
                if hasattr(lang_data, "intro_text") and lang_data.intro_text is not None:
                    db_translation.intro_text = lang_data.intro_text
                if hasattr(lang_data, "text") and lang_data.text is not None:
                    db_translation.text = lang_data.text
                db_translation.updated_at = datetime.utcnow()
            else:
                # Create new translation
                db_translation = models.BlogTranslation(
                    post_id=post_id,
                    language=lang,
                    title=lang_data.title,
                    intro_text=lang_data.intro_text,
                    text=lang_data.text
                )
                db.add(db_translation)
    
    db.commit()
    db.refresh(db_blog_post)
    
    return db_blog_post

# Delete a blog post
@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blog_post(
    post_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: models.AdminUser = Depends(auth.get_current_user)
):
    """
    Delete a blog post and all its translations.
    """
    db_blog_post = db.query(models.BlogPost).filter(models.BlogPost.id == post_id).first()
    
    if db_blog_post is None:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    # Delete the post (translations will be deleted automatically due to cascade)
    db.delete(db_blog_post)
    db.commit()
    
    return None

# Get blog posts by category with language support
@router.get("/categories/{category_id}/posts", response_model=List[schemas.BlogPostSummary])
async def read_blog_posts_by_category(
    category_id: int = Path(..., gt=0),
    language: Optional[str] = Query(None, description="Filter by language (en, ru, uz, kk)"),
    published_only: bool = Query(True, description="Show only published posts"),
    db: Session = Depends(get_db)
):
    """
    Get all blog posts for a specific category with optional language filtering.
    """
    # Check if category exists
    db_category = db.query(models.BlogCategory).filter(models.BlogCategory.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail=f"Category with ID {category_id} not found")
    
    query = db.query(models.BlogPost).filter(models.BlogPost.category_id == category_id)
    
    # Filter by published status
    if published_only:
        query = query.filter(models.BlogPost.published == True)
    
    # Apply language filter if provided
    if language:
        try:
            language = validate_language(language)
            query = query.join(models.BlogTranslation).filter(models.BlogTranslation.language == language)
        except ValueError:
            # If invalid language, just ignore the language filter
            pass
    
    # Order by date (newest first)
    query = query.order_by(models.BlogPost.date_time.desc())
    
    # Make query distinct to avoid duplicates from the join
    query = query.distinct()
    
    # Get all results without pagination
    blog_posts = query.all()
    
    # For each post, get the translation in the requested language or default to all
    result = []
    for post in blog_posts:
        post_data = {
            "id": post.id,
            "category_id": post.category_id,
            "img_or_video_link": post.img_or_video_link,
            "date_time": post.date_time,
            "views": post.views,
            "published": post.published,
            "translations": []
        }
        
        # Get translations
        translations = db.query(models.BlogTranslation).filter(
            models.BlogTranslation.post_id == post.id
        )
        
        # If language is specified, prioritize that language
        if language:
            try:
                lang = validate_language(language)
                translation = translations.filter(models.BlogTranslation.language == lang).first()
                if translation:
                    post_data["translations"].append({
                        "language": translation.language,
                        "title": translation.title,
                        "intro_text": translation.intro_text
                    })
            except ValueError:
                pass
        
        # If no language specified or translation not found, include all translations
        if not language or not post_data["translations"]:
            for translation in translations.all():
                post_data["translations"].append({
                    "language": translation.language,
                    "title": translation.title,
                    "intro_text": translation.intro_text
                })
        
        result.append(post_data)
    
    return result
