"""
State Manager
Tracks notification history to prevent duplicate alerts.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional
from pathlib import Path


class StateManager:
    """Manages notification state persistence."""
    
    def __init__(self, state_file: str = "data/state.json"):
        """
        Initialize state manager.
        
        Args:
            state_file: Path to state JSON file
        """
        self.state_file = Path(state_file)
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load state from file, or return empty dict if not exists."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Failed to load state file: {e}")
                return {}
        return {}
    
    def _save_state(self):
        """Save state to file."""
        try:
            # Ensure directory exists
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2, default=str)
        except IOError as e:
            print(f"Error saving state file: {e}")
    
    def should_notify(self, hackathon: Dict) -> bool:
        """
        Check if a notification should be sent for this hackathon.
        
        Args:
            hackathon: Hackathon dictionary with urgency metadata
        
        Returns:
            True if notification should be sent, False otherwise
        """
        url = hackathon['url']
        alert_level = hackathon['alert_level']
        notification_interval = hackathon['notification_interval']
        
        # Check if we have state for this hackathon
        if url not in self.state:
            return True
        
        last_state = self.state[url]
        last_notified_str = last_state.get('last_notified')
        
        if not last_notified_str:
            return True
        
        # Parse last notification time
        try:
            last_notified = datetime.fromisoformat(last_notified_str)
        except ValueError:
            return True
        
        # Calculate time since last notification
        now = datetime.now()
        hours_since_last = (now - last_notified).total_seconds() / 3600
        
        # Check if enough time has passed based on notification interval
        return hours_since_last >= notification_interval
    
    def record_notification(self, hackathon: Dict):
        """
        Record that a notification was sent for this hackathon.
        
        Args:
            hackathon: Hackathon dictionary with urgency metadata
        """
        url = hackathon['url']
        
        self.state[url] = {
            'last_notified': datetime.now().isoformat(),
            'level': hackathon['alert_level'],
            'name': hackathon['name']
        }
        
        self._save_state()
    
    def filter_for_notification(self, hackathons: list) -> list:
        """
        Filter hackathons to only those that should receive notifications.
        
        Args:
            hackathons: List of hackathon dictionaries
        
        Returns:
            Filtered list of hackathons
        """
        return [h for h in hackathons if self.should_notify(h)]
    
    def cleanup_old_entries(self, days: int = 30):
        """
        Remove state entries older than specified days.
        
        Args:
            days: Number of days to keep entries
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        to_remove = []
        for url, data in self.state.items():
            last_notified_str = data.get('last_notified')
            if last_notified_str:
                try:
                    last_notified = datetime.fromisoformat(last_notified_str)
                    if last_notified < cutoff:
                        to_remove.append(url)
                except ValueError:
                    to_remove.append(url)
        
        for url in to_remove:
            del self.state[url]
        
        if to_remove:
            self._save_state()
            print(f"Cleaned up {len(to_remove)} old state entries")
    
    def get_summary(self) -> Dict:
        """Get summary of current state."""
        return {
            'total_tracked': len(self.state),
            'hackathons': list(self.state.keys())
        }


def manage_state(state_file: str = "data/state.json") -> StateManager:
    """Convenience function to create state manager."""
    return StateManager(state_file)
