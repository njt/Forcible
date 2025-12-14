"""
HTML content fetcher for news articles.
"""
import requests
from typing import Optional
from bs4 import BeautifulSoup


class HTMLFetcher:
    """Handles fetching and storing raw HTML content from article URLs."""
    
    def __init__(self, database):
        """
        Initialize the HTML fetcher.
        
        Args:
            database: Database instance
        """
        self.db = database
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def fetch_html(self, url: str) -> Optional[str]:
        """
        Fetch raw HTML content from a URL.
        
        Args:
            url: Article URL
            
        Returns:
            Raw HTML content or None if fetch fails
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=30, allow_redirects=True)
            response.raise_for_status()
            
            # Parse HTML to remove script and style tags
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style']):
                script.decompose()
            
            # Return the cleaned HTML as string
            return str(soup)
            
        except requests.RequestException as e:
            print(f"Error fetching HTML from {url}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching HTML from {url}: {e}")
            return None
    
    def fetch_article_html(self, article_id: int, url: str) -> bool:
        """
        Fetch HTML for a specific article and store it in the database.
        
        Args:
            article_id: Article ID
            url: Article URL
            
        Returns:
            True if successful, False otherwise
        """
        html = self.fetch_html(url)
        if html:
            self.db.update_article_html(article_id, html)
            return True
        return False
    
    def fetch_all_missing_html(self, limit: Optional[int] = None, progress_callback: Optional[callable] = None) -> int:
        """
        Fetch HTML for all articles that don't have it yet.
        
        Args:
            limit: Maximum number of articles to process (optional)
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Number of articles successfully fetched
        """
        articles = self.db.get_articles_without_html(limit=limit)
        
        if not articles:
            return 0
        
        success_count = 0
        total = len(articles)
        
        for i, article in enumerate(articles):
            article_id = article['id']
            url = article['url']
            headline = article['headline']
            
            if progress_callback:
                progress_callback(i + 1, total, headline)
            
            if self.fetch_article_html(article_id, url):
                success_count += 1
        
        return success_count
