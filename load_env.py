#!/usr/bin/env python3
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("load_env")

def load_environment():
    """Load environment variables from .env file."""
    # Load .env file
    load_dotenv()
    
    # Check if critical environment variables are set
    critical_vars = [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID"
    ]
    
    missing_vars = []
    for var in critical_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing critical environment variables: {', '.join(missing_vars)}")
        return False
    
    logger.info("Environment variables loaded successfully")
    return True

if __name__ == "__main__":
    success = load_environment()
    if success:
        logger.info("Environment check passed")
    else:
        logger.error("Environment check failed")
