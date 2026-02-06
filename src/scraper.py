"""
Devpost Profile Scraper
Extracts registered hackathons from a Devpost user profile.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser as date_parser
from typing import List, Dict, Optional
import re


class DevpostScraper:
    """Scrapes hackathon data from Devpost user profiles."""
    
    BASE_URL = "https://devpost.com"
    
    def __init__(self, username: str):
        self.username = username
        self.challenges_url = f"{self.BASE_URL}/{username}/challenges"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def fetch_challenges_page(self, page: int = 1) -> str:
        """Fetch a page of user's hackathon challenges."""
        try:
            url = self.challenges_url if page == 1 else f"{self.challenges_url}?page={page}"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch Devpost challenges: {e}")
    
    def extract_hackathons(self, html: str) -> List[Dict]:
        """
        Extract hackathon information from challenges page HTML.
        
        Returns:
            List of hackathon dictionaries with keys:
            - name: str
            - url: str
            - deadline: datetime (UTC)
            - prize_amount: float | None
            - location: str
        """
        soup = BeautifulSoup(html, 'html.parser')
        hackathons = []
        
        # Find challenge links - they are <a> tags with specific structure
        challenge_links = soup.find_all('a', href=lambda x: x and 'devpost.com' in str(x) and 'ref_content' in str(x))
        
        for link in challenge_links:
            try:
                hackathon = self._parse_challenge_link(link)
                if hackathon and hackathon.get('deadline'):
                    hackathons.append(hackathon)
            except Exception as e:
                # Log but don't fail on individual parse errors
                print(f"Warning: Failed to parse hackathon: {e}")
                continue
        
        # Deduplicate by URL
        seen_urls = set()
        unique_hackathons = []
        for h in hackathons:
            if h['url'] not in seen_urls:
                seen_urls.add(h['url'])
                unique_hackathons.append(h)
        
        return unique_hackathons
    
    def _parse_challenge_link(self, link) -> Optional[Dict]:
        """Parse a single challenge link element."""
        # Get the full text content of the link
        full_text = link.get_text(' ', strip=True)
        
        # Skip navigation and footer links
        if not full_text or len(full_text) < 20:
            return None
        if 'Browse hackathons' in full_text or 'Host a hackathon' in full_text:
            return None
        
        # Extract URL
        url = link.get('href', '')
        if not url or 'ref_content' not in url:
            return None
        
        # Clean URL (remove tracking params)
        url = url.split('?')[0]
        if not url.startswith('http'):
            url = self.BASE_URL + url
        
        # Extract name - usually the first meaningful text or h2/h5 element
        name_elem = link.find(['h2', 'h5', 'h3'])
        if name_elem:
            name = name_elem.get_text(strip=True)
        else:
            # Find first line of text
            name = full_text.split('\n')[0].strip()
            # Clean up common prefixes
            name = re.sub(r'^(Featured\s*)?', '', name).strip()
        
        if not name or len(name) < 3:
            return None
        
        # Extract deadline from text content
        deadline = self._extract_deadline_from_text(full_text)
        
        # Extract prize amount
        prize_amount = self._extract_prize_from_text(full_text)
        
        # Extract location
        location = self._extract_location_from_text(full_text)
        
        return {
            'name': name,
            'url': url,
            'deadline': deadline,
            'prize_amount': prize_amount,
            'location': location,
            'tags': []
        }
    
    def _extract_deadline_from_text(self, text: str) -> Optional[datetime]:
        """Extract and normalize deadline from text content."""
        # Pattern: "Mar 16, 2026 08:00 PM EDT to submit"
        submit_pattern = r'([A-Z][a-z]{2}\s+\d{1,2},?\s+\d{4}\s+\d{1,2}:\d{2}\s*(?:AM|PM)\s*[A-Z]{2,4})\s+to submit'
        match = re.search(submit_pattern, text)
        if match:
            deadline_str = match.group(1)
            try:
                return date_parser.parse(deadline_str)
            except Exception:
                pass
        
        # Pattern: "Feb 2 – 20, 2026" (date range, use end date)
        range_pattern = r'([A-Z][a-z]{2}\s+\d{1,2})\s*[–-]\s*(\d{1,2}),?\s*(\d{4})'
        match = re.search(range_pattern, text)
        if match:
            try:
                end_day = match.group(2)
                year = match.group(3)
                month = match.group(1).split()[0]
                deadline_str = f"{month} {end_day}, {year} 11:59 PM"
                return date_parser.parse(deadline_str)
            except Exception:
                pass
        
        # Pattern: "Feb 09, 2026 08:00 PM EST"
        simple_pattern = r'([A-Z][a-z]{2}\s+\d{1,2},?\s+\d{4}\s+\d{1,2}:\d{2}\s*(?:AM|PM)\s*[A-Z]{2,4})'
        match = re.search(simple_pattern, text)
        if match:
            deadline_str = match.group(1)
            try:
                return date_parser.parse(deadline_str)
            except Exception:
                pass
        
        return None
    
    def _extract_prize_from_text(self, text: str) -> Optional[float]:
        """Extract prize amount from text content."""
        # Normalize text to lower case for easier matching
        text_lower = text.lower()
        
        # Common currencies cleanup map
        currencies = {
            '$': 1.0,  'usd': 1.0,
            '€': 1.08, 'eur': 1.08,
            '£': 1.25, 'gbp': 1.25,
            '₹': 0.012, 'inr': 0.012,
            'c$': 0.74, 'cad': 0.74,
            'a$': 0.65, 'aud': 0.65
        }
        
        # Pattern for "Prize pool: $50,000" or "$50,000 in prizes"
        # Matches: $50,000, 50,000 USD, 50k USD
        # Group 1: Currency prefix, Group 2: Amount, Group 3: Modifier (k/m), Group 4: Currency suffix
        prize_pattern = r'([$€£₹])?\s*([0-9,]+(?:\.[0-9]{1,2})?)\s*(k|m|mil|million)?\s*([a-z]{3})?'
        
        # Find all matches
        matches = re.finditer(prize_pattern, text_lower)
        
        max_prize = 0.0
        
        for match in matches:
            prefix, amount_str, modifier, suffix = match.groups()
            
            # Skip if no currency indicator found (avoid matching years like 2026)
            if not prefix and not suffix and 'prize' not in text_lower:
                continue
            
            # Skip if suffix isn't a known currency
            if suffix and suffix not in currencies:
                continue
                
            try:
                base_amount = float(amount_str.replace(',', ''))
                
                # Handle modifiers
                if modifier:
                    if modifier in ['k']:
                        base_amount *= 1000
                    elif modifier in ['m', 'mil', 'million']:
                        base_amount *= 1000000
                
                # Determine exchange rate
                rate = 1.0
                if prefix and prefix in currencies:
                    rate = currencies[prefix]
                elif suffix and suffix in currencies:
                    rate = currencies[suffix]
                
                val = base_amount * rate
                
                # Filter out unreasonably small numbers (likely dates or counts)
                if val > 100:
                    max_prize = max(max_prize, val)
                    
            except ValueError:
                continue
                
        return max_prize if max_prize > 0 else None
    
    def _extract_location_from_text(self, text: str) -> str:
        """Extract location from text content."""
        # Look for "Online" or location patterns
        if 'Online' in text:
            return 'Online'
        
        # Try to find location patterns like "City, Country"
        location_pattern = r'(?:Featured\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*(?:[A-Z][a-z]+|[A-Z]{2,})\s*(?:,\s*[A-Z][a-z]+)?)'
        match = re.search(location_pattern, text)
        if match:
            return match.group(1)
        
        return 'Unknown'
    
    def get_active_hackathons(self, max_pages: int = 3) -> List[Dict]:
        """
        Main method: Fetch all pages and extract active hackathons.
        
        Args:
            max_pages: Maximum number of pages to scrape
        
        Returns:
            List of hackathons with future deadlines, sorted by deadline.
        """
        all_hackathons = []
        
        for page in range(1, max_pages + 1):
            try:
                html = self.fetch_challenges_page(page)
                hackathons = self.extract_hackathons(html)
                
                if not hackathons:
                    break
                    
                all_hackathons.extend(hackathons)
            except Exception as e:
                print(f"Warning: Failed to fetch page {page}: {e}")
                break
        
        # Filter to only future hackathons
        now = datetime.now()
        active = [h for h in all_hackathons if h.get('deadline') and h['deadline'] > now]
        
        # Deduplicate by URL
        seen = set()
        unique = []
        for h in active:
            if h['url'] not in seen:
                seen.add(h['url'])
                unique.append(h)
        
        # Sort by deadline (earliest first)
        unique.sort(key=lambda h: h['deadline'])
        
        return unique


def scrape_devpost(username: str) -> List[Dict]:
    """Convenience function to scrape Devpost profile."""
    scraper = DevpostScraper(username)
    return scraper.get_active_hackathons()
