# New Zealand News Aggregator

This project is building a personalized New Zealand news aggregator with intelligent content curation.

## Architecture Overview

### Data Collection

**Local Database**
- Central database storing all collected news content
- Stores original articles, metadata, and processed insights

**News Sources**
- **Radio New Zealand**: RSS/Atom feeds
- **Stuff**: RSS/Atom feeds  
- **New Zealand Herald**: Web scraping (if RSS/Atom feeds unavailable)

**Content Fetching**
- Fetch full article content from each source
- For paywalled content: check archive.is for archived versions

### LLM Processing

Each story will be analyzed using an LLM to extract:

1. **Key Facts and Statistics**: Identify and extract important data points, numbers, and factual claims
2. **Relevance Scoring**: Determine if the story matches user interests
3. **PR Detection**: Assign probability that the story was planted by PR/communications teams
4. **Content Classification**: Decide presentation format:
   - **Headline-only**: Simple facts ("Tom Stoppard died", "Minister XYZ resigned", "Hospital wait lists 2 months longer than last year on average")
   - **Clickthrough**: Stories requiring full article access for proper understanding

### Output

A personalized newsfeed that:
- Shows only relevant content based on user interests
- Highlights key facts and statistics
- Indicates potential PR-planted stories
- Optimizes reading time by showing headline-only vs full articles

## Implementation Plan

1. Set up local database schema
2. Build feed collectors for Radio New Zealand and Stuff
3. Build web scraper for NZ Herald
4. Implement archive.is integration for paywall bypass
5. Design and implement LLM prompt chain for content analysis
6. Build personalized feed generator
7. Create user interface for consuming the newsfeed
