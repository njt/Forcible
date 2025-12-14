#!/usr/bin/env python3
"""
Forcible News Aggregator - Command Line Interface

A personalized New Zealand news aggregator with intelligent content curation.
"""
import argparse
import sys
import json
import traceback
from pathlib import Path
from datetime import datetime, UTC

from config import Config
from database import Database
from rnz_ingester import RNZIngester
from llm_processor import LLMProcessor
from html_fetcher import HTMLFetcher


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


def cmd_fetch_html(args):
    """Fetch full HTML content for articles."""
    try:
        config = Config(args.config)
        db = Database(config.get_database_path())
        
        fetcher = HTMLFetcher(db)
        
        # Get articles without HTML
        articles_to_fetch = db.get_articles_without_html(limit=args.limit)
        
        if not articles_to_fetch:
            print("No articles need HTML fetching.")
            db.close()
            return
        
        print(f"Fetching HTML for {len(articles_to_fetch)} article(s)...\n")
        
        # Progress callback
        def progress_callback(current, total, headline):
            print(f"[{current}/{total}] Fetching: {headline[:60]}...")
        
        # Fetch HTML
        success_count = fetcher.fetch_all_missing_html(
            limit=args.limit,
            progress_callback=progress_callback
        )
        
        db.close()
        print(f"\nFetch complete! Successfully fetched {success_count} article(s).")
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during HTML fetch: {e}", file=sys.stderr)
        traceback.print_exc()
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
        # Check if config file exists
        config_path = Path(args.config)
        if config_path.exists() and not args.force:
            print(f"Configuration file already exists: {args.config}")
            print("Use --force to overwrite.")
            sys.exit(1)
        
        # Determine format and copy example config
        script_dir = Path(__file__).parent
        is_json = args.config.endswith('.json')
        
        if is_json:
            example_path = script_dir / 'config.example.json'
            if not example_path.exists():
                print("Error: config.example.json not found", file=sys.stderr)
                sys.exit(1)
        else:
            example_path = script_dir / 'config.example.ini'
            if not example_path.exists():
                print("Error: config.example.ini not found", file=sys.stderr)
                sys.exit(1)
        
        config_path.write_text(example_path.read_text())
        print(f"Created configuration file: {args.config}")
        print(f"\nPlease edit {args.config} and add your OpenAI API key.")
        
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
        
        # Processed vs unprocessed
        cursor.execute('''
            SELECT 
                COUNT(CASE WHEN data LIKE '%key_facts%' THEN 1 END) as processed,
                COUNT(CASE WHEN data IS NULL OR (data NOT LIKE '%key_facts%' AND data NOT LIKE '%error%') THEN 1 END) as unprocessed
            FROM articles
        ''')
        row = cursor.fetchone()
        print(f"\nProcessed articles: {row['processed']}")
        print(f"Unprocessed articles: {row['unprocessed']}")
        
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


def cmd_process(args):
    """Process articles with LLM analysis."""
    try:
        config = Config(args.config)
        db = Database(config.get_database_path())
        
        # Get OpenAI API key
        api_key = config.get_openai_key()
        if not api_key or api_key == 'your-openai-api-key-here':
            print("Error: Please configure your OpenAI API key in the config file.", file=sys.stderr)
            sys.exit(1)
        
        # Initialize LLM processor
        processor = LLMProcessor(api_key)
        
        # Get articles to process
        if args.article_id:
            # Process specific article
            article = db.get_article_by_id(args.article_id)
            if not article:
                print(f"Error: Article {args.article_id} not found", file=sys.stderr)
                sys.exit(1)
            articles = [article]
        else:
            # Get unprocessed articles
            articles = db.get_unprocessed_articles(limit=args.limit)
        
        if not articles:
            print("No articles to process.")
            db.close()
            return
        
        print(f"Processing {len(articles)} article(s)...\n")
        
        # Process articles
        def progress_callback(current, total, headline):
            print(f"[{current}/{total}] Processing: {headline[:60]}...")
        
        results = processor.batch_analyze_articles(articles, progress_callback)
        
        # Save results to database
        print("\nSaving results...")
        for article_id, analysis in results.items():
            # Add timestamp
            analysis['processed_at'] = datetime.now(UTC).isoformat()
            
            # Get existing data and merge
            article = db.get_article_by_id(article_id)
            existing_data = article.get('data') or {}
            if isinstance(existing_data, str):
                existing_data = json.loads(existing_data)
            
            # Merge LLM analysis with existing data
            existing_data.update(analysis)
            
            # Update database
            db.update_article_data(article_id, existing_data)
            
            # Show results if verbose
            if args.verbose:
                print(f"\nArticle {article_id}: {article['headline']}")
                print(f"  Relevance: {analysis['relevance_score']}/10")
                print(f"  PR Probability: {analysis['pr_probability']}%")
                print(f"  Classification: {analysis['content_classification']}")
                print(f"  Summary: {analysis['summary']}")
                if analysis['key_facts']:
                    print(f"  Key Facts:")
                    for fact in analysis['key_facts']:
                        print(f"    - {fact['fact']} (importance: {fact['importance']}/10)")
        
        db.close()
        print(f"\nProcessing complete! {len(results)} article(s) analyzed.")
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during processing: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)


def cmd_view(args):
    """View a specific article with its analysis."""
    try:
        config = Config(args.config)
        db = Database(config.get_database_path())
        
        article = db.get_article_by_id(args.article_id)
        if not article:
            print(f"Error: Article {args.article_id} not found", file=sys.stderr)
            sys.exit(1)
        
        # Display article info
        print(f"\n{'='*80}")
        print(f"Article ID: {article['id']}")
        print(f"Source: {article['source']}")
        print(f"Headline: {article['headline']}")
        print(f"URL: {article['url']}")
        if article['published_date']:
            print(f"Published: {article['published_date']}")
        print(f"{'='*80}\n")
        
        # Display content
        if article['content']:
            print("Content:")
            print(article['content'])
            print()
        
        # Display analysis if available
        data = article.get('data')
        if data and isinstance(data, dict):
            if 'key_facts' in data:
                print(f"\n{'='*80}")
                print("LLM ANALYSIS")
                print(f"{'='*80}\n")
                
                print(f"Summary: {data.get('summary', 'N/A')}")
                print(f"Relevance Score: {data.get('relevance_score', 'N/A')}/10")
                print(f"PR Probability: {data.get('pr_probability', 'N/A')}%")
                print(f"Classification: {data.get('content_classification', 'N/A')}")
                print(f"Processed At: {data.get('processed_at', 'N/A')}")
                
                if data.get('reasoning'):
                    print(f"\nPR Assessment Reasoning:")
                    print(f"  {data['reasoning']}")
                
                if data.get('key_facts'):
                    print(f"\nKey Facts:")
                    for fact in data['key_facts']:
                        print(f"  - {fact['fact']} (importance: {fact['importance']}/10)")
                
                if data.get('error'):
                    print(f"\nError during analysis: {data['error']}")
            else:
                print("\nNo LLM analysis available for this article.")
        else:
            print("\nNo analysis data available for this article.")
        
        print()
        db.close()
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error viewing article: {e}", file=sys.stderr)
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
    
    # fetch-html command
    parser_fetch_html = subparsers.add_parser('fetch-html', help='Fetch full HTML content for articles')
    parser_fetch_html.add_argument(
        '--limit',
        type=int,
        help='Maximum number of articles to fetch (default: all without HTML)'
    )
    parser_fetch_html.set_defaults(func=cmd_fetch_html)
    
    # list command
    parser_list = subparsers.add_parser('list', help='List articles')
    parser_list.add_argument('--source', help='Filter by source')
    parser_list.add_argument('--limit', type=int, default=20, help='Maximum articles to show')
    parser_list.set_defaults(func=cmd_list)
    
    # stats command
    parser_stats = subparsers.add_parser('stats', help='Show database statistics')
    parser_stats.set_defaults(func=cmd_stats)
    
    # process command
    parser_process = subparsers.add_parser('process', help='Process articles with LLM analysis')
    parser_process.add_argument(
        '--limit',
        type=int,
        help='Maximum number of articles to process (default: all unprocessed)'
    )
    parser_process.add_argument(
        '--article-id',
        type=int,
        help='Process a specific article by ID'
    )
    parser_process.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed analysis results'
    )
    parser_process.set_defaults(func=cmd_process)
    
    # view command
    parser_view = subparsers.add_parser('view', help='View article with analysis')
    parser_view.add_argument('article_id', type=int, help='Article ID to view')
    parser_view.set_defaults(func=cmd_view)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == '__main__':
    main()
