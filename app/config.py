import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base URL for file access - defaults to None which will use the request's base URL
BASE_URL = os.getenv("BASE_URL", "https://api.alpamis.space")

# JWT Settings
SECRET_KEY = os.getenv("SECRET_KEY", "YOUR_SECRET_KEY_HERE")  # In production, use a secure random key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1800"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))  # 30 days
REFRESH_TOKEN_SECRET_KEY = os.getenv("REFRESH_TOKEN_SECRET_KEY", SECRET_KEY)  # Use a different key in production

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

# Telegram Notification Settings
TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "True").lower() in ("true", "1", "t")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Print Telegram settings for debugging
print(f"TELEGRAM_ENABLED: {TELEGRAM_ENABLED}")
print(f"TELEGRAM_BOT_TOKEN: {'Set' if TELEGRAM_BOT_TOKEN else 'Not set'}")
print(f"TELEGRAM_CHAT_ID: {'Set' if TELEGRAM_CHAT_ID else 'Not set'}")
