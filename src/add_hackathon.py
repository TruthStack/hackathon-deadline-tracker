"""
Add Hackathon script
Adds a new hackathon URL to the external tracking list.
"""

import argparse
import json
import os
from pathlib import Path
from datetime import datetime
from generic_scraper import GenericScraper

def load_external(file_path: Path):
    if not file_path.exists():
        return []
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception:
        return []

def save_external(file_path: Path, data: list):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def main():
    parser = argparse.ArgumentParser(description="Add external hackathon to tracking")
    parser.add_argument("url", help="URL of the hackathon")
    parser.add_argument("--deadline", help="Manual deadline (YYYY-MM-DD)", default=None)
    args = parser.parse_args()
    
    print(f"🔍 Scrapeing metdata from: {args.url}")
    scraper = GenericScraper()
    hackathon = scraper.scrape(args.url)
    
    if not hackathon:
        print("❌ Failed to scrape URL.")
        return
    
    # Override deadline if provided manually
    if args.deadline:
        try:
            hackathon['deadline'] = datetime.strptime(args.deadline, "%Y-%m-%d").replace(hour=23, minute=59)
        except ValueError:
            print("❌ Invalid date format. Use YYYY-MM-DD")
            return

    print(f"✅ Found: {hackathon['name']}")
    print(f"📅 Deadline: {hackathon['deadline']}")
    
    # Save to JSON
    data_dir = Path(__file__).parent.parent / 'data'
    external_file = data_dir / 'external.json'
    
    data = load_external(external_file)
    
    # Update if exists, else append
    existing = next((item for item in data if item['url'] == hackathon['url']), None)
    if existing:
        existing.update(hackathon)
        print("Updated existing entry.")
    else:
        data.append(hackathon)
        print("Added new entry.")
    
    save_external(external_file, data)
    print("💾 Saved to data/external.json")

if __name__ == "__main__":
    main()
