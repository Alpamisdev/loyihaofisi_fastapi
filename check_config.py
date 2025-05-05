#!/usr/bin/env python3
import inspect
import logging
from app.config import *

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("check_config")

def check_config():
    """Check what variables are available in the config module."""
    # Get all variables from the config module
    config_vars = {name: value for name, value in globals().items() 
                  if not name.startswith('_') and not inspect.ismodule(value)}
    
    logger.info("Available config variables:")
    for name, value in config_vars.items():
        # Mask sensitive values
        if "TOKEN" in name or "KEY" in name or "PASSWORD" in name or "SECRET" in name:
            value_str = f"{str(value)[:5]}..." if value else "Not set"
        else:
            value_str = str(value)
        
        logger.info(f"  {name}: {value_str}")
    
    # Check specifically for Telegram variables
    telegram_vars = ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "TELEGRAM_ENABLED"]
    missing = [var for var in telegram_vars if var not in config_vars]
    
    if missing:
        logger.warning(f"Missing Telegram config variables: {', '.join(missing)}")
        return False
    
    logger.info("All required Telegram config variables are available")
    return True

if __name__ == "__main__":
    check_config()
