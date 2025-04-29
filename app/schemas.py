from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Import EmailStr conditionally to avoid errors if email-validator is not installed
try:
    from pydantic import EmailStr
except ImportError:
    from typing import Annotated
    from pydantic import StringConstraints
    # Create a fallback type that's just a string with validation
    EmailStr = Annotated[str, StringConstraints(pattern=r"[^@]+@[^@]+\.[^@]+")]

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

class StaffBase(BaseModel):
    position: Optional[str] = None
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    photo: Optional[str] = None

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

# Token schema for authentication
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
