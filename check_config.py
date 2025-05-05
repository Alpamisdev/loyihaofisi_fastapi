#!/usr/bin/env python3
import os
import logging
from dotenv import load_dotenv
from app.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_ENABLED

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("check_config")

def check_config():
    """Check if config variables are loaded correctly."""
    # Load .env file
    load_dotenv()
    
    # Check Telegram configuration
    logger.info(f"TELEGRAM_ENABLED: {TELEGRAM_ENABLED}")
    logger.info(f"TELEGRAM_BOT_TOKEN: {'Set' if TELEGRAM_BOT_TOKEN else 'Not set'}")
    if TELEGRAM_BOT_TOKEN:
        # Show first few characters for verification
        logger.info(f"  Token starts with: {TELEGRAM_BOT_TOKEN[:5]}...")
    
    logger.info(f"TELEGRAM_CHAT_ID: {'Set' if TELEGRAM_CHAT_ID else 'Not set'}")
    if TELEGRAM_CHAT_ID:
        logger.info(f"  Chat ID: {TELEGRAM_CHAT_ID}")
    
    # Check if critical environment variables are set
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Missing critical Telegram configuration!")
        return False
    
    logger.info("Config variables loaded successfully")
    return True

if __name__ == "__main__":
    success = check_config()
    if success:
        logger.info("Config check passed")
    else:
        logger.error("Config check failed")
