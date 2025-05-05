import logging
import httpx
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from ..config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_ENABLED

# Configure logging
logger = logging.getLogger(__name__)

def format_feedback_for_telegram(feedback: Dict[str, Any]) -> str:
    """Format feedback data for Telegram notification with concise information."""
    created_at = feedback.get('created_at', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')
    
    # Create a concise message for Telegram with effective formatting
    message = f"""
📬 *New Feedback Received*

🏷️ *Theme:* {feedback.get('theme', 'Not specified')}
👤 *From:* {feedback.get('full_name', 'Not provided')}

📱 *Contact:* {feedback.get('phone_number', 'Not provided')}
📧 *Email:* {feedback.get('email', 'Not provided')}

📝 *Message:*
_{feedback.get('text', 'No message')}_

⏰ Received at: {created_at}
    """
    
    return message

async def get_bot_info() -> Tuple[bool, str]:
    """Get information about the bot to verify the token is valid."""
    try:
        # Check if token is configured
        if not TELEGRAM_BOT_TOKEN:
            return False, "Telegram bot token is not configured"
            
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        logger.info(f"Checking bot info with token: {TELEGRAM_BOT_TOKEN[:5]}...")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10)
        
        if response.status_code != 200:
            return False, f"Failed to get bot info: {response.text}"
        
        data = response.json()
        if not data.get('ok', False):
            return False, f"Telegram API error: {data.get('description', 'Unknown error')}"
        
        bot_info = data.get('result', {})
        return True, f"Bot verified: @{bot_info.get('username')} (ID: {bot_info.get('id')})"
    
    except Exception as e:
        return False, f"Error checking bot info: {str(e)}"

async def send_telegram_notification(feedback: Dict[str, Any]) -> bool:
    """Send feedback notification via Telegram."""
    # Check if Telegram notifications are enabled
    if not TELEGRAM_ENABLED:
        logger.info("Telegram notifications are disabled in configuration")
        return False
        
    # Check if token and chat ID are configured
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Telegram bot token is not configured")
        return False
        
    if not TELEGRAM_CHAT_ID:
        logger.error("Telegram chat ID is not configured")
        return False
    
    logger.info(f"Using Telegram bot token: {TELEGRAM_BOT_TOKEN[:5]}... and chat ID: {TELEGRAM_CHAT_ID}")
    
    try:
        # First, verify the bot token is valid
        bot_valid, bot_message = await get_bot_info()
        if not bot_valid:
            logger.error(bot_message)
            return False
        else:
            logger.info(bot_message)
        
        # Format message for Telegram
        message = format_feedback_for_telegram(feedback)
        
        # Send message to Telegram
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        logger.info(f"Sending message to chat ID: {TELEGRAM_CHAT_ID}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10)
        
        # Check for HTTP errors
        if response.status_code != 200:
            error_text = response.text
            logger.error(f"Telegram API error: {response.status_code} - {error_text}")
            
            # Provide more specific guidance based on the error
            if "chat not found" in error_text:
                logger.error("The chat ID is incorrect or the bot is not a member of the chat.")
                logger.error("Please make sure:")
                logger.error("1. The chat ID is correct")
                logger.error("2. The bot has been added to the chat/group")
                logger.error("3. For groups, make sure the ID starts with a negative sign")
            
            return False
        
        # Parse response to check for Telegram API errors
        response_data = response.json()
        if not response_data.get('ok', False):
            logger.error(f"Telegram API returned error: {response_data.get('description', 'Unknown error')}")
            return False
        
        logger.info(f"Telegram notification sent successfully for feedback ID: {feedback.get('id')}")
        return True
    
    except Exception as e:
        logger.error(f"Error sending Telegram notification: {str(e)}", exc_info=True)
        return False
