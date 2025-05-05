from pydantic import BaseModel, Field, validator
from typing import Optional, List, Union, Dict
from datetime import datetime
from enum import Enum

# Import EmailStr conditionally to avoid errors if email-validator is not installed
try:
    from pydantic import EmailStr
except ImportError:
    from typing import Annotated
    from pydantic import StringConstraints
    # Create a fallback type that's just a string with validation
    EmailStr = Annotated[str, StringConstraints(pattern=r"[^@]+@[^@]+\.[^@]+")]

# Language Enum for multilingual support
class LanguageEnum(str, Enum):
    EN = "en"
    RU = "ru"
    UZ = "uz"
    KK = "kk"  # Karakalpak

# Base schemas
class MenuBase(BaseModel):
    name: str
    icon: Optional[str] = None

class YearNameBase(BaseModel):
    img: Optional[str] = None
    text: str

class ContactsBase(BaseModel):
    address: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None

class SocialNetworkBase(BaseModel):
    name: str
    icon: Optional[str] = None
    link: str

class FeedbackBase(BaseModel):
    full_name: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    text: Optional[str] = None
    theme: Optional[str] = None

class StaffBase(BaseModel):
    position: Optional[str] = None
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    photo: Optional[str] = None
    address: Optional[str] = None  # Ensure this is Optional

class BlogCategoryBase(BaseModel):
    name: str

class BlogItemBase(BaseModel):
    category_id: int
    title: str
    img_or_video_link: Optional[str] = None
    intro_text: Optional[str] = None
    text: Optional[str] = None

class AboutCompanyBase(BaseModel):
    title: str
    img: Optional[str] = None
    text: Optional[str] = None

class AboutCompanyCategoryBase(BaseModel):
    name: str

class AboutCompanyCategoryItemBase(BaseModel):
    category_id: int
    title: str
    text: Optional[str] = None
    feedback_id: Optional[int] = None

class DocumentCategoryBase(BaseModel):
    name: str

class DocumentItemBase(BaseModel):
    category_id: int
    title: str
    name: Optional[str] = None
    link: str

class MenuLinkBase(BaseModel):
    menu_id: int
    target_type: str
    target_id: int
    label: Optional[str] = None
    position: Optional[int] = 0

class AdminUserBase(BaseModel):
    username: str
    role: Optional[str] = "admin"

class AdminUserCreate(AdminUserBase):
    password: str

# Uploaded File schemas
class UploadedFileBase(BaseModel):
    filename: str
    original_filename: str
    file_path: str
    file_url: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None

class UploadedFile(UploadedFileBase):
    id: int
    created_at: datetime
    uploaded_by: Optional[int] = None
    
    class Config:
        from_attributes = True
        # Make the model more permissive
        extra = "ignore"

# Response schemas (including id and other auto-generated fields)
class Menu(MenuBase):
    id: int
    
    class Config:
        from_attributes = True

class YearName(YearNameBase):
    id: int
    
    class Config:
        from_attributes = True

class Contacts(ContactsBase):
    id: int
    
    class Config:
        from_attributes = True

class SocialNetwork(SocialNetworkBase):
    id: int
    
    class Config:
        from_attributes = True

class Feedback(FeedbackBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class Staff(StaffBase):
    id: int
    
    class Config:
        from_attributes = True

class BlogCategory(BlogCategoryBase):
    id: int
    
    class Config:
        from_attributes = True

class BlogItem(BlogItemBase):
    id: int
    date_time: datetime
    views: int
    
    class Config:
        from_attributes = True

class AboutCompany(AboutCompanyBase):
    id: int
    date_time: datetime
    views: int
    
    class Config:
        from_attributes = True

class AboutCompanyCategory(AboutCompanyCategoryBase):
    id: int
    
    class Config:
        from_attributes = True

class AboutCompanyCategoryItem(AboutCompanyCategoryItemBase):
    id: int
    date_time: datetime
    views: int
    
    class Config:
        from_attributes = True

class DocumentCategory(DocumentCategoryBase):
    id: int
    
    class Config:
        from_attributes = True

class DocumentItem(DocumentItemBase):
    id: int
    
    class Config:
        from_attributes = True

class MenuLink(MenuLinkBase):
    id: int
    
    class Config:
        from_attributes = True

class AdminUser(AdminUserBase):
    id: int
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Token schemas for authentication
class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None
    expires_in: Optional[int] = None  # Seconds until the access token expires

class TokenData(BaseModel):
    username: Optional[str] = None

# New schemas for refresh token
class RefreshTokenCreate(BaseModel):
    user_id: int
    device_info: Optional[str] = None
    ip_address: Optional[str] = None

class RefreshToken(BaseModel):
    id: int
    user_id: int
    expires_at: datetime
    created_at: datetime
    device_info: Optional[str] = None
    revoked: bool = False
    
    class Config:
        from_attributes = True

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class TokenRevokeRequest(BaseModel):
    refresh_token: str

# News Translation Schema
class NewsTranslationBase(BaseModel):
    language: str
    title: str
    content: Optional[str] = None
    summary: Optional[str] = None

class NewsTranslationCreate(NewsTranslationBase):
    pass

class NewsTranslation(NewsTranslationBase):
    id: int
    post_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# News Post Schema
class NewsPostBase(BaseModel):
    image_url: Optional[str] = None
    published: bool = False
    publication_date: Optional[datetime] = None

class NewsPostCreate(NewsPostBase):
    translations: List[NewsTranslationCreate]

class NewsPostUpdate(NewsPostBase):
    translations: Optional[List[NewsTranslationCreate]] = None

class NewsPost(NewsPostBase):
    id: int
    created_at: datetime
    updated_at: datetime
    author_id: Optional[int] = None
    views: int
    
    class Config:
        from_attributes = True

class NewsPostDetail(NewsPost):
    translations: List[NewsTranslation] = []
    author: Optional[AdminUser] = None
    
    class Config:
        from_attributes = True

# Schema for translation summary in list view
class TranslationSummary(BaseModel):
    language: str
    title: str
    summary: Optional[str] = None

# Schema for news post summary in list view
class NewsPostSummary(BaseModel):
    id: int
    image_url: Optional[str] = None
    published: bool
    publication_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    views: int
    translations: List[TranslationSummary] = []
    
    class Config:
        from_attributes = True

# New schema for multilingual news content
class MultilingualNewsContent(BaseModel):
    title: str
    content: Optional[str] = None
    summary: Optional[str] = None

# New schema for multilingual news creation
class MultilingualNewsCreate(BaseModel):
    image_url: Optional[str] = None
    published: bool = False
    publication_date: Optional[datetime] = None
    en: MultilingualNewsContent
    ru: MultilingualNewsContent
    uz: MultilingualNewsContent
    kk: MultilingualNewsContent
    
    @validator('publication_date', pre=True, always=True)
    def set_publication_date(cls, v, values):
        if values.get('published', False) and not v:
            return datetime.utcnow()
        return v

# New schema for multilingual news update
class MultilingualNewsUpdate(BaseModel):
    image_url: Optional[str] = None
    published: Optional[bool] = None
    publication_date: Optional[datetime] = None
    en: Optional[MultilingualNewsContent] = None
    ru: Optional[MultilingualNewsContent] = None
    uz: Optional[MultilingualNewsContent] = None
    kk: Optional[MultilingualNewsContent] = None
    
    @validator('publication_date', pre=True, always=True)
    def set_publication_date(cls, v, values):
        if values.get('published', False) and not v:
            return datetime.utcnow()
        return v
