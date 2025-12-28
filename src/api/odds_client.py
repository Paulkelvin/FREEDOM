"""
The Odds API Client with rate limiting and error handling
"""
import requests
import time
from typing import Dict, List, Optional
from datetime import datetime
from config.settings import (
    ODDS_API_KEY, ODDS_API_BASE_URL, REGIONS, SPORTS, MARKETS,
    ODDS_FORMAT, MAX_MONTHLY_REQUESTS, REQUEST_RETRY_DELAY
)
from src.utils.logger import setup_logger


class OddsAPIClient:
    """
    Client for interacting with The Odds API (the-odds-api.com)
    Handles rate limiting, retries, and quota tracking
    """
    
    def __init__(self):
        self.api_key = ODDS_API_KEY
        self.base_url = ODDS_API_BASE_URL
        self.requests_made = 0
        self.quota_used = 0
        self.logger = setup_logger()
        
    def get_sports_odds(self, sport: str) -> Optional[List[Dict]]:
        """
        Fetch odds for a specific sport
        
        Args:
            sport: Sport key (e.g., 'basketball_nba', 'soccer_epl')
            
        Returns:
            List of event dictionaries with odds data, or None on failure
        """
        # Check quota before making request
        if self.requests_made >= MAX_MONTHLY_REQUESTS:
            self.logger.error(f"❌ Monthly API quota exceeded ({MAX_MONTHLY_REQUESTS} requests)")
            return None
        
        endpoint = f"{self.base_url}/sports/{sport}/odds"
        params = {
            'apiKey': self.api_key,
            'regions': ','.join(REGIONS),
            'markets': ','.join(MARKETS),
            'oddsFormat': ODDS_FORMAT,
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Fetching odds for {sport} (Attempt {attempt + 1}/{max_retries})...")
                response = requests.get(endpoint, params=params, timeout=10)
                
                # Track quota from response headers
                if 'x-requests-used' in response.headers:
                    self.quota_used = int(response.headers['x-requests-used'])
                if 'x-requests-remaining' in response.headers:
                    quota_remaining = int(response.headers['x-requests-remaining'])
                    self.logger.info(f"📊 API Quota: {self.quota_used} used | {quota_remaining} remaining")
                
                response.raise_for_status()
                self.requests_made += 1
                
                events = response.json()
                self.logger.info(f"✅ Fetched {len(events)} events for {sport}")
                return events
                
            except requests.exceptions.HTTPError as e:
                if response.status_code == 401:
                    self.logger.error(f"❌ Invalid API Key. Check your .env file.")
                    return None
                elif response.status_code == 429:
                    self.logger.warning(f"⚠️ Rate limit exceeded. Waiting {REQUEST_RETRY_DELAY}s...")
                    time.sleep(REQUEST_RETRY_DELAY)
                else:
                    self.logger.error(f"❌ HTTP Error {response.status_code}: {e}")
                    
            except requests.exceptions.ConnectionError:
                self.logger.error(f"❌ Connection error. Check your internet connection.")
                time.sleep(30)
                
            except requests.exceptions.Timeout:
                self.logger.error(f"❌ Request timeout. Retrying...")
                time.sleep(10)
                
            except Exception as e:
                self.logger.error(f"❌ Unexpected error: {e}")
                
        # All retries failed
        self.logger.error(f"❌ Failed to fetch odds for {sport} after {max_retries} attempts")
        return None
    
    def get_all_sports_odds(self) -> Dict[str, List[Dict]]:
        """
        Fetch odds for all configured sports
        
        Returns:
            Dictionary mapping sport name to list of events
        """
        all_odds = {}
        for sport in SPORTS:
            odds = self.get_sports_odds(sport)
            if odds:
                all_odds[sport] = odds
            # Small delay between requests to be respectful
            time.sleep(1)
        return all_odds
    
    def parse_bookmaker_odds(self, event: Dict) -> List[Dict]:
        """
        Extract bookmaker odds from an event
        
        Args:
            event: Event dictionary from API response
            
        Returns:
            List of {bookmaker, outcome, odds} dictionaries
        """
        extracted_odds = []
        
        for bookmaker in event.get('bookmakers', []):
            bookmaker_name = bookmaker.get('key', 'unknown')
            
            for market in bookmaker.get('markets', []):
                if market.get('key') != 'h2h':
                    continue
                    
                for outcome in market.get('outcomes', []):
                    extracted_odds.append({
                        'bookmaker': bookmaker_name,
                        'outcome': outcome.get('name'),
                        'odds': outcome.get('price'),
                        'last_update': bookmaker.get('last_update')
                    })
        
        return extracted_odds
    
    def is_odds_stale(self, timestamp: str, max_age_minutes: int = 5) -> bool:
        """
        Check if odds data is too old to be reliable
        
        Args:
            timestamp: ISO format timestamp from API
            max_age_minutes: Maximum acceptable age in minutes
            
        Returns:
            True if stale, False if fresh
        """
        try:
            odds_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            age_seconds = (datetime.now(odds_time.tzinfo) - odds_time).total_seconds()
            return age_seconds > (max_age_minutes * 60)
        except:
            return True  # Assume stale if can't parse
