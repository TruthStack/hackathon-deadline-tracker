"""
Quick hackathon deadline report - generates detailed output without Telegram.
"""

import os
from dotenv import load_dotenv
from datetime import datetime

from scraper import scrape_devpost
from urgency import UrgencyEngine


def generate_report():
    """Generate a detailed hackathon deadline report."""
    load_dotenv()
    
    username = os.getenv('DEVPOST_USERNAME', 'truthcodeexplorer')
    now = datetime.now()
    
    print("=" * 80)
    print("🏆 HACKATHON DEADLINE REPORT")
    print(f"📅 Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"👤 User: {username}")
    print("=" * 80)
    
    # Scrape hackathons
    print("\n🔍 Fetching hackathons from Devpost...")
    try:
        hackathons = scrape_devpost(username)
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print(f"✅ Found {len(hackathons)} active hackathons\n")
    
    if not hackathons:
        print("No active hackathons found!")
        return
    
    # Process with urgency engine
    engine = UrgencyEngine(top_n=50)  # Show all
    
    # Group by urgency level
    critical = []
    high = []
    medium = []
    low = []
    
    for h in hackathons:
        hours = engine.calculate_hours_remaining(h['deadline'])
        level = engine.get_alert_level(hours)
        h['hours_remaining'] = hours
        h['alert_level'] = level
        
        if level == "CRITICAL":
            critical.append(h)
        elif level == "HIGH":
            high.append(h)
        elif level == "MEDIUM":
            medium.append(h)
        elif level == "LOW":
            low.append(h)
    
    def format_countdown(hours):
        if hours < 1:
            return f"{int(hours * 60)}m"
        elif hours < 24:
            return f"{int(hours)}h"
        else:
            days = int(hours / 24)
            remaining_hours = int(hours % 24)
            return f"{days}d {remaining_hours}h"
    
    def format_prize(amount):
        if amount is None:
            return "TBA"
        elif amount > 1000:
            return f"${amount/1000:.0f}K"
        else:
            return f"${amount:.0f}"
    
    def print_section(title, emoji, hackathons):
        if not hackathons:
            return
        print(f"\n{emoji} {title} ({len(hackathons)} hackathons)")
        print("-" * 80)
        for i, h in enumerate(hackathons, 1):
            countdown = format_countdown(h['hours_remaining'])
            deadline = h['deadline'].strftime('%b %d, %Y %I:%M %p')
            prize = format_prize(h.get('prize_amount'))
            print(f"  {i}. {h['name'][:50]}")
            print(f"     ⏰ {countdown} remaining | 📅 {deadline} | 💰 {prize}")
            print(f"     🔗 {h['url']}")
            print()
    
    print_section("🔴 CRITICAL - Submit NOW (≤3h)", "🔴", critical)
    print_section("🟠 HIGH PRIORITY - Closing Soon (≤12h)", "🟠", high)
    print_section("🟡 MEDIUM PRIORITY - Approaching (≤48h)", "🟡", medium)
    print_section("🟢 LOW PRIORITY - Coming Up (≤7 days)", "🟢", low)
    
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"  🔴 Critical:  {len(critical)}")
    print(f"  🟠 High:      {len(high)}")
    print(f"  🟡 Medium:    {len(medium)}")
    print(f"  🟢 Low:       {len(low)}")
    print(f"  📋 Total Active: {len(hackathons)}")
    print("=" * 80)


if __name__ == "__main__":
    generate_report()
