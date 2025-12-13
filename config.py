"""
Configuration management for the news aggregator.
"""
import configparser
import json
import os
from pathlib import Path


class Config:
    """Manages configuration from INI or JSON file."""
    
    def __init__(self, config_path='config.ini'):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to configuration file (INI or JSON)
        """
        self.config_path = config_path
        self.config = None
        self.config_data = None
        self.is_json = config_path.endswith('.json')
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"Configuration file not found: {config_path}. "
                f"Please copy config.example.ini to config.ini or config.example.json to config.json and configure it."
            )
        
        if self.is_json:
            with open(config_path, 'r') as f:
                self.config_data = json.load(f)
        else:
            self.config = configparser.ConfigParser()
            self.config.read(config_path)
    
    def get_openai_key(self):
        """Get OpenAI API key."""
        if self.is_json:
            return self.config_data.get('openai', {}).get('api_key')
        return self.config.get('openai', 'api_key')
    
    def get_prompt(self, prompt_name):
        """Get a specific prompt by name."""
        if self.is_json:
            return self.config_data.get('prompts', {}).get(prompt_name)
        return self.config.get('prompts', prompt_name)
    
    def get_database_path(self):
        """Get database file path."""
        if self.is_json:
            return self.config_data.get('database', {}).get('path', 'news.db')
        return self.config.get('database', 'path', fallback='news.db')
    
    def get_source_urls(self):
        """Get all configured source URLs."""
        if self.is_json:
            return self.config_data.get('sources', {})
        if not self.config.has_section('sources'):
            return {}
        return dict(self.config.items('sources'))
    
    def get_llm_model(self):
        """Get LLM model name."""
        if self.is_json:
            return self.config_data.get('llm', {}).get('model', 'gpt-4o-mini')
        if self.config.has_section('llm') and self.config.has_option('llm', 'model'):
            return self.config.get('llm', 'model')
        return 'gpt-4o-mini'
