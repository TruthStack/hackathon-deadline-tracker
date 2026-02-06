"""
Generic Hackathon Scraper
Extracts basic metadata (title, deadline) from arbitrary hackathon URLs.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dateutil import parser as date_parser
import re
from typing import Optional, Dict

class GenericScraper:
    """Scrapes metadata from generic hackathon pages."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def scrape(self, url: str) -> Optional[Dict]:
        """Scrape title and deadline from URL."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            
            # 1. Extract Title
            title = self._extract_title(soup)
            if not title:
                print(f"Could not extract title from {url}")
                return None
                
            # 2. Extract Deadline (Best Effort)
            deadline = self._extract_deadline(soup.get_text())
            
            # Default if not found
            if not deadline:
                deadline = datetime.now() + timedelta(days=30)
                print(f"⚠️  Could not find deadline for '{title}', defaulting to 30 days.")
            
            return {
                'name': title,
                'url': url,
                'deadline': deadline,
                'prize_amount': 0, # Hard to parse generically without specific selectors
                'location': 'Online',
                'tags': ['External']
            }
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract title from meta tags or title tag."""
        # Try OpenGraph title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content']
            
        # Try standard title
        if soup.title:
            return soup.title.string.strip()
            
        return None
    
    def _extract_deadline(self, text: str) -> Optional[datetime]:
        """Attempt to find date patterns in text."""
        # Look for "Deadline: <Date>"
        deadline_patterns = [
            r'Deadline:\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'Ends on\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'Submission deadline:\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})'
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return date_parser.parse(match.group(1))
                except Exception:
                    continue
        
        return None
