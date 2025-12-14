# Forcible News Aggregator

A personalized New Zealand news aggregator with intelligent content curation.

## Overview

Forcible is a command-line tool that collects news from New Zealand sources, stores them in a local SQLite database, and provides intelligent analysis using LLMs to extract key facts, detect PR content, and personalize the news feed.

## Features

- **Multi-source aggregation**: Fetches news from Radio New Zealand RSS feeds
- **LLM-powered analysis**: Uses OpenAI's structured outputs to analyze articles
  - Extracts key facts and statistics with importance scoring
  - Scores article relevance for NZ news interests
  - Detects potential PR-planted stories
  - Classifies content as "headline-only" or "clickthrough"
  - Generates concise summaries
- **Flexible configuration**: Supports both INI and JSON config formats
- **SQLite storage**: Local database for all articles and analysis
- **CLI interface**: Easy-to-use command-line tools

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

Alternatively, you can use JSON configuration:

```bash
python forcible.py --config config.json init
```

3. Edit `config.ini` (or `config.json`) and add your OpenAI API key:

**For INI format:**
```ini
[openai]
api_key = your-actual-api-key-here
```

**For JSON format:**
```json
{
  "openai": {
    "api_key": "your-actual-api-key-here"
  }
}
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

### Fetch Full Article HTML

Fetch full HTML content for articles that don't have it yet:

```bash
python forcible.py fetch-html
```

Fetch HTML for a limited number of articles:

```bash
python forcible.py fetch-html --limit 10
```

This command fetches article content from URLs and extracts only the essential text (paragraphs, headings, links) to minimize token usage for LLM processing. Navigation, ads, and other non-content elements are removed.

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

### Process Articles with LLM

Process unprocessed articles with LLM analysis:

```bash
python forcible.py process
```

Process a limited number of articles:

```bash
python forcible.py process --limit 10
```

Process a specific article by ID:

```bash
python forcible.py process --article-id 42
```

Show detailed analysis results:

```bash
python forcible.py process --verbose
```

### View Article Analysis

View a specific article with its LLM analysis:

```bash
python forcible.py view 42
```

This displays the article headline, content, and structured LLM analysis including:
- Key facts and statistics
- Relevance score
- PR probability assessment
- Content classification
- Summary

## Architecture

### Components

- **config.py**: Configuration management (supports both INI and JSON formats)
- **database.py**: SQLite database interface for storing articles
- **rnz_ingester.py**: Radio New Zealand RSS feed ingester
- **html_fetcher.py**: HTML content fetcher for retrieving full article content
- **llm_processor.py**: LLM-based article analysis with structured outputs
- **forcible.py**: Command-line interface

### Database Schema

**articles** table:
- `id`: Primary key
- `url`: Unique article URL
- `source`: Source identifier (e.g., 'rnz_national')
- `headline`: Article headline
- `published_date`: Publication date (ISO format)
- `fetched_date`: Date fetched from source
- `content`: Article content/summary from RSS feed
- `raw_html`: Extracted article content (text, headings, links) from article URL
- `data`: JSON field for LLM analysis results (facts, relevance, PR probability, etc.)
- `created_at`: Record creation timestamp
- `updated_at`: Last update timestamp

The `data` field contains structured LLM analysis:
```json
{
  "key_facts": [
    {"fact": "...", "importance": 8}
  ],
  "relevance_score": 7,
  "pr_probability": 25,
  "content_classification": "headline-only",
  "summary": "...",
  "reasoning": "...",
  "processed_at": "2024-01-01T12:00:00"
}
```

**source_tracking** table:
- `source_name`: Source identifier (primary key)
- `last_scraped`: Last scrape timestamp
- `last_article_date`: Most recent article date seen

### Configuration

The configuration file (INI or JSON format) supports:

- **OpenAI API key**: For LLM processing
- **LLM model**: Model to use (default: gpt-4o-mini)
- **Prompts**: Configurable prompts for different analysis tasks (legacy, not used with structured outputs)
- **Sources**: RSS/Atom feed URLs for different news sources
- **Database**: Database file path

You can use either `config.ini` (INI format) or `config.json` (JSON format). The JSON format provides better structure for complex configurations.

## News Sources

Currently supported:

### Radio New Zealand (RNZ)
- National news
- World news
- Business news
- Political news

All via RSS feeds.

## Future Enhancements

- Additional sources (Stuff, NZ Herald)
- Web scraping for sources without RSS feeds
- archive.is integration for paywall bypass
- User preference management
- Web interface for viewing personalized feed
- Batch processing optimizations
- Caching and rate limiting for LLM API calls
