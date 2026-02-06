"""
HLUEAS - Hackathon Lifecycle Urgency & Execution Automation System
Main orchestrator that coordinates scraping, urgency calculation, and notifications.
"""

import os
import sys
from dotenv import load_dotenv
from typing import Optional

from scraper import scrape_devpost
from urgency import compute_urgency
from notifier import send_notifications
from state import StateManager


def load_config() -> dict:
    """Load configuration from environment variables."""
    load_dotenv()
    
    config = {
        'devpost_username': os.getenv('DEVPOST_USERNAME'),
        'telegram_bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
        'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID'),
        'top_n': int(os.getenv('TOP_N_HACKATHONS', '3')),
        'dry_run': os.getenv('DRY_RUN', 'false').lower() == 'true'
    }
    
    # Validate required config
    required = ['devpost_username', 'telegram_bot_token', 'telegram_chat_id']
    missing = [k for k in required if not config[k]]
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    return config


def main(dry_run: Optional[bool] = None, force: bool = False):
    """
    Main execution flow.
    
    Args:
        dry_run: Override dry_run setting from environment
        force: If True, skip state check and always send notifications (for manual runs)
    """
    print("=" * 60)
    print("HLUEAS - Hackathon Deadline Watch")
    print("=" * 60)
    
    # Load configuration
    try:
        config = load_config()
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\nPlease create a .env file with required variables.")
        print("See .env.example for template.")
        sys.exit(1)
    
    # Override dry_run if specified
    if dry_run is not None:
        config['dry_run'] = dry_run
    
    print(f"\n📋 Configuration:")
    print(f"  Devpost User: {config['devpost_username']}")
    print(f"  Top N Hackathons: {config['top_n']}")
    print(f"  Dry Run: {config['dry_run']}")
    print(f"  Force Mode: {force}")
    print()
    
    # Step 1: Scrape Devpost profile
    print("🔍 Scraping Devpost profile...")
    try:
        hackathons = scrape_devpost(config['devpost_username'])
        print(f"✅ Found {len(hackathons)} active hackathons")
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
        sys.exit(1)
    
    if not hackathons:
        print("\n✨ No active hackathons found. You're all clear!")
        return
    
    # Step 2: Compute urgency and priority
    print("\n⚡ Computing urgency scores...")
    urgent_hackathons = compute_urgency(hackathons, top_n=config['top_n'])
    print(f"✅ {len(urgent_hackathons)} hackathons require attention")
    
    if not urgent_hackathons:
        print("\n✨ No urgent deadlines. All hackathons are >7 days away.")
        return
    
    # Display urgency summary
    print("\n📊 Urgency Summary:")
    for i, h in enumerate(urgent_hackathons, 1):
        emoji = "🔴" if h['alert_level'] == "CRITICAL" else \
                "🟠" if h['alert_level'] == "HIGH" else \
                "🟡" if h['alert_level'] == "MEDIUM" else "🟢"
        print(f"  {i}. {emoji} {h['name']}")
        print(f"     Level: {h['alert_level']} | Hours Left: {h['hours_remaining']:.1f}h")
    
    # Step 3: Filter based on notification state (skip if force mode)
    state_manager = StateManager()
    
    if force:
        print("\n🔔 Force mode enabled - sending all notifications...")
        to_notify = urgent_hackathons
    else:
        print("\n🔔 Checking notification state...")
        to_notify = []
        skipped = []
        for h in urgent_hackathons:
            if state_manager.should_notify(h):
                to_notify.append(h)
            else:
                skipped.append(h)
        
        if skipped:
            print(f"⚠️  Skipping {len(skipped)} hackathons (recently notified):")
            for h in skipped:
                print(f"   - {h['name']} ({h['hours_remaining']:.1f}h left)")
    
    print(f"✅ {len(to_notify)} hackathons need notification")
    
    if not to_notify:
        print("\n✨ All notifications already sent recently.")
        print("💡 Tip: Use --force flag to send notifications anyway.")
        return
    
    # Step 4: Send notifications
    print("\n📤 Sending notifications...")
    result = send_notifications(
        to_notify,
        config['telegram_bot_token'],
        config['telegram_chat_id'],
        dry_run=config['dry_run']
    )
    
    if config['dry_run']:
        print(f"\n✅ DRY RUN: Would send {result['sent']} notifications")
    else:
        print(f"\n✅ Sent {result['sent']} notifications")
        if result['failed'] > 0:
            print(f"⚠️  {result['failed']} notifications failed")
    
    # Step 5: Update state (only if not force mode, to preserve interval logic for GitHub Actions)
    if not config['dry_run'] and not force:
        print("\n💾 Updating state...")
        for hackathon in to_notify:
            state_manager.record_notification(hackathon)
        print("✅ State updated")
    elif force:
        print("\n💡 Force mode: State not updated (intervals preserved for scheduled runs)")
    
    # Cleanup old state entries
    state_manager.cleanup_old_entries(days=30)
    
    print("\n" + "=" * 60)
    print("✨ HLUEAS run complete!")
    print("=" * 60)


if __name__ == "__main__":
    # Check for flags
    dry_run = '--dry-run' in sys.argv
    force = '--force' in sys.argv
    
    main(dry_run=dry_run, force=force)
