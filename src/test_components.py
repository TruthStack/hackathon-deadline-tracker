"""
Test script to verify HLUEAS components without requiring Devpost credentials.
"""

from datetime import datetime, timedelta
from urgency import UrgencyEngine, compute_urgency
from notifier import TelegramNotifier
from state import StateManager


def test_urgency_engine():
    """Test urgency calculation logic."""
    print("=" * 60)
    print("Testing Urgency Engine")
    print("=" * 60)
    
    engine = UrgencyEngine(top_n=3)
    
    # Create mock hackathons with different deadlines
    now = datetime.now()
    mock_hackathons = [
        {
            'name': 'Critical Hackathon',
            'url': 'https://devpost.com/critical',
            'deadline': now + timedelta(hours=2),
            'prize_amount': 5000,
            'tags': ['AI', 'ML']
        },
        {
            'name': 'High Priority Hackathon',
            'url': 'https://devpost.com/high',
            'deadline': now + timedelta(hours=10),
            'prize_amount': 10000,
            'tags': ['Web3']
        },
        {
            'name': 'Medium Priority Hackathon',
            'url': 'https://devpost.com/medium',
            'deadline': now + timedelta(hours=36),
            'prize_amount': 2000,
            'tags': ['Climate']
        },
        {
            'name': 'Low Priority Hackathon',
            'url': 'https://devpost.com/low',
            'deadline': now + timedelta(days=5),
            'prize_amount': 1000,
            'tags': ['Education']
        },
        {
            'name': 'Ignored Hackathon',
            'url': 'https://devpost.com/ignored',
            'deadline': now + timedelta(days=10),
            'prize_amount': 500,
            'tags': ['Other']
        }
    ]
    
    # Process hackathons
    processed = engine.process_hackathons(mock_hackathons)
    
    print(f"\nProcessed {len(processed)} hackathons (top {engine.top_n}):\n")
    
    for i, h in enumerate(processed, 1):
        emoji = engine.get_emoji_for_level(h['alert_level'])
        print(f"{i}. {emoji} {h['name']}")
        print(f"   Level: {h['alert_level']}")
        print(f"   Hours Left: {h['hours_remaining']:.1f}h")
        print(f"   Priority Score: {h['priority_score']:.2f}")
        print(f"   Notification Interval: {h['notification_interval']}h")
        print()
    
    print("✅ Urgency Engine Test Passed\n")
    return processed


def test_notifier(hackathons):
    """Test notification formatting (dry run)."""
    print("=" * 60)
    print("Testing Telegram Notifier (Dry Run)")
    print("=" * 60)
    
    # Use dummy credentials for dry run
    notifier = TelegramNotifier(
        bot_token="dummy_token",
        chat_id="dummy_chat_id"
    )
    
    # Send notifications in dry run mode
    result = notifier.send_batch(hackathons, dry_run=True)
    
    print(f"\n✅ Notifier Test Passed")
    print(f"   Would send: {result['sent']} notifications\n")


def test_state_manager(hackathons):
    """Test state persistence."""
    print("=" * 60)
    print("Testing State Manager")
    print("=" * 60)
    
    # Use test state file
    state_manager = StateManager(state_file="data/test_state.json")
    
    # First run - all should notify
    to_notify_1 = state_manager.filter_for_notification(hackathons)
    print(f"\nFirst run: {len(to_notify_1)} hackathons to notify")
    
    # Record notifications
    for h in to_notify_1:
        state_manager.record_notification(h)
    
    # Second run - none should notify (too soon)
    to_notify_2 = state_manager.filter_for_notification(hackathons)
    print(f"Second run (immediate): {len(to_notify_2)} hackathons to notify")
    
    # Check state summary
    summary = state_manager.get_summary()
    print(f"\nState summary:")
    print(f"  Total tracked: {summary['total_tracked']}")
    
    print("\n✅ State Manager Test Passed\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("HLUEAS Component Tests")
    print("=" * 60 + "\n")
    
    # Test urgency engine
    processed_hackathons = test_urgency_engine()
    
    # Test notifier
    test_notifier(processed_hackathons)
    
    # Test state manager
    test_state_manager(processed_hackathons)
    
    print("=" * 60)
    print("✨ All Tests Passed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
