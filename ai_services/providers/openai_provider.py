"""
OpenAI provider implementation.
"""
import requests
import logging
from typing import Dict, Any, List
from .base import BaseAIProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseAIProvider):
    """
    OpenAI API provider implementation.
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        super().__init__(model_config)
        self.endpoint_url = self.endpoint_url or "https://api.openai.com/v1/chat/completions"
        self.embedding_url = "https://api.openai.com/v1/embeddings"
        
        # Default model names if not specified
        if not self.model_name:
            self.model_name = "gpt-3.5-turbo"
        
        # Embedding model
        self.embedding_model = "text-embedding-ada-002"
    
    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        Send a chat completion request to OpenAI.
        """
        headers = self.prepare_headers()
        
        # Add organization ID if provided
        if self.model_config.get('organization_id'):
            headers['OpenAI-Organization'] = self.model_config['organization_id']
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": kwargs.get('max_tokens', self.max_tokens),
            "temperature": kwargs.get('temperature', self.temperature),
            "top_p": kwargs.get('top_p', self.top_p),
            "frequency_penalty": kwargs.get('frequency_penalty', self.frequency_penalty),
            "presence_penalty": kwargs.get('presence_penalty', self.presence_penalty),
        }
        
        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in payload and value is not None:
                payload[key] = value
        
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
            logger.error(f"OpenAI API request failed: {str(e)}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embeddings using OpenAI's API.
        """
        headers = self.prepare_headers()
        
        payload = {
            "model": self.embedding_model,
            "input": text
        }
        
        try:
            response = requests.post(
                self.embedding_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if 'data' in result and len(result['data']) > 0:
                return result['data'][0]['embedding']
            
            raise ValueError("No embedding data in response")
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenAI embedding request failed: {str(e)}")
            raise
    
    def is_available(self) -> bool:
        """
        Check if OpenAI API is available.
        """
        if not self.api_key:
            return False
        
        try:
            # Test with a simple models endpoint
            headers = self.prepare_headers()
            response = requests.get(
                "https://api.openai.com/v1/models",
                headers=headers,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def get_supported_models(self) -> List[str]:
        """
        Get list of supported OpenAI models.
        """
        return [
            "gpt-4-turbo-preview",
            "gpt-4-0125-preview",
            "gpt-4-1106-preview",
            "gpt-4",
            "gpt-3.5-turbo-0125",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
        ]
