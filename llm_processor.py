"""
LLM post-processing for news articles using structured outputs.
"""
from openai import OpenAI
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class KeyFact(BaseModel):
    """A key fact or statistic from an article."""
    fact: str = Field(description="The fact or statistic extracted from the article")
    importance: int = Field(description="Importance score from 1-10", ge=1, le=10)


class ArticleAnalysis(BaseModel):
    """Structured analysis of a news article."""
    key_facts: List[KeyFact] = Field(
        description="List of key facts and statistics from the article"
    )
    relevance_score: int = Field(
        description="Relevance score for New Zealand news interests (0-10)",
        ge=0,
        le=10
    )
    pr_probability: int = Field(
        description="Probability (0-100) that this was planted by PR/communications",
        ge=0,
        le=100
    )
    content_classification: str = Field(
        description="Either 'headline-only' or 'clickthrough'",
        pattern="^(headline-only|clickthrough)$"
    )
    summary: str = Field(
        description="Brief one-sentence summary of the article"
    )
    reasoning: str = Field(
        description="Brief explanation of the PR probability assessment"
    )


class LLMProcessor:
    """Handles LLM processing of news articles."""
    
    def __init__(self, api_key: str):
        """
        Initialize the LLM processor.
        
        Args:
            api_key: OpenAI API key
        """
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"  # Using gpt-4o-mini for structured outputs
    
    def analyze_article(
        self,
        headline: str,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze an article using LLM with structured output.
        
        Args:
            headline: Article headline
            content: Article content (summary or full text)
            
        Returns:
            Dictionary containing structured analysis results
        """
        # Construct the prompt
        article_text = f"Headline: {headline}\n\n"
        if content:
            article_text += f"Content: {content}"
        else:
            article_text += "Content: [No content available - analyze headline only]"
        
        prompt = f"""Analyze this New Zealand news article and provide structured analysis.

{article_text}

Please provide:
1. Key facts and statistics with importance scores (1-10)
2. Relevance score (0-10) for general New Zealand news interests
3. PR probability (0-100) - likelihood this was planted by PR/communications teams. Consider:
   - Generic corporate announcements
   - Overly promotional language
   - Lack of critical perspective
   - Focus on company/organization success without context
4. Content classification:
   - "headline-only" if the headline alone conveys the key information
   - "clickthrough" if the full article is needed for understanding
5. A brief one-sentence summary
6. Brief reasoning for PR probability assessment"""

        try:
            # Use structured output with response_format
            # Note: Using beta API for structured outputs which provides strong guarantees
            # that the output matches the Pydantic schema
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert news analyst specializing in New Zealand media. You provide objective, structured analysis of news articles."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format=ArticleAnalysis
            )
            
            # Extract the structured response
            analysis = completion.choices[0].message.parsed
            
            # Convert to dictionary
            result = {
                "key_facts": [
                    {
                        "fact": fact.fact,
                        "importance": fact.importance
                    }
                    for fact in analysis.key_facts
                ],
                "relevance_score": analysis.relevance_score,
                "pr_probability": analysis.pr_probability,
                "content_classification": analysis.content_classification,
                "summary": analysis.summary,
                "reasoning": analysis.reasoning,
                "processed_at": None  # Will be set by caller
            }
            
            return result
            
        except Exception as e:
            # Catch OpenAI API errors and other exceptions
            # For production use, consider catching specific exceptions:
            # - openai.APIError, openai.RateLimitError, etc.
            print(f"Error during LLM analysis: {e}")
            # Return a default structure on error
            return {
                "key_facts": [],
                "relevance_score": 5,
                "pr_probability": 0,
                "content_classification": "clickthrough",
                "summary": headline,
                "reasoning": f"Analysis failed: {str(e)}",
                "error": str(e),
                "processed_at": None
            }
    
    def batch_analyze_articles(
        self,
        articles: List[Dict[str, Any]],
        progress_callback: Optional[callable] = None
    ) -> Dict[int, Dict[str, Any]]:
        """
        Analyze multiple articles in batch.
        
        Args:
            articles: List of article dictionaries (must have 'id', 'headline', 'content')
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary mapping article IDs to analysis results
        """
        results = {}
        total = len(articles)
        
        for i, article in enumerate(articles):
            article_id = article['id']
            headline = article['headline']
            content = article.get('content')
            
            if progress_callback:
                progress_callback(i + 1, total, headline)
            
            analysis = self.analyze_article(headline, content)
            results[article_id] = analysis
        
        return results
