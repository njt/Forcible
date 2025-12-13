"""
Radio New Zealand RSS feed ingester.
"""
import feedparser
import requests
from datetime import datetime
from typing import Optional, Dict, Any, List
from dateutil import parser as date_parser
import time


class RNZIngester:
    """Handles ingestion of Radio New Zealand RSS feeds."""
    
    def __init__(self, database, config):
        """
        Initialize the ingester.
        
        Args:
            database: Database instance
            config: Config instance
        """
        self.db = database
        self.config = config
    
    def fetch_feed(self, url: str, source_name: str) -> int:
        """
        Fetch and parse an RSS feed.
        
        Args:
            url: RSS feed URL
            source_name: Name of the source for tracking
            
        Returns:
            Number of new articles added
        """
        print(f"Fetching feed: {source_name} from {url}")
        
        try:
            # Parse the feed
            feed = feedparser.parse(url)
            
            if feed.bozo and hasattr(feed, 'bozo_exception'):
                print(f"Warning: Feed parsing issue: {feed.bozo_exception}")
            
            if not feed.entries:
                print(f"No entries found in feed: {source_name}")
                return 0
            
            new_articles = 0
            latest_date = None
            
            # Process each entry
            for entry in feed.entries:
                # Extract article URL
                url = entry.get('link', '')
                if not url:
                    print(f"Skipping entry without URL: {entry.get('title', 'Unknown')}")
                    continue
                
                # Skip if already in database
                if self.db.article_exists(url):
                    continue
                
                # Extract headline
                headline = entry.get('title', 'Untitled')
                
                # Extract publication date
                published_date = None
                if 'published_parsed' in entry and entry.published_parsed:
                    try:
                        dt = datetime(*entry.published_parsed[:6])
                        published_date = dt.isoformat()
                        
                        # Track latest date
                        if latest_date is None or dt > datetime.fromisoformat(latest_date):
                            latest_date = published_date
                    except Exception as e:
                        print(f"Error parsing date: {e}")
                elif 'published' in entry:
                    try:
                        dt = date_parser.parse(entry.published)
                        published_date = dt.isoformat()
                        
                        if latest_date is None or dt > datetime.fromisoformat(latest_date):
                            latest_date = published_date
                    except Exception as e:
                        print(f"Error parsing date string: {e}")
                
                # Extract content
                content = None
                if 'summary' in entry:
                    content = entry.summary
                elif 'description' in entry:
                    content = entry.description
                elif 'content' in entry and entry.content:
                    content = entry.content[0].get('value', '')
                
                # Store initial data
                initial_data = {
                    'raw_entry': {
                        'title': headline,
                        'link': url,
                        'published': published_date
                    }
                }
                
                # Insert into database
                try:
                    article_id = self.db.insert_article(
                        url=url,
                        source=source_name,
                        headline=headline,
                        published_date=published_date,
                        content=content,
                        data=initial_data
                    )
                    new_articles += 1
                    print(f"Added: {headline[:60]}...")
                except Exception as e:
                    print(f"Error inserting article: {e}")
            
            # Update scrape time
            self.db.update_scrape_time(source_name, latest_date)
            
            print(f"Completed {source_name}: {new_articles} new articles")
            return new_articles
            
        except Exception as e:
            print(f"Error fetching feed {source_name}: {e}")
            return 0
    
    def fetch_all_rnz_feeds(self) -> Dict[str, int]:
        """
        Fetch all configured RNZ feeds.
        
        Returns:
            Dictionary mapping source name to number of new articles
        """
        sources = self.config.get_source_urls()
        results = {}
        
        for source_name, url in sources.items():
            if source_name.startswith('rnz_'):
                count = self.fetch_feed(url, source_name)
                results[source_name] = count
                # Be polite to the server
                time.sleep(1)
        
        return results
    
    def fetch_full_article_content(self, url: str) -> Optional[str]:
        """
        Attempt to fetch full article content from URL.
        
        Args:
            url: Article URL
            
        Returns:
            Article content or None if fetch fails
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; NewsAggregator/1.0)'
            }
            response = requests.get(url, headers=headers, timeout=10, verify=True)
            response.raise_for_status()
            
            # Basic extraction - in production, would use BeautifulSoup
            # or other HTML parsing for better extraction
            return response.text
            
        except Exception as e:
            print(f"Error fetching full article from {url}: {e}")
            return None
