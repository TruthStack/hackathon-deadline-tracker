"""
Telegram Notifier
Sends formatted alerts via Telegram Bot API.
"""

import requests
import time
from typing import Dict
from datetime import datetime, timedelta


class TelegramNotifier:
    """Sends hackathon deadline notifications via Telegram."""
    
    API_BASE = "https://api.telegram.org/bot"
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram notifier.
        
        Args:
            bot_token: Telegram bot token from @BotFather
            chat_id: Target chat ID to send messages to
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"{self.API_BASE}{bot_token}/sendMessage"
    
    def format_countdown(self, hours_remaining: float) -> str:
        """
        Format hours remaining into human-readable countdown.
        
        Args:
            hours_remaining: Hours until deadline
        
        Returns:
            Formatted string like "2h 15m" or "3d 4h"
        """
        if hours_remaining < 1:
            minutes = int(hours_remaining * 60)
            return f"{minutes}m"
        elif hours_remaining < 24:
            hours = int(hours_remaining)
            minutes = int((hours_remaining - hours) * 60)
            return f"{hours}h {minutes}m"
        else:
            days = int(hours_remaining / 24)
            hours = int(hours_remaining % 24)
            return f"{days}d {hours}h"
    
    def escape_markdown(self, text: str) -> str:
        """Escape special Markdown characters to prevent parsing errors."""
        special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in special_chars:
            text = text.replace(char, '\\' + char)
        return text
    
    def format_message(self, hackathon: Dict) -> str:
        """
        Format hackathon data into a notification message.
        
        Args:
            hackathon: Hackathon dictionary with urgency metadata
        
        Returns:
            Formatted message string
        """
        emoji = self._get_emoji(hackathon['alert_level'])
        # Escape special characters in name to prevent Markdown errors
        name = self.escape_markdown(hackathon['name'])
        countdown = self.format_countdown(hackathon['hours_remaining'])
        deadline = hackathon['deadline'].strftime('%Y-%m-%d %H:%M UTC')
        url = hackathon['url']
        level = hackathon['alert_level']
        
        # Build message
        message = f"{emoji} *{level} ALERT*\n\n"
        message += f"*{name}*\n\n"
        message += f"⏰ *{countdown} remaining*\n"
        message += f"📅 Deadline: {deadline}\n\n"
        
        if hackathon.get('prize_amount'):
            message += f"💰 Prize: ${hackathon['prize_amount']:,.0f}\n\n"
        
        message += f"🔗 [Submit Now]({url})\n\n"
        
        if level == "CRITICAL":
            message += "⚠️ *FINAL HOURS \\- SUBMIT NOW\\!*"
        elif level == "HIGH":
            message += "⚡ *Deadline approaching fast\\!*"
        
        return message
    
    def _get_emoji(self, level: str) -> str:
        """Get emoji for alert level."""
        emoji_map = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢",
            "IGNORE": "⚪"
        }
        return emoji_map.get(level, "⚪")
    
    def send_notification(self, hackathon: Dict, dry_run: bool = False) -> bool:
        """
        Send a notification for a hackathon.
        
        Args:
            hackathon: Hackathon dictionary with urgency metadata
            dry_run: If True, print message instead of sending
        
        Returns:
            True if successful, False otherwise
        """
        message = self.format_message(hackathon)
        
        if dry_run:
            print("\n" + "="*60)
            print("DRY RUN - Would send:")
            print(message)
            print("="*60 + "\n")
            return True
        
        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': False
            }
            
            response = requests.post(self.api_url, json=payload, timeout=15)
            
            # Check for Telegram API errors
            if response.status_code != 200:
                error_data = response.json()
                print(f"❌ Telegram API error for '{hackathon['name']}':")
                print(f"   Status: {response.status_code}")
                print(f"   Error: {error_data.get('description', 'Unknown error')}")
                return False
            
            print(f"✅ Sent: {hackathon['name']}")
            return True
        except requests.RequestException as e:
            print(f"❌ Network error sending '{hackathon['name']}': {e}")
            return False
    
    def send_batch(self, hackathons: list, dry_run: bool = False) -> Dict[str, int]:
        """
        Send notifications for multiple hackathons.
        
        Args:
            hackathons: List of hackathon dictionaries
            dry_run: If True, print messages instead of sending
        
        Returns:
            Dictionary with 'sent' and 'failed' counts
        """
        sent = 0
        failed = 0
        
        for i, hackathon in enumerate(hackathons):
            if self.send_notification(hackathon, dry_run=dry_run):
                sent += 1
            else:
                failed += 1
            
            # Add delay between messages to avoid Telegram rate limiting
            if i < len(hackathons) - 1 and not dry_run:
                time.sleep(2)
        
        return {'sent': sent, 'failed': failed}
    
    def test_connection(self) -> bool:
        """Test if bot token and chat ID are valid."""
        try:
            test_message = "🤖 HLUEAS Test - Connection successful!"
            payload = {
                'chat_id': self.chat_id,
                'text': test_message
            }
            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Connection test failed: {e}")
            return False


def send_notifications(
    hackathons: list,
    bot_token: str,
    chat_id: str,
    dry_run: bool = False
) -> Dict[str, int]:
    """Convenience function to send notifications."""
    notifier = TelegramNotifier(bot_token, chat_id)
    return notifier.send_batch(hackathons, dry_run=dry_run)
