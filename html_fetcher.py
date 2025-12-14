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
        Fetch and extract article content from a URL.
        
        Extracts only the main article content (paragraphs, headings, links)
        to minimize token usage for LLM processing.
        
        Args:
            url: Article URL
            
        Returns:
            Extracted article content or None if fetch fails
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=30, allow_redirects=True)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 
                                'aside', 'iframe', 'noscript', 'form']):
                element.decompose()
            
            # Try to find the main article content
            # Common article containers
            article_content = None
            for selector in ['article', 'main', '[role="main"]', '.article-content', 
                           '.post-content', '.entry-content', '#content']:
                article_content = soup.select_one(selector)
                if article_content:
                    break
            
            # If no article container found, use body
            if not article_content:
                article_content = soup.body if soup.body else soup
            
            # Extract text content with structure
            extracted = []
            
            # Extract title if available
            title = soup.find('h1')
            if title:
                extracted.append(f"# {title.get_text(strip=True)}\n")
            
            # Extract paragraphs, headings, and lists from the article content
            for element in article_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'blockquote']):
                text = element.get_text(strip=True)
                if text:  # Only include non-empty elements
                    tag = element.name
                    
                    if tag == 'p':
                        extracted.append(text)
                    elif tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        level = int(tag[1])
                        extracted.append(f"\n{'#' * level} {text}\n")
                    elif tag in ['ul', 'ol']:
                        # Extract list items
                        for li in element.find_all('li', recursive=False):
                            li_text = li.get_text(strip=True)
                            if li_text:
                                extracted.append(f"- {li_text}")
                    elif tag == 'blockquote':
                        extracted.append(f"> {text}")
                    
                    extracted.append("")  # Add blank line between elements
            
            # Extract external links
            links = []
            for a in article_content.find_all('a', href=True):
                href = a['href']
                link_text = a.get_text(strip=True)
                # Only include external links (http/https)
                if href.startswith('http') and link_text:
                    links.append(f"[{link_text}]({href})")
            
            # Combine content
            content = "\n".join(extracted).strip()
            
            # Add links section if there are external links
            if links:
                content += "\n\n## External Links\n" + "\n".join(links)
            
            return content if content else None
            
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
