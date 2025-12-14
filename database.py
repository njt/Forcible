"""
Database management for the news aggregator.
"""
import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, List, Any


class Database:
    """Manages SQLite database for storing articles."""
    
    def __init__(self, db_path='news.db'):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()
    
    def _init_schema(self):
        """Initialize database schema."""
        cursor = self.conn.cursor()
        
        # Articles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                source TEXT NOT NULL,
                headline TEXT NOT NULL,
                published_date TEXT,
                fetched_date TEXT NOT NULL,
                content TEXT,
                data TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Source tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS source_tracking (
                source_name TEXT PRIMARY KEY,
                last_scraped TEXT NOT NULL,
                last_article_date TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_articles_source 
            ON articles(source)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_articles_published_date 
            ON articles(published_date)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_articles_url 
            ON articles(url)
        ''')
        
        self.conn.commit()
    
    def article_exists(self, url: str) -> bool:
        """
        Check if article already exists in database.
        
        Args:
            url: Article URL
            
        Returns:
            True if article exists, False otherwise
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT 1 FROM articles WHERE url = ?', (url,))
        return cursor.fetchone() is not None
    
    def insert_article(
        self,
        url: str,
        source: str,
        headline: str,
        published_date: Optional[str] = None,
        content: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Insert a new article into the database.
        
        Args:
            url: Article URL
            source: Source name (e.g., 'rnz_national')
            headline: Article headline
            published_date: Publication date (ISO format)
            content: Full article content
            data: Additional data as JSON (facts, relevance, etc.)
            
        Returns:
            Article ID
        """
        cursor = self.conn.cursor()
        fetched_date = datetime.utcnow().isoformat()
        
        data_json = json.dumps(data) if data else None
        
        cursor.execute('''
            INSERT INTO articles 
            (url, source, headline, published_date, fetched_date, content, data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (url, source, headline, published_date, fetched_date, content, data_json))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def update_article_data(self, article_id: int, data: Dict[str, Any]):
        """
        Update article data (for LLM processing results).
        
        Args:
            article_id: Article ID
            data: Data to update
        """
        cursor = self.conn.cursor()
        data_json = json.dumps(data)
        updated_at = datetime.utcnow().isoformat()
        
        cursor.execute('''
            UPDATE articles 
            SET data = ?, updated_at = ?
            WHERE id = ?
        ''', (data_json, updated_at, article_id))
        
        self.conn.commit()
    
    def get_last_scrape_time(self, source_name: str) -> Optional[str]:
        """
        Get the last scrape time for a source.
        
        Args:
            source_name: Source name
            
        Returns:
            ISO format datetime string or None
        """
        cursor = self.conn.cursor()
        cursor.execute(
            'SELECT last_scraped FROM source_tracking WHERE source_name = ?',
            (source_name,)
        )
        row = cursor.fetchone()
        return row['last_scraped'] if row else None
    
    def update_scrape_time(
        self,
        source_name: str,
        last_article_date: Optional[str] = None
    ):
        """
        Update the last scrape time for a source.
        
        Args:
            source_name: Source name
            last_article_date: Most recent article date seen
        """
        cursor = self.conn.cursor()
        last_scraped = datetime.utcnow().isoformat()
        
        cursor.execute('''
            INSERT OR REPLACE INTO source_tracking 
            (source_name, last_scraped, last_article_date)
            VALUES (?, ?, ?)
        ''', (source_name, last_scraped, last_article_date))
        
        self.conn.commit()
    
    def get_articles(
        self,
        source: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get articles from database.
        
        Args:
            source: Filter by source (optional)
            limit: Maximum number of articles to return
            
        Returns:
            List of article dictionaries
        """
        cursor = self.conn.cursor()
        
        if source:
            cursor.execute('''
                SELECT * FROM articles 
                WHERE source = ?
                ORDER BY published_date DESC 
                LIMIT ?
            ''', (source, limit))
        else:
            cursor.execute('''
                SELECT * FROM articles 
                ORDER BY published_date DESC 
                LIMIT ?
            ''', (limit,))
        
        articles = []
        for row in cursor.fetchall():
            article = dict(row)
            if article['data']:
                article['data'] = json.loads(article['data'])
            articles.append(article)
        
        return articles
    
    def get_unprocessed_articles(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get articles that haven't been processed by LLM yet.
        
        Args:
            limit: Maximum number of articles to return (optional)
            
        Returns:
            List of article dictionaries
            
        Note:
            Uses LIKE pattern matching on JSON data field. For better performance
            on large datasets, consider using JSON functions like json_extract()
            or adding a separate 'processed' boolean column.
        """
        cursor = self.conn.cursor()
        
        # Articles are unprocessed if data is NULL or doesn't contain 'key_facts'
        query = '''
            SELECT * FROM articles 
            WHERE data IS NULL 
               OR (data NOT LIKE '%key_facts%' AND data NOT LIKE '%error%')
            ORDER BY published_date DESC
        '''
        
        if limit:
            query += ' LIMIT ?'
            cursor.execute(query, (limit,))
        else:
            cursor.execute(query)
        
        articles = []
        for row in cursor.fetchall():
            article = dict(row)
            if article['data']:
                try:
                    article['data'] = json.loads(article['data'])
                except json.JSONDecodeError:
                    article['data'] = None
            articles.append(article)
        
        return articles
    
    def get_article_by_id(self, article_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single article by ID.
        
        Args:
            article_id: Article ID
            
        Returns:
            Article dictionary or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM articles WHERE id = ?', (article_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        article = dict(row)
        if article['data']:
            try:
                article['data'] = json.loads(article['data'])
            except json.JSONDecodeError:
                article['data'] = None
        
        return article
    
    def close(self):
        """Close database connection."""
        self.conn.close()
