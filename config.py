"""
Configuration management for the news aggregator.
"""
import configparser
import os
from pathlib import Path


class Config:
    """Manages configuration from INI file."""
    
    def __init__(self, config_path='config.ini'):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}. "
                f"Please copy config.example.ini to config.ini and configure it."
            )
        
        self.config.read(config_path)
    
    def get_openai_key(self):
        """Get OpenAI API key."""
        return self.config.get('openai', 'api_key')
    
    def get_prompt(self, prompt_name):
        """Get a specific prompt by name."""
        return self.config.get('prompts', prompt_name)
    
    def get_database_path(self):
        """Get database file path."""
        return self.config.get('database', 'path', fallback='news.db')
    
    def get_source_urls(self):
        """Get all configured source URLs."""
        if not self.config.has_section('sources'):
            return {}
        return dict(self.config.items('sources'))
