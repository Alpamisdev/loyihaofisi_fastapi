#!/usr/bin/env python3
import asyncio
import logging
from datetime import datetime
from app.utils.telegram_notifier import send_telegram_notification

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_telegram")

async def test_telegram_notification():
    """Test the Telegram notification system."""
    # Create a sample feedback
    sample_feedback = {
        "id": 999,
        "full_name": "Test User",
        "phone_number": "+1234567890",
        "email": "test@example.com",
        "text": "This is a test feedback message.\nIt has multiple lines.\nTesting Telegram notification system.",
        "theme": "Website Feedback",
        "created_at": datetime.now()
    }
    
    logger.info("Sending test Telegram notification...")
    
    # Send notification
    success = await send_telegram_notification(sample_feedback)
    
    # Log result
    if success:
        logger.info("Telegram notification sent successfully!")
    else:
        logger.error("Failed to send Telegram notification.")
    
    return success

if __name__ == "__main__":
    asyncio.run(test_telegram_notification())
