# Forcible News Aggregator

A personalized New Zealand news aggregator with intelligent content curation.

## Overview

Forcible is a command-line tool that collects news from New Zealand sources, stores them in a local SQLite database, and provides intelligent analysis using LLMs to extract key facts, detect PR content, and personalize the news feed.

## Installation

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Initialize the configuration:

```bash
python forcible.py init
```

This creates a `config.ini` file from the example template.

3. Edit `config.ini` and add your OpenAI API key:

```ini
[openai]
api_key = your-actual-api-key-here
```

## Usage

### Fetch News Articles

Fetch articles from all configured sources:

```bash
python forcible.py fetch
```

Fetch only from Radio New Zealand:

```bash
python forcible.py fetch --source rnz
```

### List Articles

List recent articles:

```bash
python forcible.py list
```

List articles from a specific source:

```bash
python forcible.py list --source rnz_national
```

Limit the number of articles shown:

```bash
python forcible.py list --limit 10
```

### View Statistics

Show database statistics:

```bash
python forcible.py stats
```

## Architecture

### Components

- **config.py**: Configuration management (API keys, prompts, source URLs)
- **database.py**: SQLite database interface for storing articles
- **rnz_ingester.py**: Radio New Zealand RSS feed ingester
- **forcible.py**: Command-line interface

### Database Schema

**articles** table:
- `id`: Primary key
- `url`: Unique article URL
- `source`: Source identifier (e.g., 'rnz_national')
- `headline`: Article headline
- `published_date`: Publication date (ISO format)
- `fetched_date`: Date fetched from source
- `content`: Article content/summary
- `data`: JSON field for LLM analysis results (facts, relevance, PR probability, etc.)
- `created_at`: Record creation timestamp
- `updated_at`: Last update timestamp

**source_tracking** table:
- `source_name`: Source identifier (primary key)
- `last_scraped`: Last scrape timestamp
- `last_article_date`: Most recent article date seen

### Configuration

The `config.ini` file supports:

- **OpenAI API key**: For LLM processing
- **Prompts**: Configurable prompts for different analysis tasks
- **Sources**: RSS/Atom feed URLs for different news sources
- **Database**: Database file path

## News Sources

Currently supported:

### Radio New Zealand (RNZ)
- National news
- World news
- Business news
- Political news

All via RSS feeds.

## Future Enhancements

- LLM processing pipeline for extracting facts, relevance scoring, and PR detection
- Additional sources (Stuff, NZ Herald)
- Web scraping for sources without RSS feeds
- archive.is integration for paywall bypass
- User preference management
- Web interface for viewing personalized feed
