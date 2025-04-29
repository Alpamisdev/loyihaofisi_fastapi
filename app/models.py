from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import datetime

# Core Navigation & Contacts
class Menu(Base):
    __tablename__ = "menu"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    icon = Column(String)
    
    menu_links = relationship("MenuLink", back_populates="menu")

class YearName(Base):
    __tablename__ = "year_name"
    
    id = Column(Integer, primary_key=True, index=True)
    img = Column(String)
    text = Column(String, nullable=False)

class Contacts(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    address = Column(String)
    phone_number = Column(String)
    email = Column(String)

class SocialNetwork(Base):
    __tablename__ = "social_networks"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    icon = Column(String)
    link = Column(String, nullable=False)

class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    phone_number = Column(String)
    email = Column(String)
    text = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    about_company_items = relationship("AboutCompanyCategoryItem", back_populates="feedback")

# Staff
class Staff(Base):
    __tablename__ = "staff"
    
    id = Column(Integer, primary_key=True, index=True)
    position = Column(String)
    full_name = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    photo = Column(String)

# Blog
class BlogCategory(Base):
    __tablename__ = "blog_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
    blog_items = relationship("BlogItem", back_populates="category")

class BlogItem(Base):
    __tablename__ = "blog_items"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("blog_categories.id"))
    title = Column(String, nullable=False)
    img_or_video_link = Column(String)
    date_time = Column(DateTime, default=func.now())
    views = Column(Integer, default=0)
    text = Column(Text)
    intro_text = Column(Text)
    
    category = relationship("BlogCategory", back_populates="blog_items")

# About Company
class AboutCompany(Base):
    __tablename__ = "about_company"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    img = Column(String)
    date_time = Column(DateTime, default=func.now())
    views = Column(Integer, default=0)
    text = Column(Text)

class AboutCompanyCategory(Base):
    __tablename__ = "about_company_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
    items = relationship("AboutCompanyCategoryItem", back_populates="category")

class AboutCompanyCategoryItem(Base):
    __tablename__ = "about_company_category_items"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("about_company_categories.id"))
    title = Column(String, nullable=False)
    text = Column(Text)
    views = Column(Integer, default=0)
    date_time = Column(DateTime, default=func.now())
    feedback_id = Column(Integer, ForeignKey("feedback.id"), nullable=True)
    
    category = relationship("AboutCompanyCategory", back_populates="items")
    feedback = relationship("Feedback", back_populates="about_company_items")

# Documents
class DocumentCategory(Base):
    __tablename__ = "documents_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
    documents = relationship("DocumentItem", back_populates="category")

class DocumentItem(Base):
    __tablename__ = "documents_items"
    
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("documents_categories.id"))
    title = Column(String, nullable=False)
    name = Column(String)
    link = Column(String, nullable=False)
    
    category = relationship("DocumentCategory", back_populates="documents")

# Menu Links
class MenuLink(Base):
    __tablename__ = "menu_links"
    
    id = Column(Integer, primary_key=True, index=True)
    menu_id = Column(Integer, ForeignKey("menu.id"))
    target_type = Column(String)
    target_id = Column(Integer)
    label = Column(String)
    position = Column(Integer, default=0)
    
    menu = relationship("Menu", back_populates="menu_links")

# Admin Users
class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="admin")
    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime, nullable=True)

# Uploaded Files
class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_url = Column(String, nullable=False)
    file_size = Column(Integer)  # Size in bytes
    mime_type = Column(String)
    created_at = Column(DateTime, default=func.now())
    uploaded_by = Column(Integer, ForeignKey("admin_users.id"), nullable=True)
