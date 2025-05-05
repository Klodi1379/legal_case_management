"""
Groq provider implementation.
"""
import requests
import logging
from typing import Dict, Any, List
from .base import BaseAIProvider

logger = logging.getLogger(__name__)


class GroqProvider(BaseAIProvider):
    """
    Groq API provider implementation.
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        super().__init__(model_config)
        self.endpoint_url = self.endpoint_url or "https://api.groq.com/openai/v1/chat/completions"
        
        # Default model name if not specified
        if not self.model_name:
            self.model_name = "mixtral-8x7b-32768"
    
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Send a chat completion request to Groq.
        """
        headers = self.prepare_headers()
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": kwargs.get('max_tokens', self.max_tokens),
            "temperature": kwargs.get('temperature', self.temperature),
            "top_p": kwargs.get('top_p', self.top_p),
        }
        
        try:
            response = requests.post(
                self.endpoint_url,
                headers=headers,
                json=payload,
                timeout=30  # Groq is very fast
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Groq API request failed: {str(e)}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Groq doesn't provide embeddings API, so we'll return a placeholder.
        """
        logger.warning("Groq doesn't provide embeddings API")
        # Return a dummy embedding vector
        return [0.0] * 768
    
    def is_available(self) -> bool:
        """
        Check if Groq API is available.
        """
        if not self.api_key:
            return False
        
        try:
            headers = self.prepare_headers()
            response = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers=headers,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def get_supported_models(self) -> List[str]:
        """
        Get list of supported Groq models.
        """
        return [
            "mixtral-8x7b-32768",
            "llama2-70b-4096",
            "gemma-7b-it",
        ]
