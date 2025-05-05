#!/usr/bin/env python3
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("check_env")

def check_environment():
    """Check if environment variables are loaded correctly."""
    # Load .env file
    load_dotenv()
    
    # Check Telegram configuration
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    telegram_enabled = os.getenv("TELEGRAM_ENABLED")
    
    logger.info(f"TELEGRAM_BOT_TOKEN: {'Set' if telegram_bot_token else 'Not set'}")
    if telegram_bot_token:
        # Show first few characters for verification
        logger.info(f"  Token starts with: {telegram_bot_token[:5]}...")
    
    logger.info(f"TELEGRAM_CHAT_ID: {'Set' if telegram_chat_id else 'Not set'}")
    if telegram_chat_id:
        logger.info(f"  Chat ID: {telegram_chat_id}")
    
    logger.info(f"TELEGRAM_ENABLED: {telegram_enabled}")
    
    # Check if critical environment variables are set
    if not telegram_bot_token or not telegram_chat_id:
        logger.warning("Missing critical Telegram configuration!")
        return False
    
    logger.info("Environment variables loaded successfully")
    return True

if __name__ == "__main__":
    success = check_environment()
    if success:
        logger.info("Environment check passed")
    else:
        logger.error("Environment check failed")
