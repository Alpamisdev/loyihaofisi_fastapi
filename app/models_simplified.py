from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import datetime

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
    
    # Metadata fields are removed
