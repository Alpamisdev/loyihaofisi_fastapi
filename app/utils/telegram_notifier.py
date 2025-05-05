import logging
import httpx
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Telegram configuration
BOT_TOKEN = "5952272127:AAFJ1lkN1kxsCy2vRxhJ5kIidioWvXuV3LQ"
CHAT_ID = -1002283248375

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

async def send_telegram_notification(feedback: Dict[str, Any]) -> bool:
    """Send feedback notification via Telegram."""
    try:
        # Format message for Telegram
        message = format_feedback_for_telegram(feedback)
        
        # Send message to Telegram
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10)
        
        # Check for HTTP errors
        if response.status_code != 200:
            logger.error(f"Telegram API error: {response.status_code} - {response.text}")
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
