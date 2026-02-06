"""
Urgency Engine
Computes urgency scores and determines escalation levels for hackathon deadlines.
"""

from datetime import datetime
from typing import List, Dict, Literal


AlertLevel = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "IGNORE"]


class UrgencyEngine:
    """Calculates urgency and priority for hackathon deadlines."""
    
    # Escalation thresholds (in hours)
    CRITICAL_THRESHOLD = 3
    HIGH_THRESHOLD = 12
    MEDIUM_THRESHOLD = 48
    LOW_THRESHOLD = 168  # 7 days
    
    # Notification intervals (in hours)
    INTERVALS = {
        "CRITICAL": 1,
        "HIGH": 3,
        "MEDIUM": 12,
        "LOW": 24,
        "IGNORE": 168,  # Weekly
    }
    
    def __init__(self, top_n: int = 3):
        """
        Initialize urgency engine.
        
        Args:
            top_n: Maximum number of hackathons to focus on
        """
        self.top_n = top_n
    
    def calculate_hours_remaining(self, deadline: datetime) -> float:
        """Calculate hours remaining until deadline."""
        now = datetime.now()
        delta = deadline - now
        return max(0, delta.total_seconds() / 3600)
    
    def get_alert_level(self, hours_remaining: float) -> AlertLevel:
        """
        Determine alert level based on hours remaining.
        
        Args:
            hours_remaining: Hours until deadline
        
        Returns:
            Alert level: CRITICAL, HIGH, MEDIUM, LOW, or IGNORE
        """
        if hours_remaining <= self.CRITICAL_THRESHOLD:
            return "CRITICAL"
        elif hours_remaining <= self.HIGH_THRESHOLD:
            return "HIGH"
        elif hours_remaining <= self.MEDIUM_THRESHOLD:
            return "MEDIUM"
        elif hours_remaining <= self.LOW_THRESHOLD:
            return "LOW"
        else:
            return "IGNORE"
    
    def get_notification_interval(self, level: AlertLevel) -> float:
        """Get notification interval in hours for a given alert level."""
        return self.INTERVALS[level]
    
    def calculate_priority_score(
        self,
        hours_remaining: float,
        prize_amount: float = 0,
        tag_match_score: float = 0
    ) -> float:
        """
        Calculate priority score for ranking hackathons.
        
        Formula:
            priority = (1.0 / max(hours_remaining, 1)) * 50
                     + (prize_normalized * 20)
                     + (tag_match_score * 30)
        
        Args:
            hours_remaining: Hours until deadline
            prize_amount: Prize amount in USD (normalized to 0-1)
            tag_match_score: Tag match score (0-1)
        
        Returns:
            Priority score (higher = more urgent/important)
        """
        # Time urgency component (50% weight)
        time_score = (1.0 / max(hours_remaining, 1)) * 50
        
        # Prize component (20% weight)
        # Normalize prize to 0-1 scale (assuming max prize of $10,000)
        prize_normalized = min(prize_amount / 10000, 1.0) if prize_amount else 0
        prize_score = prize_normalized * 20
        
        # Tag match component (30% weight)
        tag_score = tag_match_score * 30
        
        return time_score + prize_score + tag_score
    
    def process_hackathons(self, hackathons: List[Dict]) -> List[Dict]:
        """
        Process hackathons: calculate urgency, priority, and filter top N.
        
        Args:
            hackathons: List of hackathon dictionaries
        
        Returns:
            Processed hackathons with urgency metadata, sorted by priority
        """
        processed = []
        
        for hackathon in hackathons:
            hours_remaining = self.calculate_hours_remaining(hackathon['deadline'])
            alert_level = self.get_alert_level(hours_remaining)
            
            # Skip if in IGNORE level
            if alert_level == "IGNORE":
                continue
            
            priority_score = self.calculate_priority_score(
                hours_remaining=hours_remaining,
                prize_amount=hackathon.get('prize_amount', 0),
                tag_match_score=0  # TODO: Implement tag matching
            )
            
            processed.append({
                **hackathon,
                'hours_remaining': hours_remaining,
                'alert_level': alert_level,
                'priority_score': priority_score,
                'notification_interval': self.get_notification_interval(alert_level)
            })
        
        # Sort by priority (highest first)
        processed.sort(key=lambda h: h['priority_score'], reverse=True)
        
        # Return top N
        return processed[:self.top_n]
    
    def get_emoji_for_level(self, level: AlertLevel) -> str:
        """Get emoji indicator for alert level."""
        emoji_map = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢",
            "IGNORE": "⚪"
        }
        return emoji_map.get(level, "⚪")


def compute_urgency(hackathons: List[Dict], top_n: int = 3) -> List[Dict]:
    """Convenience function to compute urgency for hackathons."""
    engine = UrgencyEngine(top_n=top_n)
    return engine.process_hackathons(hackathons)
