#!/usr/bin/env python3
"""
Forcible News Aggregator - Command Line Interface

A personalized New Zealand news aggregator with intelligent content curation.
"""
import argparse
import sys
from pathlib import Path

from config import Config
from database import Database
from rnz_ingester import RNZIngester


def cmd_fetch(args):
    """Fetch articles from configured sources."""
    try:
        config = Config(args.config)
        db = Database(config.get_database_path())
        
        if args.source == 'rnz' or args.source == 'all':
            print("Fetching Radio New Zealand feeds...")
            ingester = RNZIngester(db, config)
            results = ingester.fetch_all_rnz_feeds()
            
            total = sum(results.values())
            print(f"\nTotal new articles: {total}")
            for source, count in results.items():
                print(f"  {source}: {count}")
        
        db.close()
        print("\nFetch complete!")
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during fetch: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_list(args):
    """List articles from the database."""
    try:
        config = Config(args.config)
        db = Database(config.get_database_path())
        
        articles = db.get_articles(source=args.source, limit=args.limit)
        
        if not articles:
            print("No articles found.")
            db.close()
            return
        
        print(f"\nFound {len(articles)} articles:\n")
        
        for article in articles:
            print(f"[{article['source']}] {article['headline']}")
            print(f"  URL: {article['url']}")
            if article['published_date']:
                print(f"  Published: {article['published_date']}")
            print()
        
        db.close()
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error listing articles: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_init(args):
    """Initialize configuration and database."""
    try:
        # Check if config.ini exists
        config_path = Path(args.config)
        if config_path.exists() and not args.force:
            print(f"Configuration file already exists: {args.config}")
            print("Use --force to overwrite.")
            sys.exit(1)
        
        # Copy example config
        example_path = Path('config.example.ini')
        if not example_path.exists():
            print("Error: config.example.ini not found", file=sys.stderr)
            sys.exit(1)
        
        config_path.write_text(example_path.read_text())
        print(f"Created configuration file: {args.config}")
        print("\nPlease edit config.ini and add your OpenAI API key.")
        
        # Initialize database
        config = Config(args.config)
        db = Database(config.get_database_path())
        print(f"Initialized database: {config.get_database_path()}")
        db.close()
        
    except Exception as e:
        print(f"Error during initialization: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_stats(args):
    """Show statistics about the database."""
    try:
        config = Config(args.config)
        db = Database(config.get_database_path())
        
        cursor = db.conn.cursor()
        
        # Total articles
        cursor.execute('SELECT COUNT(*) as count FROM articles')
        total = cursor.fetchone()['count']
        print(f"Total articles: {total}")
        
        # Articles by source
        cursor.execute('''
            SELECT source, COUNT(*) as count 
            FROM articles 
            GROUP BY source 
            ORDER BY count DESC
        ''')
        print("\nArticles by source:")
        for row in cursor.fetchall():
            print(f"  {row['source']}: {row['count']}")
        
        # Last scrape times
        cursor.execute('SELECT * FROM source_tracking ORDER BY last_scraped DESC')
        print("\nLast scrape times:")
        for row in cursor.fetchall():
            print(f"  {row['source_name']}: {row['last_scraped']}")
        
        db.close()
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error getting statistics: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Forcible News Aggregator - Personalized NZ news with intelligent curation'
    )
    parser.add_argument(
        '--config',
        default='config.ini',
        help='Path to configuration file (default: config.ini)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # init command
    parser_init = subparsers.add_parser('init', help='Initialize configuration and database')
    parser_init.add_argument('--force', action='store_true', help='Overwrite existing config')
    parser_init.set_defaults(func=cmd_init)
    
    # fetch command
    parser_fetch = subparsers.add_parser('fetch', help='Fetch articles from sources')
    parser_fetch.add_argument(
        '--source',
        default='all',
        choices=['all', 'rnz'],
        help='Source to fetch from (default: all)'
    )
    parser_fetch.set_defaults(func=cmd_fetch)
    
    # list command
    parser_list = subparsers.add_parser('list', help='List articles')
    parser_list.add_argument('--source', help='Filter by source')
    parser_list.add_argument('--limit', type=int, default=20, help='Maximum articles to show')
    parser_list.set_defaults(func=cmd_list)
    
    # stats command
    parser_stats = subparsers.add_parser('stats', help='Show database statistics')
    parser_stats.set_defaults(func=cmd_stats)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == '__main__':
    main()
