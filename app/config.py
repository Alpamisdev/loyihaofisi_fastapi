import os
from typing import Optional
from datetime import timedelta

# Base URL for file access - defaults to None which will use the request's base URL
BASE_URL = os.getenv("BASE_URL", "https://api.alpamis.space")

# JWT Settings
SECRET_KEY = os.getenv("SECRET_KEY", "YOUR_SECRET_KEY_HERE")  # In production, use a secure random key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

# File Upload Settings
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "104857600"))  # 100MB default
ALLOWED_IMAGE_TYPES = [
    "image/jpeg", 
    "image/png", 
    "image/gif", 
    "image/webp", 
    "image/svg+xml", 
    "image/bmp", 
    "image/tiff"
]

# Token settings as timedelta objects
ACCESS_TOKEN_EXPIRE = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
REFRESH_TOKEN_EXPIRE = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
