import logging
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from datetime import datetime
import os
from ..config import (
    EMAIL_ENABLED, 
    EMAIL_HOST, 
    EMAIL_PORT, 
    EMAIL_USERNAME, 
    EMAIL_PASSWORD, 
    EMAIL_FROM, 
    EMAIL_TO,
    TELEGRAM_ENABLED,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID
)

# Configure logging
logger = logging.getLogger(__name__)

def format_feedback_for_email(feedback: Dict[str, Any]) -> str:
    """Format feedback data for email notification with detailed information."""
    created_at = feedback.get('created_at', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #333366; }}
            .feedback-item {{ margin-bottom: 10px; }}
            .label {{ font-weight: bold; }}
            .theme {{ color: #ff6600; font-weight: bold; }}
            .footer {{ margin-top: 30px; font-size: 12px; color: #999; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>New Feedback Received</h1>
            
            <div class="feedback-item">
                <span class="label">Theme:</span> 
                <span class="theme">{feedback.get('theme', 'Not specified')}</span>
            </div>
            
            <div class="feedback-item">
                <span class="label">From:</span> {feedback.get('full_name', 'Not provided')}
            </div>
            
            <div class="feedback-item">
                <span class="label">Email:</span> {feedback.get('email', 'Not provided')}
            </div>
            
            <div class="feedback-item">
                <span class="label">Phone:</span> {feedback.get('phone_number', 'Not provided')}
            </div>
            
            <div class="feedback-item">
                <span class="label">Message:</span>
                <p>{feedback.get('text', 'No message').replace('\n', '<br>')}</p>
            </div>
            
            <div class="feedback-item">
                <span class="label">Received at:</span> {created_at}
            </div>
            
            <div class="footer">
                This is an automated message from your website feedback system.
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

def format_feedback_for_telegram(feedback: Dict[str, Any]) -> str:
    """Format feedback data for Telegram notification with concise information."""
    created_at = feedback.get('created_at', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')
    
    # Create a concise message for Telegram
    message = f"""
📬 *New Feedback*
🏷️ *Theme:* {feedback.get('theme', 'Not specified')}
👤 *From:* {feedback.get('full_name', 'Not provided')}
📱 *Phone:* {feedback.get('phone_number', 'Not provided')}
📧 *Email:* {feedback.get('email', 'Not provided')}
📝 *Message:* 
{feedback.get('text', 'No message')}

⏰ Received at: {created_at}
    """
    
    return message

async def send_email_notification(feedback: Dict[str, Any]) -> bool:
    """Send feedback notification via email."""
    if not EMAIL_ENABLED:
        logger.info("Email notifications are disabled")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"New Feedback: {feedback.get('theme', 'Website Feedback')}"
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        
        # Create HTML content
        html_content = format_feedback_for_email(feedback)
        msg.attach(MIMEText(html_content, 'html'))
        
        # Connect to SMTP server and send email
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            if EMAIL_USERNAME and EMAIL_PASSWORD:
                server.starttls()
                server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
            
            server.send_message(msg)
        
        logger.info(f"Email notification sent successfully for feedback ID: {feedback.get('id')}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send email notification: {str(e)}", exc_info=True)
        return False

async def send_telegram_notification(feedback: Dict[str, Any]) -> bool:
    """Send feedback notification via Telegram."""
    if not TELEGRAM_ENABLED or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.info("Telegram notifications are disabled or not configured")
        return False
    
    try:
        # Format message for Telegram
        message = format_feedback_for_telegram(feedback)
        
        # Send message to Telegram
        api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(api_url, json=payload)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        logger.info(f"Telegram notification sent successfully for feedback ID: {feedback.get('id')}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {str(e)}", exc_info=True)
        return False

async def send_feedback_notifications(feedback: Dict[str, Any]) -> Dict[str, bool]:
    """Send feedback notifications to all configured channels."""
    results = {
        "email": False,
        "telegram": False
    }
    
    # Send email notification
    results["email"] = await send_email_notification(feedback)
    
    # Send Telegram notification
    results["telegram"] = await send_telegram_notification(feedback)
    
    return results
