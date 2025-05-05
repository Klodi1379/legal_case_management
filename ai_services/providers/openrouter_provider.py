"""
OpenRouter provider implementation.
"""
import requests
import logging
from typing import Dict, Any, List
from .base import BaseAIProvider

logger = logging.getLogger(__name__)


class OpenRouterProvider(BaseAIProvider):
    """
    OpenRouter API provider implementation.
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        super().__init__(model_config)
        self.endpoint_url = self.endpoint_url or "https://openrouter.ai/api/v1/chat/completions"
        
        # Default model name if not specified
        if not self.model_name:
            self.model_name = "openai/gpt-3.5-turbo"
    
    def prepare_headers(self) -> Dict[str, str]:
        """
        Prepare headers for OpenRouter API requests.
        """
        headers = super().prepare_headers()
        
        # OpenRouter specific headers
        headers['HTTP-Referer'] = self.model_config.get('site_url', 'http://localhost:8000')
        headers['X-Title'] = self.model_config.get('app_name', 'Legal Case Management')
        
        return headers
    
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Send a chat completion request to OpenRouter.
        """
        headers = self.prepare_headers()
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": kwargs.get('max_tokens', self.max_tokens),
            "temperature": kwargs.get('temperature', self.temperature),
            "top_p": kwargs.get('top_p', self.top_p),
        }
        
        # Add provider-specific parameters if needed
        if 'provider' in kwargs:
            payload['provider'] = kwargs['provider']
        
        try:
            response = requests.post(
                self.endpoint_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API request failed: {str(e)}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        OpenRouter doesn't provide embeddings API, so we'll return a placeholder.
        """
        logger.warning("OpenRouter doesn't provide embeddings API")
        # Return a dummy embedding vector
        return [0.0] * 768
    
    def is_available(self) -> bool:
        """
        Check if OpenRouter API is available.
        """
        if not self.api_key:
            return False
        
        try:
            headers = self.prepare_headers()
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers=headers,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def get_supported_models(self) -> List[str]:
        """
        Get list of supported OpenRouter models.
        """
        # OpenRouter supports many models, here are some popular ones
        return [
            "openai/gpt-4-turbo-preview",
            "openai/gpt-4",
            "openai/gpt-3.5-turbo",
            "anthropic/claude-3-opus",
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3-haiku",
            "anthropic/claude-2.1",
            "google/gemini-pro",
            "google/palm-2-chat-bison",
            "meta-llama/llama-2-70b-chat",
            "mistralai/mistral-7b-instruct",
            "perplexity/pplx-70b-online",
            "cohere/command",
        ]
