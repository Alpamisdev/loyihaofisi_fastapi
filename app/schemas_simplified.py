from pydantic import BaseModel
from typing import Optional
from datetime import datetime

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
